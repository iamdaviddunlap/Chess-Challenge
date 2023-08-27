import random
import torch
import numpy as np
from torch.profiler import profile, record_function, ProfilerActivity

from constants import Constants
from dataset_manager import DatasetManager

random.seed(Constants.random_seed)


class GameController:

    @staticmethod
    def play_game(host, parasite, host_is_white, **kwargs):
        result = GameController.play_supervised_learning(host, parasite, **kwargs)
        return result

    @staticmethod
    def play_chess(white_player, black_player):
        return -1  # TODO implement play_chess

    # @staticmethod
    # def play_labeled_dataset_single_player(player, dataset, **kwargs):
    #     with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA], record_shapes=True) as prof:
    #         with record_function("play_labeled_dataset_single_player"):
    #             player_loss = 0.0
    #
    #             # Iterate over dataset
    #             for item in dataset:
    #                 # print(f"Memory Allocated: {torch.cuda.memory_allocated() / 1e6} MB")
    #                 # print(f"Memory Reserved: {torch.cuda.memory_reserved() / 1e6} MB")
    #
    #                 # Separating inputs and correct outputs based on Constants.outputs_count
    #                 inputs = item[:-Constants.outputs_count]
    #                 correct_outputs = item[-Constants.outputs_count:]
    #
    #                 player.genome.reset_state()
    #
    #                 # Assuming player.genome.activate() returns an array of outputs of length Constants.outputs_count
    #                 player_outputs = player.genome.activate(inputs, **kwargs).cpu()
    #
    #                 # Checking for NaNs in player_outputs
    #                 if any(np.isnan(output) for output in player_outputs):
    #                     raise Exception('Got nan as player output :(')
    #
    #                 # Calculating the loss for each output and summing them
    #                 for correct_output, player_output in zip(correct_outputs, player_outputs):
    #                     player_output = player_output.item()  # Extract value from tensor if it's a tensor
    #                     player_loss += abs(correct_output - player_output)
    #
    #             torch.cuda.empty_cache()
    #     print(prof.key_averages().table(sort_by="cuda_time_total"))
    #     return player_loss
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
