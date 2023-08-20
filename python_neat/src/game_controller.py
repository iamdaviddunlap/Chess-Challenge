import random
import torch

from constants import Constants
from dataset_manager import DatasetManager

random.seed(Constants.random_seed)


class GameController:

    @staticmethod
    def play_game(host, parasite, host_is_white):
        result = GameController.play_supervised_learning(host, parasite)
        return result

    @staticmethod
    def play_chess(white_player, black_player):
        return -1  # TODO implement play_chess

    @staticmethod
    def play_labeled_dataset_single_player(player, dataset):
        player_loss = 0.0

        # Iterate over dataset
        for item in dataset:
            inputs = item[:-1]
            correct_output = item[-1]
            player.genome.reset_state()
            player_output = player.genome.activate(inputs)
            # player_output = random.random()  # TODO take this out!
            player_output = player_output.item()  # Extract value from tensor

            player_loss += abs(correct_output - player_output)

        return player_loss

    @staticmethod
    def play_supervised_learning(host_player, parasite_player):
        # dataset = DatasetHolder.XORDataset()
        # dataset = DatasetHolder.GaussianClassificationDataset()
        dataset = DatasetManager().xor_dataset()

        host_loss = GameController.play_labeled_dataset_single_player(host_player, dataset)
        parasite_loss = GameController.play_labeled_dataset_single_player(parasite_player, dataset)

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
