import random
import numpy as np
import chess
import tqdm
import logging
from torch.profiler import profile, record_function, ProfilerActivity

from chess_util import board_to_binary, move_to_binary, MOVE_ENCODING_LENGTH, STARTING_POSITION_INPUT_ARRAY
from constants import Constants
from dataset_manager import DatasetManager

random.seed(Constants.random_seed)


class GameController:

    @staticmethod
    def play_game(host, parasite, host_is_white, **kwargs):
        # result = GameController.play_supervised_learning(host, parasite, **kwargs)
        result = GameController.play_chess_puzzles(host, parasite, **kwargs)
        return result

    @staticmethod
    def play_chess(white_player, black_player):
        return -1  # TODO implement play_chess

    @staticmethod
    def play_labeled_dataset_single_player(player, dataset, **kwargs):
        player_loss = 0.0

        # Iterate over dataset
        for item in dataset:
            # Separating inputs and correct outputs based on Constants.outputs_count
            inputs = item[:-Constants.outputs_count]
            correct_outputs = item[-Constants.outputs_count:]

            player.genome.reset_state()

            # Assuming player.genome.activate() returns an array of outputs of length Constants.outputs_count
            player_outputs = player.genome.activate(inputs, **kwargs)

            # Checking for NaNs in player_outputs
            if any(np.isnan(output) for output in player_outputs):
                raise Exception('Got nan as player output :(')

            # Calculating the loss for each output and summing them
            for correct_output, player_output in zip(correct_outputs, player_outputs):
                player_output = player_output.item()  # Extract value from tensor if it's a tensor
                player_loss += abs(correct_output - player_output)

        return player_loss

    @staticmethod
    def scores_to_int(player1_score, player2_score, one_if_player1_is_bigger=True):
        if abs(player1_score - player2_score) < 0.0001:
            return 0
        if one_if_player1_is_bigger:
            if player1_score > player2_score:
                return 1
        else:
            if player1_score < player2_score:
                return 1
        return -1


    @staticmethod
    def play_supervised_learning(host_player, parasite_player, gpu_chance=0.0, **kwargs):
        # dataset = DatasetHolder.XORDataset()
        # dataset = DatasetHolder.GaussianClassificationDataset()

        device = "cuda" if random.random() < gpu_chance else "cpu"
        host_player.to_device(device)
        parasite_player.to_device(device)
        dataset = DatasetManager().xor_dataset(device=device)

        host_loss = GameController.play_labeled_dataset_single_player(host_player, dataset, **kwargs)
        parasite_loss = GameController.play_labeled_dataset_single_player(parasite_player, dataset, **kwargs)

        # Return 1 if host player is closer to correct XOR output, -1 otherwise
        if abs(host_loss - parasite_loss) < 0.0001:
            return 0
        if host_loss < parasite_loss:
            return 1
        return -1

    @staticmethod
    def play_random(host_player, parasite_player):
        # TODO untested
        return random.randint(-1, 1)

    @staticmethod
    def _get_player_best_move(player, all_moves_input_tensors, apply_best_activation=True):
        """
        Given a list of tensors, activate the player with each tensor and return the index of the input that resulted
        in the most activated output.
        """
        old_internal_activations = np.copy(player.activations)
        best_activation = -10000000
        best_move_idx = None
        best_internal_activations = old_internal_activations
        for i in range(len(all_moves_input_tensors)):
            input_tensor = all_moves_input_tensors[i]
            output_result = player.activate(input_tensor)[0]
            if output_result > best_activation:
                best_activation = output_result
                best_move_idx = i
                best_internal_activations = np.copy(player.activations)  # TODO do we need to be cloning here?
            player.activations = old_internal_activations

        if apply_best_activation:
            player.activations = best_internal_activations
        return best_move_idx, best_internal_activations

    @staticmethod
    def play_chess_puzzles(player1, player2, gpu_chance=0.2, **kwargs):
        chess_puzzles_inputs = GameController.get_chess_puzzles_inputs()
        player1_id, player1_score = GameController.play_chess_puzzles_singleplayer((player1, chess_puzzles_inputs))
        player2_id, player2_score = GameController.play_chess_puzzles_singleplayer((player2, chess_puzzles_inputs))
        print(f"In play_chess_puzzles, player1_score: {player1_score}, player2_score: {player2_score}")
        return GameController.scores_to_int(player1_score, player2_score, one_if_player1_is_bigger=True)


    @staticmethod
    def get_chess_puzzles_inputs(device="cpu"):
        # Get the (newly shuffled) puzzles dataset and clip to the number of puzzles we're evaluating per game
        puzzles_dataset = DatasetManager().get_chess_puzzle_dataset()
        puzzles_dataset = puzzles_dataset[:Constants.num_puzzles_per_game]

        all_puzzle_inputs = []
        for _, puzzle in puzzles_dataset.iterrows():
            # Extract the puzzle info from the dataframe row
            fen = puzzle['FEN']
            moves = puzzle['Moves'].split(' ')
            difficulty = puzzle['Rating_mod']

            board = chess.Board(fen=fen)

            puzzle_inputs = []

            is_player_turn = False
            for i in range(len(moves)):
                if is_player_turn:
                    correct_move = moves[i]
                    binary_board_string = board_to_binary(board)

                    # Create the input tensors for all legal moves
                    all_moves_input_tensors = []
                    legal_moves_lst = [x for x in board.legal_moves]
                    for potential_move in legal_moves_lst:
                        model_input_str = binary_board_string + move_to_binary(potential_move, board)
                        model_input_tensor = np.array([int(c) for c in model_input_str], dtype=np.float)
                        all_moves_input_tensors.append(model_input_tensor)
                    correct_move_idx = [x.uci() for x in legal_moves_lst].index(correct_move)
                    puzzle_inputs.append((all_moves_input_tensors, correct_move_idx))

                # Apply the move to the board and switch if it is the players' turn or not
                board.push_uci(moves[i])
                is_player_turn = not is_player_turn

            all_puzzle_inputs.append((puzzle_inputs, difficulty))

        return all_puzzle_inputs

    @staticmethod
    def play_chess_puzzles_singleplayer(args, device="cpu"):
        player, chess_puzzles_inputs = args
        organism_id = player.organism_id
        player = player.genome
        player.reset_state()
        player.to_device(device)
        total_score = 0
        for puzzle_tup in chess_puzzles_inputs:
            puzzle_lst, difficulty = puzzle_tup
            player.activate(STARTING_POSITION_INPUT_ARRAY)
            total_correct_moves = 0
            for moves_tuple in puzzle_lst:
                moves_input_tensors, correct_idx = moves_tuple
                best_move_idx, best_internal_activations = GameController._get_player_best_move(
                    player, moves_input_tensors, apply_best_activation=False)
                if best_move_idx == correct_idx:
                    total_correct_moves += 1
                    player.activations = best_internal_activations
                else:
                    break
            player.reset_state()
            target_correct_moves = float(len(puzzle_tup[0]))
            player_ratio = total_correct_moves / target_correct_moves
            total_score += player_ratio * difficulty
        return organism_id, total_score
