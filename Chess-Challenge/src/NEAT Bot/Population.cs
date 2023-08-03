using System;
using System.Collections.Generic;

namespace Chess_Challenge.NEAT_Bot; 

public class Population {

    private Random Random;
    public List<Organism> Organisms { get; } = new();

    public Population(int numOrganisms, int organismInputs, int organismOutputs, Random? random = null) {
        Random = random ?? new Random();  // Create new Random object if none is provided
        for (var i = 0; i < numOrganisms; i++) {
            var genome = new Genome(inputs: organismInputs, outputs: organismOutputs, randomSeed: 1);
            var organism = new Organism(genome);
            Organisms.Add(organism);
        }
        // TODO should I start a population by mutating all species?
    }

    public Dictionary<Organism, Organism> EvaluateFitnesses(Organism host, Population parasitePopulation, List<Organism> hallOfFame) {
        var results = new Dictionary<Organism, Organism>();
        
        // TODO implement EvaluateFitnesses in Population
        
        return results;
    } 
    
    public void Reproduce() {
        // TODO implement Reproduce in Population
    } 
}