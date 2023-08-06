using System;
using System.Collections.Generic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public class Population {

    private Random Random;
    private InnovationHandler _innovationHandler;
    private int _curSpeciesId;
    public List<Organism> Organisms { get; } = new();  // List of all organisms in this population
    public List<Organism> SpeciesReps { get; } = new();  // List containing 1 representative of each species
    public List<int> SpeciesIds = new();  // List of all speciesIds that have been assigned to organisms in this population

    public Population(InnovationHandler innovationHandler, Random? random = null) {
        Random = random ?? new Random();  // Create new Random object if none is provided
        _innovationHandler = innovationHandler;
        for (var i = 0; i < Constants.PopulationSize; i++) {
            var genome = new Genome(innovationHandler, Random);
            var organism = new Organism(genome, innovationHandler);
            Mutation.MutateGenome(organism.Genome, Random);
            Organisms.Add(organism);
        }
        Speciate();
    }

    /// Returns a list of challenger Organisms taken as a combination of this population's champions and the Hall of Fame
    public List<Organism> SelectChallengers(List<Organism> hallOfFame) {
        List<Organism> challengers = new List<Organism>();
        List<int> challengerIds = new List<int>();
        List<Organism> speciesChampions = new List<Organism>();

        // Gather all species champions
        foreach (var speciesId in SpeciesIds) {
            speciesChampions.Add(GetSpeciesChampion(speciesId));
        }

        // Sort the speciesChampions list by Fitness in descending order and take the top few
        speciesChampions = speciesChampions.OrderByDescending(o => o.Fitness).ToList();
        challengers.AddRange(speciesChampions.Take(Constants.NumChampionParasites));
        challengerIds.AddRange(speciesChampions.Take(Constants.NumChampionParasites).Select(o => o.OrganismId));

        // Add challengers from the Hall of Fame
        if (hallOfFame.Count > 0) {
            for (var i = 0; i < Math.Min(Constants.NumHallOfFameParasites, hallOfFame.Count); i++) {
                Organism hofChallenger = hallOfFame[Random.Next(hallOfFame.Count)];
                challengers.Add(hofChallenger);
                challengerIds.Add(hofChallenger.OrganismId);
            }
        }

        // If we don't have enough challengers (because we're in an early generation), pick random organisms as
        // challengers until we have enough
        while (challengers.Count < Constants.NumHallOfFameParasites + Constants.NumChampionParasites) {
            var randomOrganism = Organisms[Random.Next(Organisms.Count)];
            if (challengerIds.Contains(randomOrganism.OrganismId)) continue;
            challengers.Add(randomOrganism);
            challengerIds.Add(randomOrganism.OrganismId);
        }

        return challengers;
    }


    public void SelectAndReproduce() {
        var newOrganisms = new List<Organism>();
        
        // Dictionary to hold average fitness per species
        Dictionary<int, double> speciesAverageFitness = new Dictionary<int, double>();
        double totalAvgFitness = 0;
        
        // Clear species reps and unique innovation maps
        SpeciesReps.Clear();
        _innovationHandler.ConnectionIdMapping.Clear();
        _innovationHandler.NodeIdMapping.Clear();
        
        // First pass over species list. Eliminate the weakest, find the average fitness, save the species champ, and
        // reassign the species rep as a random member of the species
        var speciesChamps = new List<Organism>();
        foreach (var speciesId in SpeciesIds) {
            EliminateSpeciesWeakest(speciesId);
            var speciesOrganisms = Organisms.Where(o => o.SpeciesId == speciesId).ToList();
            var avgFitness = speciesOrganisms.Average(o => o.Fitness);
            var speciesChamp = speciesOrganisms.OrderByDescending(o => o.Fitness).First();
            var speciesRep = speciesOrganisms[Random.Next(speciesOrganisms.Count)];
            SpeciesReps.Add(speciesRep);
            speciesChamps.Add(speciesChamp);
            speciesAverageFitness[speciesId] = avgFitness;
            totalAvgFitness += avgFitness;
        }

        // Find the "superchamp" ie the organism with the greatest fitness in the entire population
        var superChamp = Organisms.OrderByDescending(o => o.Fitness).First();

        // create special clones from super champ with no structural changes, only weight changes
        for (int i = 0; i < Constants.MinSuperchampOffspring; i++) {
            var newSuperchampGenome = superChamp.Genome.Clone();
            Mutation.MutateWeights(newSuperchampGenome, Random);
            var newSuperchampChild = new Organism(newSuperchampGenome, _innovationHandler);
            newOrganisms.Add(newSuperchampChild);
        }

        // directly clone the species champions
        foreach (var champ in speciesChamps) {
            var clonedGenome = champ.Genome.Clone();
            var newOrganism = new Organism(clonedGenome, _innovationHandler);
            newOrganisms.Add(newOrganism);
        }

        int remaining = Constants.PopulationSize - newOrganisms.Count;
        
        foreach (var speciesId in SpeciesIds) {
            var speciesNewOrganisms = new List<Organism>();
            var speciesOrganisms = Organisms.Where(o => o.SpeciesId == speciesId).ToList();
            double averageFitness = speciesAverageFitness[speciesId]; // Retrieve stored average fitness
            int numSpeciesOffspring = Math.Max((int)((averageFitness / totalAvgFitness) * remaining), 1);
            for (int i = 0; i < numSpeciesOffspring; i++) {
                if (speciesOrganisms.Count > 1 && Random.NextDouble() > Constants.MutateOnlyProb) {
                    // Sexually reproduce
                    Organism offspring;
                    if (Random.NextDouble() < Constants.CrossSpeciesMatingProb) {
                        // Do cross-species mating. Pick a random parent from this species and the champ from a different one
                        int otherSpeciesId;
                        do {  // Select a random species that is not the current one
                            otherSpeciesId = SpeciesIds[Random.Next(SpeciesIds.Count)];
                        } while (otherSpeciesId == speciesId);
                        // Select the champion from the other species
                        var champOrganism = speciesChamps.First(o => o.SpeciesId == otherSpeciesId);
                        
                        var index = Random.Next(speciesOrganisms.Count);
                        offspring = speciesOrganisms[index].Reproduce(Random, champOrganism);
                    } else {
                        var index1 = -1;
                        var index2 = -1;
                        while (index1 == index2) {
                            index1 = Random.Next(speciesOrganisms.Count);
                            index2 = Random.Next(speciesOrganisms.Count);
                        }

                        offspring = speciesOrganisms[index1].Reproduce(Random, speciesOrganisms[index2]);
                    }
                    // Decide whether or not to mutate baby
                    if (Random.NextDouble() > Constants.MateOnlyProb) {
                        Mutation.MutateGenome(offspring.Genome, Random);
                    }
                    speciesNewOrganisms.Add(offspring);
                }
                else {
                    // Asexually reproduce
                    // This happens if there is only 1 organism in the species or based on MutateOnlyProb
                    var index = Random.Next(speciesOrganisms.Count);
                    var offspring = speciesOrganisms[index].Reproduce(Random);
                    speciesNewOrganisms.Add(offspring);
                }
            }
            newOrganisms.AddRange(speciesNewOrganisms);
        }
        
        // Fill in the rest of the population by having the top organisms asexually reproduce
        remaining = Constants.PopulationSize - newOrganisms.Count;
        var asexualParents = Organisms.OrderByDescending(o => o.Fitness).Take(remaining).ToList();
        foreach (var parent in asexualParents) {
            var offspring = parent.Reproduce(Random);
            newOrganisms.Add(offspring);
        }
        
        // Cut off organisms if we created too many
        newOrganisms = newOrganisms.Take(Constants.PopulationSize).ToList();

        // Replace the old population with the new one
        Organisms.Clear();
        Organisms.AddRange(newOrganisms);
    
        // Perform speciation on new organisms
        Speciate();
    }

    public void EliminateSpeciesWeakest(int speciesId) {
        // Use LINQ to filter Organisms by SpeciesId and then sort by Fitness in descending order
        var speciesOrganisms = Organisms.Where(o => o.SpeciesId == speciesId).OrderByDescending(o => o.Fitness).ToList();

        // Determine the cut-off index
        int cutoffIndex = (int)(speciesOrganisms.Count * Constants.SpeciesElitePercentage);
    
        // If the species has two or more organisms, keep at least 2, otherwise keep the top %
        if (speciesOrganisms.Count >= 2) {
            cutoffIndex = Math.Max(cutoffIndex, 2);
        } else if (speciesOrganisms.Count == 1) {
            cutoffIndex = 1;
        }

        // Iterate from the cutoff index to the end, removing each organism from the Organisms list
        for (int i = speciesOrganisms.Count - 1; i >= cutoffIndex; i--) {
            Organisms.Remove(speciesOrganisms[i]);
        }
    }

    public void Speciate() {
        foreach (var organism in Organisms) {
            var foundSpecies = false;
            foreach (var speciesRep in SpeciesReps) {
                var geneDifference = organism.Genome.GeneticDifference(speciesRep.Genome);
                if (geneDifference <= Constants.SpeciesCompatThresh) {
                    organism.SpeciesId = speciesRep.SpeciesId;
                    foundSpecies = true;
                    break;
                }
            }

            if (foundSpecies) continue;
            var newId = GetNextSpeciesId();
            organism.SpeciesId = newId;
            SpeciesReps.Add(organism);
        }

        // Clear the SpeciesIds list
        SpeciesIds.Clear();

        // Assign new unique species IDs by going through the Organisms list
        var uniqueSpeciesIds = Organisms.Select(o => o.SpeciesId).Distinct();

        // Replace the SpeciesIds list with the new unique species IDs
        SpeciesIds.AddRange(uniqueSpeciesIds);

        // Remove organisms from SpeciesReps that are no longer representatives of any species
        SpeciesReps.RemoveAll(rep => !SpeciesIds.Contains(rep.SpeciesId));
        
        // Adjust SpeciesCompatThresh to target SpeciesCountTarget number of species
        if (SpeciesIds.Count < Constants.SpeciesCountTarget) {
            Constants.SpeciesCompatThresh -= Constants.SpeciesCompatModifier;
        } else if (SpeciesIds.Count > Constants.SpeciesCountTarget) {
            Constants.SpeciesCompatThresh += Constants.SpeciesCompatModifier;
        }
        // Ensure the SpeciesCompatThresh can't get too low
        if (Constants.SpeciesCompatThresh < Constants.SpeciesCompatModifier) {
            Constants.SpeciesCompatThresh = Constants.SpeciesCompatModifier;
        }
    }

    private int GetNextSpeciesId() {
        var curId = _curSpeciesId;
        _curSpeciesId++;
        return curId;
    }

    private Organism GetSpeciesChampion(int speciesId) {
        // Use LINQ to filter Organisms by SpeciesId and then sort by Fitness in descending order
        var species = Organisms.Where(o => o.SpeciesId == speciesId).OrderByDescending(o => o.Fitness).ToList();
    
        // If there are no organisms of the specified species, throw a new exception
        if (species.Count == 0) {
            throw new KeyNotFoundException($"No organisms found for species id: {speciesId}");
        }
    
        // Otherwise, return the first organism in the list (the one with the highest fitness)
        return species[0];
    }

}