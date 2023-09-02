import random
import torch
import numpy as np
import chess
import tqdm
import logging
from torch.profiler import profile, record_function, ProfilerActivity

from chess_util import board_to_binary, move_to_binary, MOVE_ENCODING_LENGTH, STARTING_POSITION_INPUT_TENSOR
from constants import Constants
from dataset_manager import DatasetManager

random.seed(Constants.random_seed)


class GameController:

    @staticmethod
    def play_game(host, parasite, host_is_white, **kwargs):
        # result = GameController.play_supervised_learning(host, parasite, **kwargs)
        result = GameController.play_chess_puzzles(host.genome, parasite.genome, **kwargs)
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
            correct_outputs = item[-Constants.outputs_count:].cpu()

            player.genome.reset_state()

            # Assuming player.genome.activate() returns an array of outputs of length Constants.outputs_count
            player_outputs = player.genome.activate(inputs, **kwargs).cpu()

            # Checking for NaNs in player_outputs
            if any(np.isnan(output) for output in player_outputs):
                raise Exception('Got nan as player output :(')

            # Calculating the loss for each output and summing them
            for correct_output, player_output in zip(correct_outputs, player_outputs):
                player_output = player_output.item()  # Extract value from tensor if it's a tensor
                player_loss += abs(correct_output - player_output)

        torch.cuda.empty_cache()
        return player_loss

    @staticmethod
    def play_supervised_learning(host_player, parasite_player, gpu_chance=0.0, **kwargs):
        # dataset = DatasetHolder.XORDataset()
        # dataset = DatasetHolder.GaussianClassificationDataset()

        device = "cuda" if random.random() < gpu_chance else "cpu"
        host_player.to_device(device)
        parasite_player.to_device(device)
        dataset = DatasetManager().concentric_circle_dataset(device=device)

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
        old_internal_activations = player.activations.clone()
        best_activation = -10000000
        best_move_idx = None
        best_internal_activations = old_internal_activations
        for i in range(len(all_moves_input_tensors)):
            input_tensor = all_moves_input_tensors[i]
            output_result = player.activate(input_tensor).cpu().item()
            if output_result > best_activation:
                best_activation = output_result
                best_move_idx = i
                best_internal_activations = player.activations.clone()  # TODO do we need to be cloning here?
            player.activations = old_internal_activations

        if apply_best_activation:
            player.activations = best_internal_activations
        return best_move_idx, best_internal_activations

    @staticmethod
    def play_chess_puzzles(player1, player2, gpu_chance=0.2, **kwargs):
        device = "cuda" if random.random() < gpu_chance else "cpu"
        player1.to_device(device)
        player2.to_device(device)

        # Get the (newly shuffled) puzzles dataset and clip to the number of puzzles we're evaluating per game
        puzzles_dataset = DatasetManager().get_chess_puzzle_dataset()
        puzzles_dataset = puzzles_dataset[:Constants.num_puzzles_per_game]

        # Loop over each puzzle, totaling each player's score (% of moves correctly predicted * the puzzle's difficulty)
        player_1_total_score = 0
        player_2_total_score = 0
        for _, puzzle in puzzles_dataset.iterrows():
            # Extract the puzzle info from the dataframe row
            fen = puzzle['FEN']
            moves = puzzle['Moves'].split(' ')
            difficulty = puzzle['Rating_mod']

            board = chess.Board(fen=fen)

            # Initialize players' weights with the initial board state before the puzzle begins
            binary_input_string = board_to_binary(board) + '0' * MOVE_ENCODING_LENGTH
            tensor_input = torch.tensor([int(c) for c in binary_input_string], dtype=torch.float).to(device)
            player1.activate(tensor_input)
            player2.activate(tensor_input)

            # Loop over all the moves in this puzzle. The player is only 1 color, so half the moves are just played and
            # not evaluated. The first move in the moves list is not the players' move
            is_player_turn = False
            player1_correct_moves = 0
            player2_correct_moves = 0
            player1_is_out = False
            player2_is_out = False
            for i in range(len(moves)):
                if is_player_turn:
                    correct_move = moves[i]
                    binary_board_string = board_to_binary(board)

                    # Create the input tensors for all legal moves
                    # Do this here so we can use the same ones for both players
                    all_moves_input_tensors = []
                    legal_moves_lst = [x for x in board.legal_moves]
                    for potential_move in legal_moves_lst:
                        model_input_str = binary_board_string + move_to_binary(potential_move, board)
                        model_input_tensor = torch.tensor([int(c) for c in model_input_str], dtype=torch.float).to(device)
                        all_moves_input_tensors.append(model_input_tensor)

                    # Only get a player's preferred move if they've not been eliminated
                    if not player1_is_out:
                        player1_move_idx, p1_best_internal_activations = GameController._get_player_best_move(
                            player1, all_moves_input_tensors, apply_best_activation=False)
                        player1_move = legal_moves_lst[player1_move_idx]
                        if player1_move.uci() == moves[i]:
                            player1_correct_moves += 1
                            player1.activations = p1_best_internal_activations
                        else:
                            player1_is_out = True
                    if not player2_is_out:
                        player2_move_idx, p2_best_internal_activations = GameController._get_player_best_move(
                            player2, all_moves_input_tensors, apply_best_activation=False)
                        player2_move = legal_moves_lst[player2_move_idx]
                        if player2_move.uci() == correct_move:
                            player2_correct_moves += 1
                            player2.activations = p2_best_internal_activations
                        else:
                            player2_is_out = True

                # Quit the puzzle early if both players have been eliminated
                if player1_is_out and player2_is_out:
                    break

                # Apply the move to the board and switch if it is the players' turn or not
                board.push_uci(moves[i])
                is_player_turn = not is_player_turn

            # When this puzzle has been completed, update both players' scores
            # The score = % of moves correctly predicted * the puzzle's difficulty
            player_moves_in_puzzle = float(len(moves[1::2]))
            player_1_ratio = player1_correct_moves / player_moves_in_puzzle
            player_2_ratio = player2_correct_moves / player_moves_in_puzzle
            player_1_total_score += player_1_ratio * difficulty
            player_2_total_score += player_2_ratio * difficulty

        player1.reset_state()
        player2.reset_state()

        # At the end of evaluating all puzzles, return which player is better
        # TODO maybe also return the average difficulty of the puzzles so that can be factored into fitness?
        #  Probably not necessary if the number of puzzles we use is sufficiently high
        if abs(player_1_total_score - player_2_total_score) < 0.0001:
            return 0
        if player_1_total_score > player_2_total_score:
            return 1
        return -1


    @staticmethod
    def get_chess_puzzles_inputs(device):
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
                        model_input_tensor = torch.tensor([int(c) for c in model_input_str], dtype=torch.float).to(device)
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
            player.activate(STARTING_POSITION_INPUT_TENSOR.to(device))
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
