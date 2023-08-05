using System;
using System.Collections.Generic;

namespace Chess_Challenge.NEAT_Bot; 

public abstract class Trainer {
    public static void RunTraining(int maxGenerations) {

        int randomSeed = 1;
        Random random = new Random(randomSeed);
        
        // Initialization
        InnovationHandler innovationHandler = new InnovationHandler();
        Population hostPopulation = new Population(innovationHandler, random);
        Population parasitePopulation = new Population(innovationHandler, random);

        List<Organism> hallOfFame = new List<Organism>();

        // Main evolutionary loop
        for (var generation = 0; generation < maxGenerations; generation++) {
            
            
            var parasitePrecalcResults = new Dictionary<Tuple<Organism, Organism, bool>, int>();
            var allHostResults = new Dictionary<Tuple<Organism, Organism, bool>, int>();
            var allParasiteResults = new Dictionary<Tuple<Organism, Organism, bool>, int>();

            var challengersForHosts = parasitePopulation.selectChallengers(hallOfFame);
            var challengersForParasites = hostPopulation.selectChallengers(hallOfFame);
            
            // Evaluate raw fitness for hosts. Also save any results for organisms that are challengers for the parasites
            foreach (Organism host in hostPopulation.Organisms) {
                var curHostGameWinners = hostPopulation.EvaluateFitness(host, challengersForHosts);

                if(challengersForParasites.Contains(host)) {
                    foreach(var (originalKey, value) in curHostGameWinners) {
                        allHostResults[originalKey] = value;
                        var newValue = -value;

                        // Create a new key with swapped Organisms and inverted bool
                        var newKey = new Tuple<Organism, Organism, bool>(originalKey.Item2, originalKey.Item1, !originalKey.Item3);

                        parasitePrecalcResults[newKey] = newValue;
                    }
                }
                else {
                    foreach(var entry in curHostGameWinners) {
                        allHostResults[entry.Key] = entry.Value;
                    }
                }
            }
            
            // Evaluate raw fitness of parasites
            foreach (Organism parasite in parasitePopulation.Organisms) {
                var curParasiteGameWinners = parasitePopulation.EvaluateFitness(parasite, challengersForParasites, parasitePrecalcResults);
                foreach(var entry in curParasiteGameWinners) {
                    allParasiteResults[entry.Key] = entry.Value;
                }
            }

            var x = 1;

            // TODO everything below here is basically pseudocode, but roughly what I want
            // // Form species in both populations
            // hostPopulation.Speciate();
            // parasitePopulation.Speciate();
            //
            // // Selection and breeding
            // foreach (Population population in new List<Population>{hostPopulation, parasitePopulation}) {
            //     foreach (Species species in population.Species) {
            //         species.EliminateWeakest();
            //         List<NeuralNetworkBot> offspring = species.Breed();
            //         population.ReplacePopulation(offspring);
            //     }
            // }
        }
    }
}