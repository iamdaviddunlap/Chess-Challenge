using System;

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
        result = PlayRandom(host, parasite, random);  // TODO don't use PlayRandom!
        
        return result;
    }

    /// Simulate a game of chess. Returns 1 if white wins, 0 if draw, -1 if black wins
    private static int PlayChess(Organism whitePlayer, Organism blackPlayer) {
        return -1;  // TODO implement PlayChess
    }

    private static int PlayXOR(Organism hostPlayer, Organism parasitePlayer) {
        return -1;  // TODO implement PlayXOR
    }
    
    private static int PlayRandom(Organism hostPlayer, Organism parasitePlayer, Random random) {
        return random.Next(-1, 2);  // Generates random numbers -1, 0, or 1
    }
}