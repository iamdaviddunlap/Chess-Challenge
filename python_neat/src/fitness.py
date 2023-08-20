from collections import defaultdict
from threading import Lock
from concurrent.futures import ProcessPoolExecutor
import time
import math

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
    def evaluate_fitness_sync(host, challengers, precalc_results=None):
        results = {}
        start = time.time()
        for challenger in challengers:
            for i in range(2):
                host_is_white = i == 0
                key = (host.organism_id, challenger.organism_id, host_is_white)
                if precalc_results and key in precalc_results:
                    result = precalc_results[key]
                else:
                    result = GameController.play_game(host, challenger, host_is_white)
                results[key] = result

        print(f'Sync finished playing {len(results)} games in {time.time() - start}s')
        return results

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
