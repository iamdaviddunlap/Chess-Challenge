from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
from tqdm import tqdm
import time
import os
from multiprocessing import Pool

from visualize import visualize_genome
from json_converter import genome_to_json
from organism import Organism
from genome import Genome
from mutation_handler import Mutation
from population import Population
from fitness import Fitness


def main():
    max_generations = 100

    # Initialization
    host_population = Population()
    parasite_population = Population()

    hall_of_fame = []

    # Main evolutionary loop
    for generation in range(max_generations):

        parasite_precalc_results = defaultdict(int)
        all_host_results = defaultdict(int)
        all_parasite_results = defaultdict(int)

        challengers_for_hosts = parasite_population.select_challengers(hall_of_fame)
        challengers_for_parasites = host_population.select_challengers(hall_of_fame)

        # # Evaluate raw fitness for hosts
        # with Pool(processes=os.cpu_count()) as pool:
        #     for host in tqdm(host_population.organisms):
        #         game_args = Fitness.prepare_game_args(host, challengers_for_hosts)
        #         for key, result in pool.imap(Fitness.play_game_sync, game_args):
        #             all_host_results[key] = result
        #             if host in challengers_for_parasites:
        #                 new_value = -result
        #                 new_key = (key[1], key[0], not key[2])
        #                 parasite_precalc_results[new_key] = new_value
        # Evaluate raw fitness for hosts

        all_host_results, parasite_precalc_results = Fitness.evaluate_fitness_async(
            organisms=host_population.organisms,
            champions=challengers_for_hosts,
            challengers_for_parasites=challengers_for_parasites)

        all_parasite_results, _ = Fitness.evaluate_fitness_async(
            organisms=parasite_population.organisms,
            champions=challengers_for_parasites,
            challengers_for_parasites=challengers_for_hosts,
            precalc_results=parasite_precalc_results)

        x = 1

        # # Evaluate raw fitness of parasites
        # for parasite in parasite_population.organisms:
        #     cur_parasite_game_winners = Fitness.evaluate_fitness_sync(parasite, challengers_for_parasites, parasite_precalc_results)
        #     all_parasite_results.update(cur_parasite_game_winners)

        # # Calculate fitnesses for the organisms in each population
        # penalize_size = True
        # Fitness.assign_fitnesses(host_population, all_host_results, penalize_size)
        # Fitness.assign_fitnesses(parasite_population, all_parasite_results, penalize_size)
        #
        # # Get some metrics about how things are going
        # host_champ = host_population.get_superchamp()
        # parasite_champ = parasite_population.get_superchamp()
        # dataset = DatasetHolder.XORDataset()
        # host_loss = GameController.play_labeled_dataset_single_player(host_champ, random, dataset)
        # parasite_loss = GameController.play_labeled_dataset_single_player(parasite_champ, random, dataset)
        #
        # overall_champ = host_champ if host_loss < parasite_loss else parasite_champ
        # overall_champ_guess_based_on_fitness = host_champ if host_champ.fitness > parasite_champ.fitness else parasite_champ
        # fitter_champ_str = "host" if overall_champ_guess_based_on_fitness == host_champ else "parasite"
        # hall_of_fame.append(overall_champ)
        #
        # print(f"Generation {generation}: host champion loss: {host_loss}")
        # print(f"Generation {generation}: parasite champion loss: {parasite_loss}")
        # print(f"The {fitter_champ_str} is fitter")
        # print("----------------------------")
        #
        # parasite_loss2 = GameController.play_labeled_dataset_single_player(parasite_champ, dataset)
        #
        # if generation == 999:
        #     x = 1
        #
        # # Selection and breeding
        # for population in [host_population, parasite_population]:
        #     other_population = parasite_population if population == host_population else host_population
        #     population_seeds = other_population.get_n_diff_species_champs(3)
        #     population.select_and_reproduce(population_seeds)
        #
        # # Form species in both populations
        # host_population.speciate()
        # parasite_population.speciate()


if __name__ == "__main__":
    main()
