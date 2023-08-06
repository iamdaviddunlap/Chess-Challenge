using System;
using System.Collections.Generic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public static class GameController {

    ///  Play game between two players. The return value is the fitness reward for the host
    public static int PlayGame(Organism host, Organism parasite, bool hostIsWhite, Random random) {
        int result;
        
        // result = hostIsWhite ? PlayChess(host, parasite) : PlayChess(parasite, host);
        //
        // // Reverse the score if the host is playing as the black player
        // if (!hostIsWhite) {
        //     result = -result;
        // }
        // result = PlayRandom(host, parasite, random);  // TODO don't use PlayRandom!
        result = PlayXOR(host, parasite, random);  // TODO don't use PlayXOR!
        
        return result;
    }

    /// Simulate a game of chess. Returns 1 if white wins, 0 if draw, -1 if black wins
    private static int PlayChess(Organism whitePlayer, Organism blackPlayer) {
        return -1;  // TODO implement PlayChess
    }

    public static double XORSinglePlayer(Organism player, Random random) {
        // Define XOR dataset.
        List<Tuple<double[], double>> dataset = new List<Tuple<double[], double>> {
            new Tuple<double[], double>(new double[] {0, 0, 1}, 0),
            new Tuple<double[], double>(new double[] {0, 1, 1}, 1),
            new Tuple<double[], double>(new double[] {1, 0, 1}, 1),
            new Tuple<double[], double>(new double[] {1, 1, 1}, 0)
        };

        // Randomize the dataset order.
        dataset = dataset.OrderBy(x => random.Next()).ToList();
        
        // Track score of the player.
        double playerLoss = 0.0;

        // Iterate over dataset.
        foreach (var item in dataset) {
            var inputs = item.Item1;
            var correctOutput = item.Item2;

            // Activate genomes with inputs and calculate the absolute difference from correct XOR output.
            var playerOutput = player.Genome.Activate(inputs)[0];

            playerLoss += Math.Abs(correctOutput - playerOutput);
        }

        return playerLoss;
    }

    private static int PlayXOR(Organism hostPlayer, Organism parasitePlayer, Random random) {

        double hostLoss = XORSinglePlayer(hostPlayer, random);
        double parasiteLoss = XORSinglePlayer(parasitePlayer, random);

        // Return 1 if host player is closer to correct XOR output, -1 otherwise.
        if (Math.Abs(hostLoss - parasiteLoss) < 0.0001) {
            return 0;
        }
        if (hostLoss < parasiteLoss) {
            return 1;
        }
        return -1;
    }
    
    private static int PlayRandom(Organism hostPlayer, Organism parasitePlayer, Random random) {
        return random.Next(-1, 2);  // Generates random numbers -1, 0, or 1
    }
}