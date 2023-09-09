import time
import os
import random
import json
import numpy as np
import pandas as pd

from visualize import visualize_genome
from json_converter import genome_to_json, json_to_genome
from organism import Organism
from population import Population
from fitness import Fitness
from dataset_manager import DatasetManager
from game_controller import GameController
from innovation_handler import InnovationHandler
from constants import Constants

random.seed(Constants.random_seed)


def save_hall_of_fame(hall_of_fame, generation, pruned=False):
    current_time = time.strftime("%Y-%m-%d__%H-%M-%S")
    folder_name = f"saved_genomes/hall_of_fame/hof_gen{generation}_{current_time}"
    if pruned:
        folder_name += "_pruned"
    os.makedirs(folder_name, exist_ok=True)

    # Step 5: Save each pruned organism's genome to a JSON file in the folder
    for organism in hall_of_fame:
        genome_data = genome_to_json(organism.genome)
        json_file_path = os.path.join(folder_name, f"{organism.organism_id}.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(genome_data, json_file, indent=4)


def load_hall_of_fame(hall_of_fame_folder):
    hall_of_fame = []
    for filename in os.listdir(hall_of_fame_folder):
        with open(os.path.join(hall_of_fame_folder, filename)) as f:
            json_data = json.loads(f.read())
        loaded_genome = json_to_genome(json_data)
        # Extract organism_id and fitness from the filename
        organism_id = int(filename.split('.')[0])
        new_organism = Organism(loaded_genome, organism_id=organism_id)
        hall_of_fame.append(new_organism)

    return hall_of_fame


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
    json_file_path = os.path.join(folder_name, f"pop_metadata.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(population.get_metadata_dict(), json_file, indent=4)


def load_population(population_folder):
    population_organisms = []
    metadata_filename = "pop_metadata.json"
    for filename in os.listdir(population_folder):
        if filename != metadata_filename:
            with open(os.path.join(population_folder, filename)) as f:
                json_data = json.loads(f.read())
            loaded_genome = json_to_genome(json_data)
            # Extract organism_id and fitness from the filename
            organism_id, fitness = [x for x in '.'.join(filename.split('.')[:-1]).split('_')]
            organism_id = int(organism_id)
            fitness = float(fitness)
            new_organism = Organism(loaded_genome, organism_id=organism_id)
            new_organism.fitness = fitness
            population_organisms.append(new_organism)
    population = Population(organisms=population_organisms)

    with open(os.path.join(population_folder, metadata_filename)) as f:
        pop_metadata = json.loads(f.read())
    population._cur_species_id = pop_metadata["_cur_species_id"]
    population._species_compat_thresh = pop_metadata["_species_compat_thresh"]

    InnovationHandler()._curOrganismId = max(InnovationHandler()._curOrganismId,
                                             max([x.organism_id for x in population.organisms]) + 1)
    InnovationHandler()._curNodeId = max(InnovationHandler()._curNodeId,
                                         max({node_id for o in population.organisms
                                              for node_id in [n.node_id for n in o.genome.nodes]}) + 1)
    InnovationHandler()._curConnectionId = max(InnovationHandler()._curConnectionId,
                                               max({conn_id for o in population.organisms
                                                    for conn_id in
                                                    [c.connection_id for c in o.genome.connections]}) + 1)

    return population


def get_puzzles_inputs_for_next_generation(organisms):
    num_hard_puzzles = 75
    num_random_puzzles = 25
    num_puzzles_to_play = 500

    # Get a large dataset of chess puzzles for the organisms to play
    puzzles_dataset = DatasetManager().get_chess_puzzle_dataset(keep_puzzle_id=True)
    puzzles_dataset = puzzles_dataset[:num_puzzles_to_play]
    puzzles_dataset.reset_index(inplace=True, drop=True)
    chess_puzzles_inputs = GameController.get_chess_puzzles_inputs(puzzles_dataset)

    # Calculate the average score from all organisms for each puzzle
    puzzle_scores = Fitness.evaluate_average_puzzle_score_async(
                organisms=organisms,
                chess_puzzles_inputs=chess_puzzles_inputs)
    puzzle_id_scores = {puzzles_dataset['PuzzleId'].iloc[k]: v for k, v in puzzle_scores.items()}
    print(f'Puzzle scores: {puzzle_id_scores}')

    # Selecting the num_hard_puzzles puzzles that had the lowest average score
    n_hardest_puzzles_idxs = [k for k, v in sorted(puzzle_scores.items(), key=lambda x: x[1])[:num_hard_puzzles]]
    selected_df = puzzles_dataset.iloc[n_hardest_puzzles_idxs]

    # Selecting num_random_puzzles more rows randomly from the remaining rows
    remaining_idxs = puzzles_dataset.index.difference(n_hardest_puzzles_idxs).to_list()
    random_rows = puzzles_dataset.iloc[np.random.choice(remaining_idxs, num_random_puzzles, replace=False)]

    puzzles_dataset = pd.concat([selected_df, random_rows])
    print(f'puzzle_ids for next generation: {list(puzzles_dataset["PuzzleId"])}')

    chess_puzzles_inputs = GameController.get_chess_puzzles_inputs(puzzles_dataset=puzzles_dataset)
    return chess_puzzles_inputs


def main():
    host_population_folder = 'saved_genomes/populations/host_gen45_2023-09-07__01-57-52'
    parasite_population_folder = 'saved_genomes/populations/parasite_gen45_2023-09-07__01-57-54'
    hall_of_fame_folder = 'saved_genomes/hall_of_fame/new_modded_hof_gen44'
    starting_generation = 45
    # starting_generation = 1
    # host_population_folder = None
    # parasite_population_folder = None
    # hall_of_fame_folder = None
    max_generations = 500
    chess_puzzles_inputs = None

    # Initialization
    if host_population_folder is None:
        host_population = Population()
    else:
        host_population = load_population(host_population_folder)

    if parasite_population_folder is None:
        parasite_population = Population()
    else:
        parasite_population = load_population(parasite_population_folder)

    if hall_of_fame_folder is None:
        hall_of_fame = []
    else:
        hall_of_fame = load_hall_of_fame(hall_of_fame_folder)

    # Main evolutionary loop
    for generation in range(starting_generation, max_generations+1):
        gen_start_time = time.time()

        if Constants.is_labeled_non_chess_dataset:
            challengers_for_hosts = parasite_population.select_challengers(hall_of_fame)
            challengers_for_parasites = host_population.select_challengers(hall_of_fame)
            all_host_results, parasite_precalc_results = Fitness.evaluate_fitness_adversarial_async(
                organisms=host_population.organisms,
                champions=challengers_for_hosts,
                challengers_for_parasites=challengers_for_parasites)

            all_parasite_results, _ = Fitness.evaluate_fitness_adversarial_async(
                organisms=parasite_population.organisms,
                champions=challengers_for_parasites,
                challengers_for_parasites=challengers_for_hosts,
                precalc_results=parasite_precalc_results)
        else:
            if chess_puzzles_inputs is None:
                chess_puzzles_inputs = GameController.get_chess_puzzles_inputs()

            hof_challengers = random.sample(
                hall_of_fame, k=min(len(hall_of_fame), 10))

            all_scores = Fitness.evaluate_fitness_chess_puzzles_singleplayer_async(
                organisms=host_population.organisms+parasite_population.organisms+hof_challengers,
                chess_puzzles_inputs=chess_puzzles_inputs)

            all_host_results = Fitness.convert_player_scores_to_results_dict(host_population.organisms,
                                                                             parasite_population.organisms+hof_challengers,
                                                                             all_scores)
            all_parasite_results = Fitness.convert_player_scores_to_results_dict(parasite_population.organisms,
                                                                                 host_population.organisms+hof_challengers,
                                                                                 all_scores)

        # Calculate fitnesses for the organisms in each population
        penalize_size = True
        Fitness.assign_fitnesses(host_population, all_host_results, penalize_size)
        Fitness.assign_fitnesses(parasite_population, all_parasite_results, penalize_size)

        # Get some metrics about how things are going
        host_champ = host_population.get_superchamp()
        parasite_champ = parasite_population.get_superchamp()

        if Constants.is_labeled_non_chess_dataset:
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

        if Constants.smart_pick_puzzles_to_play:
            # Determine which chess puzzles will be used to evaluate the next generation. We do this intelligently by
            # having the species champs from this generation play a lot of games, then selecting (mostly) the most
            # challenging puzzles (for this generation) to use for evaluating the next one.
            print(f'Using generation {generation} species champs to pick puzzles for generation {generation+1}...')
            organisms = []
            organisms.extend(host_population.get_n_diff_species_champs(8))
            organisms.extend(parasite_population.get_n_diff_species_champs(8))
            organisms.extend(np.random.choice(hall_of_fame, 4, replace=False))
            print(f'Organisms being used for picking next puzzles: {organisms}')
            chess_puzzles_inputs = get_puzzles_inputs_for_next_generation(organisms)

        # Selection and breeding
        print(f'Beginning selection and breeding for generation {generation}...')
        seeds_from_host = host_population.get_n_diff_species_champs(3)
        seeds_from_parasite = parasite_population.get_n_diff_species_champs(3)
        for population in [host_population, parasite_population]:
            other_population = parasite_population if population == host_population else host_population
            population_seeds = seeds_from_host if other_population == host_population else seeds_from_parasite
            population.select_and_reproduce(population_seeds)

        # Form species in both populations
        host_population.speciate()
        parasite_population.speciate()

        if generation % 1 == 0:
            save_hall_of_fame(hall_of_fame, generation)
            save_population(host_population, generation+1, is_host=True)
            save_population(parasite_population, generation+1, is_host=False)

        print(f'Processed generation {generation} in {round(time.time() - gen_start_time, 3)}s')
        print("----------------------------")


if __name__ == "__main__":
    main()
