using System;
using System.Collections.Generic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public class Population {

    private Random Random;
    private double minVal;  // The smallest a weight or bias can get
    private double maxVal;  // The biggest a weight or bias can get
    public List<Organism> Organisms { get; } = new();  // List of all organisms in this population
    public List<int> SpeciesIds = new();  // List of all speciesIds that have been assigned to organisms in this population

    public Population(int numOrganisms, int organismInputs, int organismOutputs, double minVal, double maxVal, InnovationHandler innovationHandler, Random? random = null) {
        Random = random ?? new Random();  // Create new Random object if none is provided
        this.minVal = minVal;
        this.maxVal = maxVal;
        for (var i = 0; i < numOrganisms; i++) {
            var genome = new Genome(inputs: organismInputs, outputs: organismOutputs, innovationHandler, Random, minWeight: minVal, maxWeight: maxVal);
            var organism = new Organism(genome, innovationHandler);
            Mutation.MutateGenome(organism.Genome, minVal, maxVal, Random);
            Organisms.Add(organism);
        }
        SpeciesIds.Add(-1);  // All organisms are created with species -1, so add this to the speciesId list
    }

    public Dictionary<Organism, Organism> EvaluateFitnesses(Organism host, Population parasitePopulation, List<Organism> hallOfFame) {
        var results = new Dictionary<Organism, Organism>();

        var numHoFParasites = 8;
        var numChampionParasites = 4;

        List<Organism> challengers = new List<Organism>();
        List<int> challengerIds = new List<int>();
        List<Organism> speciesChampions = new List<Organism>();

        // Gather all species champions
        foreach (var speciesId in parasitePopulation.SpeciesIds) {
            speciesChampions.Add(parasitePopulation.GetSpeciesChampion(speciesId));
        }

        // Sort the speciesChampions list by Fitness in descending order and take the top few
        speciesChampions = speciesChampions.OrderByDescending(o => o.Fitness).ToList();
        challengers.AddRange(speciesChampions.Take(numChampionParasites));
        challengerIds.AddRange(speciesChampions.Take(numChampionParasites).Select(o => o.OrganismId));

        // Add challengers from the Hall of Fame
        if (hallOfFame.Count > 0) {
            for (var i = 0; i < Math.Min(numHoFParasites, hallOfFame.Count); i++) {
                Organism hofChallenger = hallOfFame[Random.Next(hallOfFame.Count)];
                challengers.Add(hofChallenger);
                challengerIds.Add(hofChallenger.OrganismId);
            }
        }

        // If we don't have enough challengers (because we're in an early generation), pick random parasites as
        // challengers until we have enough
        while (challengers.Count < numHoFParasites + numChampionParasites) {
            var randomOrganism = parasitePopulation.Organisms[Random.Next(parasitePopulation.Organisms.Count)];
            if (challengerIds.Contains(randomOrganism.OrganismId)) continue;
            challengers.Add(randomOrganism);
            challengerIds.Add(randomOrganism.OrganismId);
        }

        // TODO finish implementing. The host should play games against each of the challengers

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