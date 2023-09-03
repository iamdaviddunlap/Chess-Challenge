import chess
import numpy as np
import random

BOARD_ENCODING_LENGTH = 256
MOVE_ENCODING_LENGTH = 28
TOTAL_ENCODING_LENGTH = BOARD_ENCODING_LENGTH + MOVE_ENCODING_LENGTH
STARTING_POSITION_INPUT_TENSOR = np.array([[1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
                                          dtype=np.float)


def board_to_binary(board):
    binary_representation_str = ''

    for square in range(64):
        piece = board.piece_at(square)
        if piece is None:
            binary_representation_str += encode_piece(piece, None)
        else:
            binary_representation_str += encode_piece(piece.piece_type, piece.color)

    return binary_representation_str


def encode_piece(piece_type, color):
    color_bit = '1' if color else '0'
    piece_bits = {
        None: '000',
        chess.PAWN: '001',
        chess.ROOK: '010',
        chess.KNIGHT: '011',
        chess.BISHOP: '100',
        chess.QUEEN: '101',
        chess.KING: '110',
    }
    return color_bit + piece_bits[piece_type]


def move_to_binary(move, board):
    uci_move = board.uci(move)
    origin, destination = uci_move[:2], uci_move[2:]
    origin_file, origin_rank = ord(origin[0]) - 97, int(origin[1]) - 1
    dest_file, dest_rank = ord(destination[0]) - 97, int(destination[1]) - 1

    origin_file_bin = format(origin_file, '04b')
    origin_rank_bin = format(origin_rank, '04b')
    dest_file_bin = format(dest_file, '04b')
    dest_rank_bin = format(dest_rank, '04b')

    # Generate Extra Bits
    bit_func = lambda condition: '1' if condition else '0'
    is_capture = board.is_capture(move)
    is_en_passant = board.is_en_passant(move)
    is_promotion = bool(move.promotion)
    is_castles = board.is_castling(move)
    is_capture_bin = bit_func(is_capture)
    is_en_passant_bin = bit_func(is_en_passant)
    is_promotion_bin = bit_func(is_promotion)
    is_castles_bin = bit_func(is_castles)

    # Determine the types of pieces involved
    capture_piece_type = board.piece_type_at(move.to_square)
    promotion_piece_type = move.promotion

    # Piece Type Encoding
    capture_color = not board.turn if is_capture else None  # The opposite color if there is a capture
    capture_piece_bin = encode_piece(capture_piece_type, capture_color)

    promotion_color = board.turn if is_promotion else None  # The same color if there is a promotion
    promotion_piece_bin = encode_piece(promotion_piece_type, promotion_color)

    # Concatenating to form the final binary string
    move_bin = origin_file_bin + origin_rank_bin + dest_file_bin + dest_rank_bin
    extra_bits = is_capture_bin + is_en_passant_bin + is_promotion_bin + is_castles_bin + capture_piece_bin + promotion_piece_bin
    final_move_bin = move_bin + extra_bits

    return final_move_bin


def binary_board_to_ascii_board(binary_str):
    # Initialize an empty board in ASCII format
    ascii_board = [[' ' for _ in range(8)] for _ in range(8)]

    # Piece lookup table
    piece_lookup = {
        '001': 'p',
        '010': 'r',
        '011': 'n',
        '100': 'b',
        '101': 'q',
        '110': 'k',
    }

    # Loop through the board's squares
    for square in range(64):
        # Extract the 4-bit chunk corresponding to this square
        chunk = binary_str[square * 4: square * 4 + 4]

        # Extract the color bit and the piece bits
        color_bit, piece_bits = chunk[0], chunk[1:]

        # Decode the piece type
        piece = piece_lookup.get(piece_bits, '.')

        # Convert to uppercase if the piece is white
        if color_bit == '1':
            piece = piece.upper()

        # Place the piece on the board
        row, col = divmod(square, 8)
        ascii_board[row][col] = piece

    # Convert the board to string format
    ascii_str = '\n'.join(reversed([' '.join(row) for row in ascii_board]))
    return ascii_str


# Function for a bot to make a move
def _bot_move(board):
    # Get the list of all legal moves
    legal_moves = list(board.legal_moves)

    # Print available moves
    # print("Available moves:", [move_to_binary(move, board) for move in legal_moves])

    # Randomly select a move
    selected_move = random.choice(legal_moves)

    # Print the selected move
    print("Selected move:", board.uci(selected_move))
    print(f"Selected move binary: {move_to_binary(selected_move, board)}")

    # Make the move on the board
    board.push(selected_move)

    resulting_board_str = binary_board_to_ascii_board(board_to_binary(board))
    if resulting_board_str != str(board):
        print('-------------')
        print(board)
        print('-------------')
        print(binary_board_to_ascii_board(board_to_binary(board)))
        binary_board_to_ascii_board(board_to_binary(board))


def main():
    # Initialize a chess board
    board = chess.Board()

    # Simulate the game
    while not board.is_game_over():
        print("\nBoard position:")
        print(binary_board_to_ascii_board(board_to_binary(board)))

        if board.turn == chess.WHITE:
            print("\nWhite's turn")
        else:
            print("\nBlack's turn")

        _bot_move(board)

    # Simulate the game
    while not board.is_game_over():
        print("\nBoard position:")
        print(binary_board_to_ascii_board(board_to_binary(board)))

        if board.turn == chess.WHITE:
            print("\nWhite's turn")
        else:
            print("\nBlack's turn")

        _bot_move(board)

    # Print the result
    if board.is_checkmate():
        print("\nCheckmate!")
    elif board.is_stalemate():
        print("\nStalemate!")
    elif board.is_insufficient_material():
        print("\nInsufficient material!")
    elif board.is_seventyfive_moves():
        print("\nDraw due to 75-move rule!")
    elif board.is_fivefold_repetition():
        print("\nDraw due to fivefold repetition!")
    elif board.is_variant_draw():
        print("\nDraw due to variant-specific rules!")
    else:
        print("\nGame over (unknown reason).")

    print("\nFinal board position:")
    print(binary_board_to_ascii_board(board_to_binary(board)))


if __name__ == '__main__':
    main()
