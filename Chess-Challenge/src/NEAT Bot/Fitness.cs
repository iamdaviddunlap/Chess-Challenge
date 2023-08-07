using System;
using System.Linq;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Chess_Challenge.NEAT_Bot; 

public static class Fitness {
    private static double ConvertGameResultToFitness(int result) {
        return result switch {
            // return the corresponding fitness reward based on the result of the game
            1 => Constants.FitnessRewardWin,
            0 => Constants.FitnessRewardDraw,
            -1 => Constants.FitnessRewardLoss,
            _ => throw new ArgumentOutOfRangeException()
        };
    }
    
    /// This function will run games to determine the host's RawFitness. It will select a set of challengers using the
    /// parasite population and the Hall of Fame. 2 games will be played against each challenger, one as white and one
    /// as black. The fitness of the host will NOT be affected by this function. It will simply find the result of its
    /// games against the challengers.
    public static async Task<Dictionary<Tuple<Organism, Organism, bool>, int>> EvaluateFitnessAsync(Organism host, List<Organism> challengers,
        Random random, Dictionary<Tuple<Organism, Organism, bool>, int>? precalcResults = null) {
        var results = new Dictionary<Tuple<Organism, Organism, bool>, int>();
        var tasks = new List<Task>();
        var threadLocalRandom = new ThreadLocal<Random>(() => new Random(random.Next()));

        // Main loop over games for each challenger. The host plays each challenger twice - once as white and once as black
        foreach (var challenger in challengers) {
            for (int i = 0; i < 2; i++) {
                bool hostIsWhite = i == 0;
                var key = new Tuple<Organism, Organism, bool>(host, challenger, hostIsWhite);
                tasks.Add(Task.Run(() =>
                {
                    int result;
                    if (precalcResults != null && precalcResults.TryGetValue(key, out var precalcResult)) {
                        // Use the precalculated result if it exists in the precalcResults dictionary
                        result = precalcResult;
                    }
                    else {
                        // Run the PlayGame method if no precalculated result is found
                        result = GameController.PlayGame(host, challenger, hostIsWhite, threadLocalRandom.Value);
                    }

                    lock (results) {
                        results[key] = result;
                    }
                }));
            }
        }

        await Task.WhenAll(tasks);

        return results;
    }
    
    public static Dictionary<Tuple<Organism, Organism, bool>, int> EvaluateFitnessSync(Organism host, List<Organism> challengers,
        Random random, Dictionary<Tuple<Organism, Organism, bool>, int>? precalcResults = null) {
        var results = new Dictionary<Tuple<Organism, Organism, bool>, int>();

        // Main loop over games for each challenger. The host plays each challenger twice - once as white and once as black
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
                    result = GameController.PlayGame(host, challenger, hostIsWhite, random);
                }

                results[key] = result;
            }
        }

        return results;
    }


    public static void AssignFitnesses(Population hostPopulation, Dictionary<Tuple<Organism, Organism, bool>, int> hostGameResults, bool penalizeSize = false) {
        
        // Find the number of unique hosts that defeat each parasite
        Dictionary<Organism, HashSet<Organism>> parasiteDefeatCount = new Dictionary<Organism, HashSet<Organism>>();
        foreach (var result in hostGameResults) {
            var host = result.Key.Item1;
            var parasite = result.Key.Item2;
            int gameResult = result.Value;
            if (gameResult > 0) { // Host defeated the parasite
                if (!parasiteDefeatCount.ContainsKey(parasite)) {
                    parasiteDefeatCount[parasite] = new HashSet<Organism>();
                }
                parasiteDefeatCount[parasite].Add(host);
            }
        }
        
        // Organism maxGenomeOrganism = hostPopulation.Organisms.Aggregate((o1, o2) => 
        //     (o1.Genome.Nodes.Count + o1.Genome.Connections.Count) > (o2.Genome.Nodes.Count + o2.Genome.Connections.Count) ? o1 : o2);
        double maxNodesCount = hostPopulation.Organisms.Max(o => o.Genome.Nodes.Count);
        // double maxConnCount = hostPopulation.Organisms.Max(o => o.Genome.Connections.Count);
        double worstRatio = hostPopulation.Organisms.Max(o => o.Genome.Connections.Count / Math.Pow(o.Genome.Nodes.Count, 2));
        

        // Calculate fitness for each organism
        foreach (var organism in hostPopulation.Organisms) {
            // Calculate penalty for genome size
            
            // Calculate penalties using a the singular biggest organism in the population instead of nodes and connections separately
            // double nodesCountPenalty = Constants.FitnessPenaltyFactorNodeCount * (organism.Genome.Nodes.Count / (double)maxGenomeOrganism.Genome.Nodes.Count);
            // double connCountPenalty = Constants.FitnessPenaltyFactorConnCount * (organism.Genome.Connections.Count / (double)maxGenomeOrganism.Genome.Connections.Count);

            double totalPenalty;
            if (penalizeSize) {
                var nodesRatio = organism.Genome.Nodes.Count / maxNodesCount;
                var connsRatio = (organism.Genome.Connections.Count / Math.Pow(organism.Genome.Nodes.Count, 2)) / worstRatio;
                totalPenalty = ((nodesRatio + connsRatio) / 2.0) * Constants.FitnessPenaltyFactor;
            }
            else {
                totalPenalty = 0;
            }
            
            var totalFitnessReward = 0.0;
            foreach (var result in hostGameResults.Where(r => r.Key.Item1 == organism)) {
                var parasite = result.Key.Item2;
                int gameResult = result.Value;
                
                // Competitive fitness sharing. The reward for defeating a parasite is 1/N * reward, where N is the
                // number of unique hosts that can defeat this parasite, and reward is the reward assigned for the game result
                int uniqueDefeats = parasiteDefeatCount.TryGetValue(parasite, out var value) ? value.Count: 0;
                double rewardModifier = uniqueDefeats > 0 ? 1.0 / uniqueDefeats: 2.0;
                totalFitnessReward += rewardModifier * ConvertGameResultToFitness(gameResult);
            }
            // Explicit fitness sharing. The total fitness is divided by the number of organisms in the same species
            int speciesCount = hostPopulation.Organisms.Count(o => o.SpeciesId == organism.SpeciesId);
            organism.Fitness = (totalFitnessReward / speciesCount) - totalPenalty;
        }
    }
}