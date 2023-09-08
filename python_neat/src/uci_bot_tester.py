import json
import os

from chess_util import *
from json_converter import json_to_genome
from organism import Organism
from game_controller import GameController
from move_evaluation_gui import display_move_evaluation


def get_model_input_null_move(board):
    """ Returns a numpy array for use as a model input that contains the board state and all 0's for the move """
    board_bin = board_to_binary(board)
    move_bin = ''.join(['0'] * MOVE_ENCODING_LENGTH)
    binary_input_str = board_bin + move_bin
    model_input_arr = np.array([int(c) for c in binary_input_str], dtype=float)
    return model_input_arr


def min_max_scale_dict(data_dict):
    min_value = min(data_dict.values())
    max_value = max(data_dict.values())
    scaled_data = {key: 2 * ((value - min_value) / (max_value - min_value)) - 1 for key, value in data_dict.items()}
    return scaled_data


class UciInteractionBot:
    def __init__(self, organism, show_gui=False):
        self.board = chess.Board()
        self.organism = organism
        self.show_gui = show_gui

    def get_move(self):
        all_moves_input_arr = GameController.get_model_input_arrs_from_board(self.board)
        agent_best_move_uci, legal_moves_evaluation, all_moves_agent_preference_arr = \
            GameController.get_player_best_move(self.organism.genome, all_moves_input_arr,
                                                apply_best_activation=True, calculate_full_preference=True)
        legal_moves_evaluation = min_max_scale_dict(legal_moves_evaluation)

        if self.show_gui:
            display_move_evaluation(legal_moves_evaluation)

        return agent_best_move_uci

    def begin_play_uci_game(self):
        player_is_white = None
        while True:
            command = input()

            if command == 'uci':
                print(f'id name GeneticBot {self.organism.organism_id}')
                print('id author David')
                print('uciok')
            elif command == 'isready':
                print('readyok')
            elif command.startswith('position'):
                params = command.split(' ')
                if 'fen' in params:
                    fen_idx = params.index('fen')
                    fen = ' '.join(params[fen_idx + 1:])
                    self.board.set_fen(fen)
                elif 'startpos' in params:
                    self.board.reset()
                    self.organism.genome.reset_state()

                if 'moves' in params:
                    moves_idx = params.index('moves')
                    for move_uci in params[moves_idx + 1:]:
                        if player_is_white is None:
                            model_input_arr = get_model_input_null_move(self.board)
                            self.organism.genome.activate(model_input_arr)
                        elif player_is_white == self.board.turn:
                            board_bin = board_to_binary(self.board)
                            move_bin = move_to_binary(self.board.parse_uci(move_uci), self.board)
                            binary_input_str = board_bin + move_bin
                            model_input_arr = np.array([int(c) for c in binary_input_str], dtype=float)
                            self.organism.genome.activate(model_input_arr)
                        self.board.push_uci(move_uci)
            elif command.startswith('go'):
                if player_is_white is None:
                    player_is_white = self.board.turn
                    if not self.organism.genome.activations.any():
                        model_input_arr = get_model_input_null_move(self.board)
                        self.organism.genome.activate(model_input_arr)
                move = self.get_move()
                print(f'bestmove {move}')
            elif command == 'quit':
                break


if __name__ == "__main__":
    show_gui = True

    current_file_path = os.path.dirname(os.path.abspath(__file__))

    gen_45_hof_addition_fp = 'saved_genomes/hall_of_fame/hof_gen45_2023-09-07__04-21-06/14645.json'
    gen_50_hof_addition_fp = 'saved_genomes/hall_of_fame/hof_gen50_2023-09-07__16-17-57/15611.json'
    gen_53_hof_addition_fp = 'saved_genomes/hall_of_fame/hof_gen53_2023-09-07__23-31-18/16385.json'
    org_id_to_load = '14375'
    genome_file_path = os.path.join(current_file_path, gen_53_hof_addition_fp)
                                    # f'saved_genomes/hall_of_fame/hof_gen43_2023-09-06__23-25-23/{org_id_to_load}.json')
    with open(genome_file_path) as f:
        json_data = json.loads(f.read())
    loaded_genome = json_to_genome(json_data)
    loaded_organism = Organism(loaded_genome)
    uci_bot = UciInteractionBot(loaded_organism, show_gui=show_gui)
    uci_bot.begin_play_uci_game()
