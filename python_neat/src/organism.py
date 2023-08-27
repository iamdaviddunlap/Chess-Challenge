import random

from genome import Genome, Node
from constants import Constants
from mutation_handler import Mutation
from innovation_handler import InnovationHandler

random.seed(Constants.random_seed)


class Organism:
    def __init__(self, genome, organism_id=None):
        self.genome = genome
        self.fitness = -1
        self.species_id = -1
        if organism_id is not None:
            self.organism_id = organism_id
        else:
            self.organism_id = InnovationHandler().get_next_organism_id()

    def reproduce(self, co_parent=None):
        if co_parent is None:
            # Asexual reproduction
            offspring_genome = self.genome.clone()
            Mutation.mutate_genome(offspring_genome)
            new_organism = Organism(offspring_genome)
            new_organism.fitness = self.fitness
            return new_organism

        # Sexual reproduction
        if random.random() < Constants.mate_avg_genes_prob:
            # Pass selection function that averages two genes
            selection_func = lambda p1, p2: round((p1 + p2) / 2.0, 3)
        else:
            # Pass selection function that selects either one or the other gene
            selection_func = lambda p1, p2: p1 if random.random() < 0.5 else p2

        offspring_genome = self._mate_multipoint(random, co_parent, selection_func)
        more_fit_parent = self if self.fitness > co_parent.fitness else co_parent
        new_organism = Organism(offspring_genome)
        new_organism.fitness = more_fit_parent.fitness
        return new_organism

    def _mate_multipoint(self, random, co_parent, selection_func):
        offspring_genome = Genome(fill_genome=False)

        # Determine the more fit parent
        more_fit_parent = self if self.fitness > co_parent.fitness else co_parent
        this_is_more_fit = more_fit_parent == self

        # Handle nodes. Only take disjoint/excess nodes from the fitter parent
        for node_id in [n.node_id for n in more_fit_parent.genome.nodes]:
            parent_node1 = \
            ([n for n in (self if this_is_more_fit else co_parent).genome.nodes if n.node_id == node_id] or [None])[0]
            parent_node2 = \
            ([n for n in (co_parent if this_is_more_fit else self).genome.nodes if n.node_id == node_id] or [None])[0]

            if parent_node1 and parent_node2:  # Matching nodes
                bias = selection_func(parent_node1.bias, parent_node2.bias)
                new_node = Node(node_id, parent_node1.node_type, parent_node1.activation_function, bias)
            else:  # Disjoint or excess node from fitter parent
                new_node = parent_node1 or parent_node2

            offspring_genome.add_node(new_node.node_type, new_node.activation_function, new_node.bias,
                                      node_id=new_node.node_id)

        # Handle matching connections
        genome2_innovation_numbers = [c.connection_id for c in co_parent.genome.connections]
        matching_connections = [c for c in self.genome.connections if c.connection_id in genome2_innovation_numbers]

        for matching_connection in matching_connections:
            co_parent_conn = \
            [c for c in co_parent.genome.connections if c.connection_id == matching_connection.connection_id][0]
            in_node = [n for n in offspring_genome.nodes if n.node_id == matching_connection.input_node.node_id][0]
            out_node = [n for n in offspring_genome.nodes if n.node_id == matching_connection.output_node.node_id][0]
            weight_to_use = selection_func(matching_connection.weight, co_parent_conn.weight)

            # Determine whether to inherit disabled status for gene
            # 75% chance it stays disabled if disabled in at least 1 parent
            do_enable = matching_connection.is_enabled and co_parent_conn.is_enabled
            if not do_enable and random.random() > Constants.inherit_disable_chance:
                do_enable = True

            # Determine inheriting of gater node
            parent1_gater_node = matching_connection.gater_node
            parent2_gater_node = co_parent_conn.gater_node

            # If both parents have null gater_nodes, offspring's gater_node should be null
            if parent1_gater_node is None and parent2_gater_node is None:
                gater_node_to_use = None
            # If one parent has null and the other has non-null, use the non-null one IF a node with that id exists in the offspring_genome
            elif (parent1_gater_node is None) != (parent2_gater_node is None):
                non_null_gater_node = parent1_gater_node or parent2_gater_node
                matching_offspring_node = [n for n in offspring_genome.nodes if n.node_id == non_null_gater_node.node_id]
                gater_node_to_use = matching_offspring_node[0] if bool(matching_offspring_node) else None
            # If both parents have non-null gater_nodes, we should check if a node with either of the ids exist in the offspring_genome
            else:
                offspring_gater_node1 = [n for n in offspring_genome.nodes if n.node_id == parent1_gater_node.node_id]
                offspring_gater_node2 = [n for n in offspring_genome.nodes if n.node_id == parent2_gater_node.node_id]

                # If only 1 exists, that one should be assigned
                if bool(offspring_gater_node1) != bool(offspring_gater_node2):
                    gater_node_to_use = offspring_gater_node1[0] if offspring_gater_node1 else offspring_gater_node2[0]
                # If they both exist, one should be chosen at random
                else:
                    gater_node_to_use = random.choice(offspring_gater_node1 + offspring_gater_node2)

            # Now, add the connection with the determined gater_node
            offspring_genome.add_connection(weight_to_use, in_node, gater_node_to_use, out_node, is_enabled=do_enable)

        # Add any disjoint/excess connections from the fitter parent
        for connection in more_fit_parent.genome.connections:
            if all(c.connection_id != connection.connection_id for c in matching_connections):
                in_node = [n for n in offspring_genome.nodes if n.node_id == connection.input_node.node_id][0]
                out_node = [n for n in offspring_genome.nodes if n.node_id == connection.output_node.node_id][0]
                offspring_genome.add_connection(connection.weight, in_node, connection.gater_node, out_node)

        offspring_genome.create_phenotype()
        return offspring_genome

    def clone(self):
        clone_organism = Organism(self.genome.clone(), organism_id=self.organism_id)
        clone_organism.fitness = self.fitness
        clone_organism.species_id = self.species_id
        return clone_organism

    def to_device(self, device):
        self.genome.to_device(device)

    def __str__(self):
        return f"Organism #{self.organism_id}"
