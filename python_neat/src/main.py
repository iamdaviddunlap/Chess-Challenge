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
from dataset_manager import DatasetManager
from game_controller import GameController


def main():
    max_generations = 100

    # Initialization
    host_population = Population()
    parasite_population = Population()

    hall_of_fame = []

    # Main evolutionary loop
    for generation in range(1, max_generations+1):
        gen_start_time = time.time()

        parasite_precalc_results = defaultdict(int)
        all_host_results = defaultdict(int)
        all_parasite_results = defaultdict(int)

        challengers_for_hosts = parasite_population.select_challengers(hall_of_fame)
        challengers_for_parasites = host_population.select_challengers(hall_of_fame)

        all_host_results, parasite_precalc_results = Fitness.evaluate_fitness_async(
            organisms=host_population.organisms,
            champions=challengers_for_hosts,
            challengers_for_parasites=challengers_for_parasites)

        all_parasite_results, _ = Fitness.evaluate_fitness_async(
            organisms=parasite_population.organisms,
            champions=challengers_for_parasites,
            challengers_for_parasites=challengers_for_hosts,
            precalc_results=parasite_precalc_results)

        # Calculate fitnesses for the organisms in each population
        penalize_size = True
        Fitness.assign_fitnesses(host_population, all_host_results, penalize_size)
        Fitness.assign_fitnesses(parasite_population, all_parasite_results, penalize_size)

        # Get some metrics about how things are going
        host_champ = host_population.get_superchamp()
        parasite_champ = parasite_population.get_superchamp()
        dataset = DatasetManager().xor_dataset()
        host_loss = GameController.play_labeled_dataset_single_player(host_champ, dataset)
        parasite_loss = GameController.play_labeled_dataset_single_player(parasite_champ, dataset)

        overall_champ = host_champ if host_loss < parasite_loss else parasite_champ
        overall_champ_guess_based_on_fitness = host_champ if host_champ.fitness > parasite_champ.fitness else parasite_champ
        fitter_champ_str = "host" if overall_champ_guess_based_on_fitness == host_champ else "parasite"
        hall_of_fame.append(overall_champ)

        print(f"Generation {generation}: host champion loss: {host_loss}")
        print(f"Generation {generation}: parasite champion loss: {parasite_loss}")
        print(f"The {fitter_champ_str} is fitter")

        if host_loss <= 0.1 or parasite_loss <= 0.1:
            x = 1

        if host_loss <= 0.001 or parasite_loss <= 0.001:
            x = 1

        if generation == 999:
            x = 1

        # Selection and breeding
        seeds_from_host = host_population.get_n_diff_species_champs(3)
        seeds_from_parasite = parasite_population.get_n_diff_species_champs(3)
        for population in [host_population, parasite_population]:
            other_population = parasite_population if population == host_population else host_population
            population_seeds = seeds_from_host if other_population == host_population else seeds_from_parasite
            population.select_and_reproduce(population_seeds)

        # Form species in both populations
        host_population.speciate()
        parasite_population.speciate()

        print(f'Processed generation {generation} in {round(time.time() - gen_start_time, 3)}s')
        print("----------------------------")


if __name__ == "__main__":
    main()
