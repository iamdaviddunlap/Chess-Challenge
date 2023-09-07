import random
import numpy as np
import chess
import tqdm
import logging
from torch.profiler import profile, record_function, ProfilerActivity

from chess_util import *
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
    def get_player_best_move(player, all_moves_input_arr, calculate_full_preference=False, apply_best_activation=True):
        """
        Given a list of tensors, activate the player with each tensor and return the index of the input that resulted
        in the most activated output.
        """
        old_internal_activations = np.copy(player.activations)
        best_activation = -10000000
        best_move_idx = None
        best_internal_activations = old_internal_activations
        all_input_results = dict()
        for i in range(len(all_moves_input_arr)):
            input_arr = all_moves_input_arr[i]
            output_result = player.activate(input_arr)[0]
            all_input_results[i] = output_result
            if output_result > best_activation:
                best_activation = output_result
                best_move_idx = i
                best_internal_activations = np.copy(player.activations)  # TODO do we need to be cloning here?
            player.activations = old_internal_activations

        if apply_best_activation:
            player.activations = best_internal_activations

        if calculate_full_preference:
            board_obj = [analyze_full_input_arr(x) for x in all_moves_input_arr][0][0]
            legal_moves_objs = [x for x in board_obj.legal_moves]
            agent_best_move_uci = legal_moves_objs[best_move_idx]
            legal_moves_evaluation = {legal_moves_objs[k]: v for k, v in all_input_results.items()}
            all_moves_agent_preference_arr = np.array([[x] for x in all_input_results.values()])
            return agent_best_move_uci, legal_moves_evaluation, all_moves_agent_preference_arr

        return best_move_idx, best_internal_activations

    @staticmethod
    def play_chess_puzzles(player1, player2, gpu_chance=0.2, **kwargs):
        chess_puzzles_inputs = GameController.get_chess_puzzles_inputs()
        player1_id, player1_score = GameController.play_chess_puzzles_singleplayer((player1, chess_puzzles_inputs))
        player2_id, player2_score = GameController.play_chess_puzzles_singleplayer((player2, chess_puzzles_inputs))
        print(f"In play_chess_puzzles, player1_score: {player1_score}, player2_score: {player2_score}")
        return GameController.scores_to_int(player1_score, player2_score, one_if_player1_is_bigger=True)


    @staticmethod
    def get_model_input_arrs_from_board(board):
        binary_board_string = board_to_binary(board)
        all_moves_input_arr = []
        legal_moves_lst = [x for x in board.legal_moves]
        for potential_move in legal_moves_lst:
            model_input_str = binary_board_string + move_to_binary(potential_move, board)
            model_input_tensor = np.array([int(c) for c in model_input_str], dtype=float)
            all_moves_input_arr.append(model_input_tensor)
        return all_moves_input_arr


    @staticmethod
    def get_chess_puzzles_inputs():
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

            puzzle_initial_input = board_to_binary(board) + ''.join(['0']*MOVE_ENCODING_LENGTH)
            # Swap the first character: 1 <-> 0 (we do this because the active player is NOT the puzzle player)
            puzzle_initial_input = puzzle_initial_input[0].replace("1", "a").replace("0", "1").replace("a", "0") + \
                                   puzzle_initial_input[1:]
            puzzle_initial_input = np.array([int(c) for c in puzzle_initial_input], dtype=float)

            puzzle_inputs = []

            is_player_turn = False
            for i in range(len(moves)):
                if is_player_turn:
                    correct_move = moves[i]

                    all_moves_input_arr = GameController.get_model_input_arrs_from_board(board)

                    legal_moves_lst = [x for x in board.legal_moves]
                    correct_move_idx = [x.uci() for x in legal_moves_lst].index(correct_move)
                    puzzle_inputs.append((np.array(all_moves_input_arr), correct_move_idx))

                # Apply the move to the board and switch if it is the players' turn or not
                board.push_uci(moves[i])
                is_player_turn = not is_player_turn

            all_puzzle_inputs.append((puzzle_initial_input, puzzle_inputs, difficulty))

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
            puzzle_initial_input, puzzle_lst, difficulty = puzzle_tup
            player.activate(puzzle_initial_input)
            total_correct_moves = 0
            for moves_tuple in puzzle_lst:
                moves_input_tensors, correct_idx = moves_tuple
                best_move_idx, best_internal_activations = GameController.get_player_best_move(
                    player, moves_input_tensors, apply_best_activation=False)
                if best_move_idx == correct_idx:
                    total_correct_moves += 1
                    player.activations = best_internal_activations
                else:
                    break
            player.reset_state()
            target_correct_moves = float(len(puzzle_lst))
            player_ratio = total_correct_moves / target_correct_moves
            total_score += player_ratio * difficulty
        return organism_id, total_score
