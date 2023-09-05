from collections import defaultdict
from threading import Lock
from concurrent.futures import ProcessPoolExecutor
import time
import math
import numpy
import numpy as np
from tqdm import tqdm
import os
from torch.multiprocessing import Pool

from constants import Constants
from game_controller import GameController


class Fitness:

    @staticmethod
    def play_game_sync(args):
        host, challenger, host_is_white, precalc_results = args
        key = (host.organism_id, challenger.organism_id, host_is_white)
        if precalc_results and key in precalc_results:
            result = precalc_results[key]
        else:
            result = GameController.play_game(host, challenger, host_is_white)
        return key, result

    @staticmethod
    def prepare_game_args(host, challengers, precalc_results=None, one_way=False):
        game_args = []
        for challenger in challengers:
            if one_way and host.organism_id >= challenger.organism_id:
                continue
            for i in range(2):
                host_is_white = i == 0
                game_args.append((host, challenger, host_is_white, precalc_results))
        return game_args

    @staticmethod
    def evaluate_fitness_adversarial_async(organisms, champions, challengers_for_parasites, precalc_results=None, one_way=False):
        all_game_args = []
        all_host_results = {}  # Dictionary to hold the host results
        parasite_precalc_results = {}  # Dictionary to hold the parasite precalculation results
        challengers_for_parasites_ids = [x.organism_id for x in challengers_for_parasites]

        for host in organisms:
            game_args = Fitness.prepare_game_args(host, champions, one_way=one_way)
            key_func = lambda x: (x[0].organism_id, x[1].organism_id, x[2])
            if precalc_results is not None:
                non_dup_game_args = [x for x in game_args if key_func(x) not in precalc_results.keys()]
                precalced = {key_func(x): precalc_results[key_func(x)]
                             for x in game_args if x not in non_dup_game_args}
                game_args = non_dup_game_args
                all_host_results = {**all_host_results, **precalced}
            all_game_args.extend(game_args)

        with Pool() as pool:
            for key, result in tqdm(pool.imap(Fitness.play_game_sync, all_game_args), total=len(all_game_args)):
                original_key = key
                value = result
                all_host_results[original_key] = value

                # Only create precalc_results if we didn't get any - ie the organisms are from the host population
                if precalc_results is None:
                    # Check if the host is in challengers_for_parasites and update the parasite results
                    host = original_key[0]  # Assuming the host ID is the first element in the key
                    if host in challengers_for_parasites_ids:
                        new_value = -value
                        new_key = (original_key[1], original_key[0], not original_key[2])
                        parasite_precalc_results[new_key] = new_value

        return all_host_results, parasite_precalc_results

    @staticmethod
    def convert_player_scores_to_results_dict(organisms, champions, scores_dict):
        result_dict = dict()
        for host in organisms:
            for challenger in champions:
                for i in range(2):
                    host_is_white = i == 0
                    key = (host.organism_id, challenger.organism_id, host_is_white)
                    result_dict[key] = GameController.scores_to_int(scores_dict[host.organism_id],
                                                                    scores_dict[challenger.organism_id],
                                                                    one_if_player1_is_bigger=True)
        return result_dict

    @staticmethod
    def evaluate_fitness_chess_puzzles_singleplayer_async(organisms):
        chess_puzzles_inputs = GameController.get_chess_puzzles_inputs(device="cpu")
        input_args = [(o, chess_puzzles_inputs) for o in organisms]
        organism_scores = dict()

        if Constants.half_power:
            num_processes = 8
        else:
            num_processes = 16
        with Pool(processes=num_processes) as pool:
            for organism_id, total_score in tqdm(pool.imap(GameController.play_chess_puzzles_singleplayer, input_args), total=len(input_args)):
                organism_scores[organism_id] = total_score

        print(organism_scores)
        return organism_scores

    @staticmethod
    def convert_game_result_to_fitness(result):
        if result == 1:
            return Constants.fitness_reward_win
        elif result == 0:
            return Constants.fitness_reward_draw
        elif result == -1:
            return Constants.fitness_reward_loss
        else:
            raise ValueError("Result out of range")

    @staticmethod
    def assign_fitnesses(host_population, host_game_results, penalize_size=False):
        parasite_defeat_count = defaultdict(set)
        for result in host_game_results.items():
            host, parasite, _ = result[0]
            game_result = result[1]
            if game_result > 0:
                parasite_defeat_count[parasite].add(host)

        max_nodes_count = max(len(o.genome.nodes) for o in host_population.organisms)
        worst_ratio = max(len(o.genome.connections) / math.pow(len(o.genome.nodes), 2) for o in host_population.organisms)

        for organism in host_population.organisms:
            total_penalty = 0
            if penalize_size:
                nodes_ratio = len(organism.genome.nodes) / max_nodes_count
                conns_ratio = (len(organism.genome.connections) / math.pow(len(organism.genome.nodes), 2)) / worst_ratio
                total_penalty = ((nodes_ratio + conns_ratio) / 2.0) * Constants.fitness_penalty_factor

            organism_game_results = [x for x in host_game_results.items() if x[0][0] == organism.organism_id]
            is_undefeated = len([x for x in organism_game_results if x[1] != 1]) == 0
            total_fitness_reward = 0
            for result in organism_game_results:
                parasite = result[0][1]
                game_result = result[1]
                unique_defeats = len(parasite_defeat_count[parasite]) if parasite in parasite_defeat_count else 0
                reward_modifier = 1.0 / unique_defeats if unique_defeats > 0 else 2.0
                total_fitness_reward += reward_modifier * Fitness.convert_game_result_to_fitness(game_result)

            species_count = sum(1 for o in host_population.organisms if o.species_id == organism.species_id)
            species_count_log = np.log(species_count+1)
            if is_undefeated:
                undefeated_special_mod = 2.0
                total_fitness_reward *= undefeated_special_mod
                organism.fitness = (total_fitness_reward / (species_count_log / undefeated_special_mod)) - (total_penalty / undefeated_special_mod)
            else:
                organism.fitness = (total_fitness_reward / species_count_log) - total_penalty

        # Normalize fitnesses
        min_fitness = min(o.fitness for o in host_population.organisms)
        max_fitness = max(o.fitness for o in host_population.organisms)
        range_fitness = max(max_fitness - min_fitness, 0.001)
        for organism in host_population.organisms:
            # Normalizing between 0 and 1
            normalized_fitness = (organism.fitness - min_fitness) / range_fitness
            # Scaling and translating to [0.01, 1.0]
            scaled_normalized_fitness = normalized_fitness * 0.99 + 0.01
            # Check for NaN
            if np.isnan(scaled_normalized_fitness):
                scaled_normalized_fitness = 0.00

            organism.fitness = scaled_normalized_fitness
