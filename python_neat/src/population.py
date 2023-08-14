import random
import itertools

from constants import Constants
from genome import Genome
from organism import Organism
from mutation_handler import Mutation
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
        # TODO
        pass

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