using System;
using System.Collections.Generic;
using ChessChallenge.API;

public class MyBot : IChessBot
{
    public Move Think(Board board, Timer timer) {
        Move[] moves = board.GetLegalMoves();
        // string boardEncoding = "ab";
        int hexValue = 0x10A51111;  // Seems like strings DO increase "bot brain size" but hex values DO NOT. However, we can only store 32 binary digits in a hex value
        if ((hexValue & 1) == 0) {
            return moves[0];
        }
        else {
            return moves[1];
        }
    }
}