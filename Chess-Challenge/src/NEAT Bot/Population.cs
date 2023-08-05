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
    public List<Organism> selectChallengers(List<Organism> hallOfFame) {
        List<Organism> challengers = new List<Organism>();
        List<int> challengerIds = new List<int>();
        List<Organism> speciesChampions = new List<Organism>();

        // Gather all species champions
        foreach (var speciesId in SpeciesIds) {
            speciesChampions.Add(GetSpeciesChampion(speciesId));
        }

        // Sort the speciesChampions list by AdjustedFitness in descending order and take the top few
        speciesChampions = speciesChampions.OrderByDescending(o => o.AdjustedFitness).ToList();
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

    /// This function will run games to determine the host's RawFitness. It will select a set of challengers using the
    /// parasite population and the Hall of Fame. 2 games will be played against each challenger, one as white and one
    /// as black. The RawFitness is the total of rewards won from all games.
    public Dictionary<Tuple<Organism, Organism, bool>, int> EvaluateFitness(Organism host, List<Organism> challengers,
        Dictionary<Tuple<Organism, Organism, bool>, int>? precalcResults = null) {
        var results = new Dictionary<Tuple<Organism, Organism, bool>, int>();

        // Main loop over games for each challenger. The host plays each challenger twice - once as white and once as black
        // TODO parallelize this loop! It will likely take a very long time as-is
        var totalFitness = 0.0;
        foreach (var challenger in challengers) 
        {
            for (int i = 0; i < 2; i++) 
            {
                bool hostIsWhite = i == 0;
                var key = new Tuple<Organism, Organism, bool>(host, challenger, hostIsWhite);

                int result;
                if (precalcResults != null && precalcResults.TryGetValue(key, out var precalcResult))
                {
                    // Use the precalculated result if it exists in the precalcResults dictionary
                    result = precalcResult;
                }
                else
                {
                    // Run the PlayGame method if no precalculated result is found
                    result = GameController.PlayGame(host, challenger, hostIsWhite, Random);
                }

                results[key] = result;
                totalFitness += GameController.ConvertResultToFitness(result);
            }
        }

        host.RawFitness = totalFitness;

        return results;
    }


    public void Reproduce() {
        // TODO implement Reproduce in Population
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
        // Use LINQ to filter Organisms by SpeciesId and then sort by AdjustedFitness in descending order
        var species = Organisms.Where(o => o.SpeciesId == speciesId).OrderByDescending(o => o.AdjustedFitness).ToList();
    
        // If there are no organisms of the specified species, throw a new exception
        if (species.Count == 0) {
            throw new KeyNotFoundException($"No organisms found for species id: {speciesId}");
        }
    
        // Otherwise, return the first organism in the list (the one with the highest fitness)
        return species[0];
    }

}