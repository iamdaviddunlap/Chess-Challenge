using System;
using System.Collections.Generic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public class Population {

    private Random Random;
    public List<Organism> Organisms { get; } = new();  // List of all organisms in this population
    public List<int> SpeciesIds = new();  // List of all speciesIds that have been assigned to organisms in this population

    public Population(InnovationHandler innovationHandler, Random? random = null) {
        Random = random ?? new Random();  // Create new Random object if none is provided
        for (var i = 0; i < Constants.PopulationSize; i++) {
            var genome = new Genome(innovationHandler, Random);
            var organism = new Organism(genome, innovationHandler);
            Mutation.MutateGenome(organism.Genome, Random);
            Mutation.MutateGenome(organism.Genome, Random);  // TODO mutating more than needed for testing
            Mutation.MutateGenome(organism.Genome, Random);  // TODO mutating more than needed for testing
            Mutation.MutateGenome(organism.Genome, Random);  // TODO mutating more than needed for testing
            Mutation.MutateGenome(organism.Genome, Random);  // TODO mutating more than needed for testing
            Organisms.Add(organism);
        }
        SpeciesIds.Add(-1);  // All organisms are created with species -1, so add this to the speciesId list
    }

    public Dictionary<Organism, Organism> EvaluateFitnesses(Organism host, Population parasitePopulation, List<Organism> hallOfFame) {
        var results = new Dictionary<Organism, Organism>();

        List<Organism> challengers = new List<Organism>();
        List<int> challengerIds = new List<int>();
        List<Organism> speciesChampions = new List<Organism>();

        // Gather all species champions
        foreach (var speciesId in parasitePopulation.SpeciesIds) {
            speciesChampions.Add(parasitePopulation.GetSpeciesChampion(speciesId));
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

        // If we don't have enough challengers (because we're in an early generation), pick random parasites as
        // challengers until we have enough
        while (challengers.Count < Constants.NumHallOfFameParasites + Constants.NumChampionParasites) {
            var randomOrganism = parasitePopulation.Organisms[Random.Next(parasitePopulation.Organisms.Count)];
            if (challengerIds.Contains(randomOrganism.OrganismId)) continue;
            challengers.Add(randomOrganism);
            challengerIds.Add(randomOrganism.OrganismId);
        }

        // TODO finish implementing. The host should play games against each of the challengers
        var diff = host.Genome.GeneticDifference(challengers[0].Genome);
        return results;
    }

    public void Reproduce() {
        // TODO implement Reproduce in Population
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