using System;
using System.Collections.Generic;
using ChessChallenge.API;

public class MyBot : IChessBot
{
    public Move Think(Board board, Timer timer) {
        Move[] moves = board.GetLegalMoves();

        // Looks like longs are the most efficient way to store things, giving us 64 bits of data per bot-brain character
        long[] hexValue = { 0x10A5111110A51111, 0x10A5111110A51111, 0x10A5111110A51111, 0x10A5111110A51111, 0x10A5111110A51111, 0x10A5111110A51111, 0x10A5111110A51111, 0x10A5111110A51111};
        
        // Some code to treat hexValue as a bitstream and process it in 51-bit chunks
        for (int i = 0, j = 0; i < hexValue.Length; j += 51) {
            if (j / 64 > i) {
                i++;
                j -= 64;
            }
            long fiftyOneBits = ((hexValue[i] >> j) | (i + 1 < hexValue.Length ? hexValue[i + 1] << (64 - j) : 0)) & ((1L << 51) - 1);
            Console.WriteLine(Convert.ToString(fiftyOneBits, 2).PadLeft(51, '0'));
            Console.WriteLine("---");
        }
        
        if ((hexValue[0] & 1) == 0) {
            return moves[0];
        }
        else {
            return moves[1];
        }
    }
}