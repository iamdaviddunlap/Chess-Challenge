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

            var challengersForHosts = parasitePopulation.SelectChallengers(hallOfFame);
            var challengersForParasites = hostPopulation.SelectChallengers(hallOfFame);
            
            // Evaluate raw fitness for hosts. Also save any results for organisms that are challengers for the parasites
            foreach (Organism host in hostPopulation.Organisms) {
                // var curHostGameWinners = Fitness.EvaluateFitnessAsync(host, challengersForHosts, random).GetAwaiter().GetResult();
                var curHostGameWinners = Fitness.EvaluateFitnessSync(host, challengersForHosts, random);

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
                // var curParasiteGameWinners = Fitness.EvaluateFitnessAsync(parasite, challengersForParasites, random, parasitePrecalcResults).GetAwaiter().GetResult();
                var curParasiteGameWinners = Fitness.EvaluateFitnessSync(parasite, challengersForParasites, random, parasitePrecalcResults);
                foreach(var entry in curParasiteGameWinners) {
                    allParasiteResults[entry.Key] = entry.Value;
                }
            }
            
            // Calculate fitnesses for the organisms in each population
            // var penalizeSize = generation % 10 == 0;
            // var penalizeSize = generation > 25;
            var penalizeSize = true;
            Fitness.AssignFitnesses(hostPopulation, allHostResults, penalizeSize);
            Fitness.AssignFitnesses(parasitePopulation, allParasiteResults, penalizeSize);
            
            // Get some metrics about how things are going
            Organism hostChamp = hostPopulation.GetSuperchamp();
            Organism parasiteChamp = parasitePopulation.GetSuperchamp();
            var dataset = DatasetHolder.CirclesClassificationDataset();
            var hostLoss = GameController.PlayLabeledDatasetSinglePlayer(hostChamp, random, dataset);
            var parasiteLoss = GameController.PlayLabeledDatasetSinglePlayer(parasiteChamp, random, dataset);
            
            var overallChamp = hostLoss < parasiteLoss ? hostChamp : parasiteChamp;
            var overallChampGuessBasedOnFitness = hostChamp.Fitness > parasiteChamp.Fitness ? hostChamp : parasiteChamp;
            var fitterChampStr = overallChampGuessBasedOnFitness == hostChamp ? "host" : "parasite";
            hallOfFame.Add(overallChamp);
            
            Console.WriteLine($"Generation {generation}: host champion loss: {hostLoss}");
            Console.WriteLine($"Generation {generation}: parasite champion loss: {parasiteLoss}");
            Console.WriteLine($"The {fitterChampStr} is fitter");
            Console.WriteLine("----------------------------");

            if (generation == 999) {
                var x = 1;
            }

            // Selection and breeding
            
            foreach (Population population in new List<Population>{hostPopulation, parasitePopulation}) {
                var otherPopulation = hostPopulation == population ? parasitePopulation : hostPopulation;
                var populationSeeds = otherPopulation.GetNSpeciesChamps(3);
                population.SelectAndReproduce(populationSeeds);
            }
            
            // Form species in both populations
            hostPopulation.Speciate();
            parasitePopulation.Speciate();
        }
    }
}