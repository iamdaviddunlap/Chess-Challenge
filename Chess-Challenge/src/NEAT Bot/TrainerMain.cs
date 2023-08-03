using System.Collections.Generic;

namespace Chess_Challenge.NEAT_Bot; 

public abstract class Trainer {
    
    // Setup hyperparameters
    private const int PopulationSize = 10;
    private const int InputsCount = 3;
    private const int OutputsCount = 1;

    public static void RunTraining(int maxGenerations) {
        // Initialization
        Population hostPopulation = new Population(PopulationSize, InputsCount, OutputsCount);
        Population parasitePopulation = new Population(PopulationSize, InputsCount, OutputsCount);

        List<Organism> hallOfFame = new List<Organism>();

        // Main evolutionary loop
        for (var generation = 0; generation < maxGenerations; generation++) {

            // Evaluate fitness of host
            foreach (Organism host in hostPopulation.Organisms) {
                Dictionary<Organism, Organism> hostGameWinners = hostPopulation.EvaluateFitnesses(host, parasitePopulation, hallOfFame);
            }
        
            // Evaluate fitness of parasite
            foreach (Organism parasite in hostPopulation.Organisms) {
                Dictionary<Organism, Organism> parasiteGameWinners = parasitePopulation.EvaluateFitnesses(parasite, hostPopulation, hallOfFame);
            }
            
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