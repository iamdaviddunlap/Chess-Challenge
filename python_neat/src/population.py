import random
import statistics

from constants import Constants
from genome import Genome
from organism import Organism
from mutation_handler import Mutation
from innovation_handler import InnovationHandler
from visualize import visualize_genome

random.seed(Constants.random_seed)


class Population:
    def __init__(self):
        self._cur_species_id = 0
        self._species_compat_thresh = Constants.species_compat_thresh_initial
        self.organisms = []
        self.species_reps = []
        # self.species_ids = []
        self.species_ids = [1, 2, 3, 4]  # TODO init as empty

        for i in range(Constants.population_size):
            genome = Genome()
            organism = Organism(genome)
            # TODO don't mutate so much
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            Mutation.mutate_genome(organism.genome)
            self.organisms.append(organism)
        self.speciate()

    def select_challengers(self, hall_of_fame):
        challengers = []
        challenger_ids = []
        species_champions = [self.get_species_top_n(species_id, 1)[0] for species_id in self.species_ids]

        species_champions.sort(key=lambda o: o.fitness, reverse=True)
        challengers.extend(species_champions[:Constants.num_champion_parasites])
        challenger_ids.extend([o.organism_id for o in species_champions[:Constants.num_champion_parasites]])

        # Add challengers from the Hall of Fame
        for i in range(min(Constants.num_hall_of_fame_parasites, len(hall_of_fame))):
            hof_challenger = hall_of_fame[random.randint(0, len(hall_of_fame) - 1)]
            challengers.append(hof_challenger)
            challenger_ids.append(hof_challenger.organism_id)

        # If we don't have enough challengers, pick random organisms as challengers until we have enough
        while len(challengers) < Constants.num_hall_of_fame_parasites + Constants.num_champion_parasites:
            x = 1
            random_organism = self.organisms[random.randint(0, len(self.organisms) - 1)]
            if random_organism.organism_id in challenger_ids:
                continue
            challengers.append(random_organism)
            challenger_ids.append(random_organism.organism_id)

        return challengers

    def get_species_top_n(self, species_id, num_champs):
        species_organisms = [o for o in self.organisms if o.species_id == species_id]
        sorted_species_organisms = sorted(species_organisms, key=lambda o: o.fitness, reverse=True)
        species_champs = sorted_species_organisms[:num_champs]
        return species_champs

    def get_superchamp(self):
        return max(self.organisms, key=lambda o: o.fitness)

    def get_n_diff_species_champs(self, num_champs):
        species_champs = [self.get_species_top_n(sid, 1)[0] for sid in self.species_ids]
        top_champs = sorted(species_champs, key=lambda o: o.fitness, reverse=True)[:num_champs]
        return top_champs

    def eliminate_species_weakest(self, species_id):
        # Filter organisms by species_id and then sort by fitness in descending order
        species_organisms = [o for o in self.organisms if o.species_id == species_id]
        species_organisms = sorted(species_organisms, key=lambda o: o.fitness, reverse=True)

        # Determine the cut-off index
        cutoff_index = int(len(species_organisms) * Constants.species_elite_percentage)

        # If the species has two or more organisms, keep at least 2, otherwise keep the top %
        if len(species_organisms) >= 2:
            cutoff_index = max(cutoff_index, 2)
        elif len(species_organisms) == 1:
            cutoff_index = 1

        # Iterate from the cutoff index to the end, removing each organism from the Organisms list
        for organism in species_organisms[cutoff_index:]:
            self.organisms.remove(organism)

    def select_and_reproduce(self, other_population_seeds):
        new_organisms = []

        # Dictionary to hold average fitness per species
        species_average_fitness = {}
        total_avg_fitness = 0

        # Clear species reps
        self.species_reps.clear()

        # First pass over species list. Eliminate the weakest, find the average fitness, save the species champ, and
        # reassign the species rep as a random member of the species
        species_champs = []
        for species_id in self.species_ids:
            self.eliminate_species_weakest(species_id)
            species_organisms = [o for o in self.organisms if o.species_id == species_id]
            avg_fitness = sum(o.fitness for o in species_organisms) / len(species_organisms)
            species_champ = max(species_organisms, key=lambda o: o.fitness)
            species_rep = species_organisms[random.randint(0, len(species_organisms) - 1)]
            self.species_reps.append(species_rep)
            species_champs.append(species_champ)
            species_average_fitness[species_id] = avg_fitness
            total_avg_fitness += avg_fitness

        # Add some completely random children
        num_random_children = 5
        max_mutations = 20
        for i in range(num_random_children):
            genome = Genome()
            organism = Organism(genome)
            num_mutations = random.randint(2, max_mutations)
            for j in range(num_mutations):
                Mutation.mutate_genome(organism.genome)
            new_organisms.append(organism)

        # Find the "superchamp"
        super_champ = self.get_superchamp()

        # Create special clones from super champ
        pop_fitnesses = [o.fitness for o in self.organisms]
        super_champ_z_score = (super_champ.fitness - statistics.mean(pop_fitnesses)) / statistics.stdev(pop_fitnesses)
        print(f"super_champ_z_score: {super_champ_z_score}")
        if super_champ_z_score >= Constants.killer_superchamp_z_score_req:
            super_champ_offspring = int(Constants.population_size * Constants.killer_superchamp_percent)
        else:
            super_champ_offspring = Constants.superchamp_offspring
        for i in range(super_champ_offspring):
            new_superchamp_genome = super_champ.genome.clone()
            Mutation.mutate_weights(new_superchamp_genome, weight_perturb_value_mod=0.4)
            new_superchamp_child = Organism(new_superchamp_genome)
            new_organisms.append(new_superchamp_child)

        # Directly clone the species champions
        for champ in species_champs:
            cloned_genome = champ.genome.clone()
            new_organism = Organism(cloned_genome)
            new_organisms.append(new_organism)

        # Reproduction phase
        remaining = Constants.population_size - len(new_organisms)
        for species_id in self.species_ids:
            species_new_organisms = []
            species_organisms = [o for o in self.organisms if o.species_id == species_id]
            average_fitness = species_average_fitness[species_id]
            num_species_offspring = max(int((average_fitness / total_avg_fitness) * remaining), 1)
            for i in range(num_species_offspring):
                if len(species_organisms) > 1 and random.random() > Constants.mutate_only_prob:
                    # Sexually reproduce
                    offspring = None
                    if len(self.species_ids) > 1 and random.random() < Constants.cross_species_mating_prob:
                        # Do cross-species mating
                        other_species_id = species_id
                        while other_species_id == species_id:
                            other_species_id = self.species_ids[random.randint(0, len(self.species_ids) - 1)]
                        champ_organism = species_champs[self.species_ids.index(other_species_id)]
                        index = random.randint(0, len(species_organisms) - 1)
                        offspring = species_organisms[index].reproduce(champ_organism)
                    elif random.random() < Constants.cross_population_mating_prob:
                        other_pop_organism = other_population_seeds[random.randint(0, len(other_population_seeds) - 1)]
                        index = random.randint(0, len(species_organisms) - 1)
                        offspring = species_organisms[index].reproduce(other_pop_organism)
                    else:
                        index1 = index2 = -1
                        while index1 == index2:
                            index1 = random.randint(0, len(species_organisms) - 1)
                            index2 = random.randint(0, len(species_organisms) - 1)
                        offspring = species_organisms[index1].reproduce(species_organisms[index2])
                    # Decide whether or not to mutate baby
                    if random.random() > Constants.mate_only_prob:
                        Mutation.mutate_genome(offspring.genome)
                    species_new_organisms.append(offspring)
                else:
                    # Asexually reproduce
                    index = random.randint(0, len(species_organisms) - 1)
                    offspring = species_organisms[index].reproduce()
                    species_new_organisms.append(offspring)

            new_organisms.extend(species_new_organisms)

        # Fill in the rest of the population by having the top organisms asexually reproduce
        remaining = Constants.population_size - len(new_organisms)
        asexual_parents = sorted(self.organisms, key=lambda o: o.fitness, reverse=True)[:remaining]
        for parent in asexual_parents:
            offspring = parent.reproduce()
            new_organisms.append(offspring)

        # Cut off organisms if we created too many
        new_organisms = new_organisms[:Constants.population_size]

        # Replace the old population with the new one
        self.organisms.clear()
        self.organisms.extend(new_organisms)

        # Clear unique innovation maps
        InnovationHandler().connection_id_mapping.clear()
        InnovationHandler().node_id_mapping.clear()

    def speciate(self):
        for organism in self.organisms:
            found_species = False
            for species_rep in self.species_reps:
                gene_difference = organism.genome.genetic_difference(species_rep.genome)
                if gene_difference <= self._species_compat_thresh:
                    organism.species_id = species_rep.species_id
                    found_species = True
                    break

            if not found_species:
                new_id = self.get_next_species_id()
                organism.species_id = new_id
                self.species_reps.append(organism)

        # Clear the species_ids list
        self.species_ids.clear()

        # Assign new unique species IDs by going through the Organisms list
        unique_species_ids = list(set(organism.species_id for organism in self.organisms))

        # Replace the species_ids list with the new unique species IDs
        self.species_ids.extend(unique_species_ids)

        # Remove organisms from species_reps that are no longer representatives of any species
        self.species_reps[:] = [rep for rep in self.species_reps if rep.species_id in self.species_ids]

        # Adjust SpeciesCompatThresh to target SpeciesCountTarget number of species
        if len(self.species_ids) < Constants.species_count_target:
            self._species_compat_thresh -= Constants.species_compat_modifier
        elif len(self.species_ids) > Constants.species_count_target:
            self._species_compat_thresh += Constants.species_compat_modifier

        # Ensure the SpeciesCompatThresh can't get too low
        if self._species_compat_thresh < Constants.species_compat_modifier:
            self._species_compat_thresh = Constants.species_compat_modifier

    def get_next_species_id(self):
        cur_id = self._cur_species_id
        self._cur_species_id += 1
        return cur_id