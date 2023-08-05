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
        // TODO clear innovation maps before making new organisms
        
        double totalAvgFitness = 0;

        // Dictionary to hold average fitness per species
        Dictionary<int, double> speciesAverageFitness = new Dictionary<int, double>();

        // Loop through species once, performing elimination and calculating total average fitness
        foreach (var speciesId in SpeciesIds) {
            EliminateSpeciesWeakest(speciesId);

            double averageFitness = Organisms.Where(o => o.SpeciesId == speciesId).Average(o => o.Fitness);
            totalAvgFitness += averageFitness;

            speciesAverageFitness[speciesId] = averageFitness; // Store average fitness for later use
        }

        // At least MinAsexualOffspring offspring will be produced with asexual reproduction
        // Probably a bit more will be made due to rounding in the calculation of numSpeciesOffspring
        int numSexualOffspring = Constants.PopulationSize - Constants.MinAsexualOffspring;
        
        // Loop through species again, calculating the number of offspring for each species by sexual reproduction
        var totalOffspring = 0;
        var newOrganisms = new List<Organism>();
        foreach (var speciesId in SpeciesIds) {
            var speciesNewOrganisms = new List<Organism>();
            var speciesOrganisms = Organisms.Where(o => o.SpeciesId == speciesId).ToList();
            double averageFitness = speciesAverageFitness[speciesId]; // Retrieve stored average fitness
            int numSpeciesOffspring = (int)((averageFitness / totalAvgFitness) * numSexualOffspring);
            totalOffspring += numSpeciesOffspring;
            if (speciesOrganisms.Count > 1) {
                // Sexually reproduce species
                for (int i = 0; i < numSpeciesOffspring; i++) {
                    // Create pairs by selecting two random objects each time
                    // Select two distinct organisms
                    int index1 = -1, index2 = -1;
                    while (index1 == index2) {
                        index1 = Random.Next(speciesOrganisms.Count);
                        index2 = Random.Next(speciesOrganisms.Count);
                    }

                    var offspring = speciesOrganisms[index1].Reproduce(Random, speciesOrganisms[index2]);
                    speciesNewOrganisms.Add(offspring);
                }
            }
            else {
                // If there is only 1 organism in the species, we must produce more with asexual reproduction
                for (int i = 0; i < numSpeciesOffspring; i++) {
                    var offspring = speciesOrganisms[0].Reproduce(Random);
                    speciesNewOrganisms.Add(offspring);
                }
            }
            newOrganisms.AddRange(speciesNewOrganisms);
        }
        
        // Fill in the rest of the population by having the top organisms asexually reproduce
        int remainder = Constants.PopulationSize - totalOffspring;
        var asexualParents = Organisms.OrderByDescending(o => o.Fitness).Take(remainder).ToList();
        foreach (var parent in asexualParents) {
            var offspring = parent.Reproduce(Random);
            newOrganisms.Add(offspring);
        }

        var x = 1;
        // TODO do something with newOrganisms
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
            SpeciesIds.Add(newId);
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