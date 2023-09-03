from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
from tqdm import tqdm
import time
import os
import random
import json
from multiprocessing import Pool
from itertools import combinations

from visualize import visualize_genome
from json_converter import genome_to_json, json_to_genome
from organism import Organism
from genome import Genome
from mutation_handler import Mutation
from population import Population
from fitness import Fitness
from dataset_manager import DatasetManager
from game_controller import GameController
from innovation_handler import InnovationHandler
from constants import Constants

random.seed(Constants.random_seed)


def save_hall_of_fame(hall_of_fame, generation, pruned=False):
    current_time = time.strftime("%Y-%m-%d__%H-%M-%S")
    folder_name = f"saved_genomes/{current_time}_generation_{generation}"
    if pruned:
        folder_name += "_pruned"
    os.makedirs(folder_name, exist_ok=True)

    # Step 5: Save each pruned organism's genome to a JSON file in the folder
    for organism in hall_of_fame:
        genome_data = genome_to_json(organism.genome)
        json_file_path = os.path.join(folder_name, f"{organism.organism_id}.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(genome_data, json_file, indent=4)


def save_population(population, generation, is_host):
    current_time = time.strftime("%Y-%m-%d__%H-%M-%S")
    population_name = "host" if is_host else "parasite"
    folder_name = f"saved_genomes/populations/{population_name}_gen{generation}_{current_time}"
    os.makedirs(folder_name, exist_ok=True)

    for organism in population.organisms:
        genome_data = genome_to_json(organism.genome)
        json_file_path = os.path.join(folder_name, f"{organism.organism_id}_{organism.fitness}.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(genome_data, json_file, indent=4)
    # Save metadata
    json_file_path = os.path.join(folder_name, f"metadata.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(population.get_metadata_dict(), json_file, indent=4)


def prune_hall_of_fame(hall_of_fame, generation):
    print('++++++++++++++++++++++++++++')
    print('Pruning hall of fame...')
    # Step 1: Prepare arguments
    organisms = hall_of_fame
    champions = hall_of_fame
    challengers_for_parasites = []  # Empty because we're only interested in hall_of_fame vs. hall_of_fame
    precalc_results = None  # No precalculated results

    # TODO IMPORTANT fix prune hall of fame for chess

    # Step 2: Call evaluate_fitness_async
    all_results, _ = Fitness.evaluate_fitness_chess_puzzles_singleplayer_async(
        organisms=organisms,
        champions=champions,
        challengers_for_parasites=challengers_for_parasites,
        precalc_results=precalc_results,
        one_way=True)

    # Step 3: Analyze results to get top_n organisms
    # Initialize a dictionary to hold the sum of game results for each organism
    sum_results = {organism.organism_id: 0 for organism in hall_of_fame}

    for (org1_id, org2_id, _), result in all_results.items():
        sum_results[org1_id] += result
        sum_results[org2_id] -= result  # Assuming that a positive result is good for org1 and bad for org2

    # Sort the organisms by their summed game results
    sorted_organisms = sorted(hall_of_fame, key=lambda x: sum_results[x.organism_id], reverse=True)

    # Keep only the top_n organisms
    pruned_hall_of_fame = sorted_organisms[:Constants.min_reduced_hof_size]

    save_hall_of_fame(pruned_hall_of_fame, generation, pruned=True)

    print('++++++++++++++++++++++++++++')
    return pruned_hall_of_fame


def load_population(population_folder):
    population_organisms = []
    for filename in os.listdir(population_folder):
        with open(os.path.join(population_folder, filename)) as f:
            json_data = json.loads(f.read())
        loaded_genome = json_to_genome(json_data)
        # Extract organism_id and fitness from the filename
        organism_id, fitness = [int(x) for x in filename.split('.')[0].split('_')]
        new_organism = Organism(loaded_genome, organism_id=organism_id)
        new_organism.fitness = fitness
        population_organisms.append(new_organism)
    population = Population(organisms=population_organisms)
    return population


def main():
    # host_population_folder = 'saved_genomes/populations/host_gen2_2023-08-29__12-46-08'
    # parasite_population_folder = 'saved_genomes/populations/parasite_gen2_2023-08-29__12-46-11'
    host_population_folder = None
    parasite_population_folder = None
    max_generations = 500

    # Initialization
    if host_population_folder is None:
        host_population = Population()
    else:
        host_population = load_population(host_population_folder)
        InnovationHandler()._curOrganismId = max(InnovationHandler()._curOrganismId,
                                                 max([x.organism_id for x in host_population.organisms])+1)
    if parasite_population_folder is None:
        parasite_population = Population()
    else:
        parasite_population = load_population(parasite_population_folder)
        InnovationHandler()._curOrganismId = max(InnovationHandler()._curOrganismId,
                                                 max([x.organism_id for x in parasite_population.organisms])+1)

    hall_of_fame = []

    # Main evolutionary loop
    for generation in range(1, max_generations+1):
        gen_start_time = time.time()

        challengers_for_hosts = parasite_population.select_challengers(hall_of_fame)
        challengers_for_parasites = host_population.select_challengers(hall_of_fame)

        # TODO put back
        # all_host_results, parasite_precalc_results = Fitness.evaluate_fitness_chess_puzzles_singleplayer_async(
        #     organisms=host_population.organisms,
        #     champions=challengers_for_hosts,
        #     challengers_for_parasites=challengers_for_parasites)
        #
        # all_parasite_results, _ = Fitness.evaluate_fitness_chess_puzzles_singleplayer_async(
        #     organisms=parasite_population.organisms,
        #     champions=challengers_for_parasites,
        #     challengers_for_parasites=challengers_for_hosts,
        #     precalc_results=parasite_precalc_results)

        # TODO remove
        all_host_results, parasite_precalc_results = Fitness.evaluate_fitness_adversarial_async(
            organisms=host_population.organisms,
            champions=challengers_for_hosts,
            challengers_for_parasites=challengers_for_parasites)

        all_parasite_results, _ = Fitness.evaluate_fitness_adversarial_async(
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

        # Calculate exact loss (NOTE: this cannot be done without labeled dataset)
        dataset = DatasetManager().xor_dataset()
        host_loss = GameController.play_labeled_dataset_single_player(host_champ, dataset)
        parasite_loss = GameController.play_labeled_dataset_single_player(parasite_champ, dataset)
        print(f"Generation {generation}: host champion loss: {host_loss}")
        print(f"Generation {generation}: parasite champion loss: {parasite_loss}")

        host_white_result = GameController.play_game(host_champ, parasite_champ, host_is_white=True)
        host_black_result = GameController.play_game(host_champ, parasite_champ, host_is_white=False)
        champ_result_sum = host_white_result + host_black_result
        if champ_result_sum > 0:
            overall_champ = host_champ
        elif champ_result_sum < 0:
            overall_champ = parasite_champ
        else:
            overall_champ = host_champ if random.random() < 0.5 else parasite_champ

        hof_champ_str = "host" if overall_champ == host_champ else "parasite"
        hall_of_fame.append(overall_champ)
        print(f"The {hof_champ_str} was added to HoF")

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

        if len(hall_of_fame) >= Constants.max_hof_size:
            hall_of_fame = prune_hall_of_fame(hall_of_fame, generation)
        elif generation % 1 == 0:
            save_hall_of_fame(hall_of_fame, generation)
            save_population(host_population, generation+1, is_host=True)
            save_population(parasite_population, generation+1, is_host=False)

        print(f'Processed generation {generation} in {round(time.time() - gen_start_time, 3)}s')
        print("----------------------------")


if __name__ == "__main__":
    main()
