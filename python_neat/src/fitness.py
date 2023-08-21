from collections import defaultdict
from threading import Lock
from concurrent.futures import ProcessPoolExecutor
import time
import math
from tqdm import tqdm
import os
from multiprocessing import Pool

from constants import Constants
from game_controller import GameController


class Fitness:
    # @staticmethod
    # def convert_game_result_to_fitness(result):
    #     # TODO untested
    #     if result == 1:
    #         return Constants.fitness_reward_win
    #     elif result == 0:
    #         return Constants.fitness_reward_draw
    #     elif result == -1:
    #         return Constants.fitness_reward_loss
    #     else:
    #         raise ValueError("Result out of range")

    # @staticmethod
    # def evaluate_fitness_async(host, challengers, precalc_results=None):
    #     results = {}
    #
    #     # Function to play a game and record the result
    #     def play_and_record(challenger, i):
    #         host_is_white = i == 0
    #         key = (host.organism_id, challenger.organism_id, host_is_white)
    #         if precalc_results and key in precalc_results:
    #             result = precalc_results[key]
    #         else:
    #             host_clone = host.clone()
    #             challenger_clone = challenger.clone()
    #             result = GameController.play_game(host_clone, challenger_clone, host_is_white)
    #
    #         results[key] = result
    #
    #     # Use ThreadPoolExecutor to run the games concurrently
    #     start = time.time()
    #     with ProcessPoolExecutor() as executor:
    #         # Submit all the games as separate tasks
    #         for challenger in challengers:
    #             for i in range(2):
    #                 executor.submit(play_and_record, challenger, i)
    #
    #     print(f'Async finished playing {len(results)} games in {time.time() - start}s')
    #     return results

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
    def prepare_game_args(host, challengers, precalc_results=None):
        game_args = []
        for challenger in challengers:
            for i in range(2):
                host_is_white = i == 0
                game_args.append((host, challenger, host_is_white, precalc_results))
        return game_args

    @staticmethod
    def evaluate_fitness_async(organisms, champions, challengers_for_parasites, precalc_results=None):
        all_game_args = []
        all_host_results = {}  # Dictionary to hold the host results
        parasite_precalc_results = {}  # Dictionary to hold the parasite precalculation results
        challengers_for_parasites_ids = [x.organism_id for x in challengers_for_parasites]

        for host in organisms:
            game_args = Fitness.prepare_game_args(host, champions)
            all_game_args.extend(game_args)

        with Pool(processes=os.cpu_count()) as pool:
            for key, result in tqdm(pool.imap(Fitness.play_game_sync, all_game_args), total=len(all_game_args)):
                original_key = key
                value = result
                all_host_results[original_key] = value

                # Check if the host is in challengers_for_parasites and update the parasite results
                host = original_key[0]  # Assuming the host ID is the first element in the key
                if host in challengers_for_parasites_ids:
                    new_value = -value
                    new_key = (original_key[1], original_key[0], not original_key[2])
                    parasite_precalc_results[new_key] = new_value

        return all_host_results, parasite_precalc_results

    # @staticmethod
    # def assign_fitnesses(host_population, host_game_results, penalize_size=False):
    #     # TODO untested
    #     parasite_defeat_count = defaultdict(set)
    #     for result in host_game_results.items():
    #         host, parasite, _ = result[0]
    #         game_result = result[1]
    #         if game_result > 0:
    #             parasite_defeat_count[parasite].add(host)
    #
    #     max_nodes_count = max(o.genome.nodes_count for o in host_population.organisms)
    #     worst_ratio = max(o.genome.connections_count / math.pow(o.genome.nodes_count, 2) for o in host_population.organisms)
    #
    #     for organism in host_population.organisms:
    #         total_penalty = 0
    #         if penalize_size:
    #             nodes_ratio = organism.genome.nodes_count / max_nodes_count
    #             conns_ratio = (organism.genome.connections_count / math.pow(organism.genome.nodes_count, 2)) / worst_ratio
    #             total_penalty = ((nodes_ratio + conns_ratio) / 2.0) * Constants.fitness_penalty_factor
    #
    #         total_fitness_reward = 0
    #         for result in filter(lambda r: r[0][0] == organism, host_game_results.items()):
    #             parasite = result[0][1]
    #             game_result = result[1]
    #             unique_defeats = len(parasite_defeat_count[parasite]) if parasite in parasite_defeat_count else 0
    #             reward_modifier = 1.0 / unique_defeats if unique_defeats > 0 else 2.0
    #             total_fitness_reward += reward_modifier * Fitness.convert_game_result_to_fitness(game_result)
    #
    #         species_count = sum(1 for o in host_population.organisms if o.species_id == organism.species_id)
    #         organism.fitness = (total_fitness_reward / species_count) - total_penalty
