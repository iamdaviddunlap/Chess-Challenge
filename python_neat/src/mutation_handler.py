import random

from constants import Constants
from visualize import visualize_genome

random.seed(Constants.random_seed)


class Mutation:

    @staticmethod
    def mutate_genome(genome):
        if random.random() < Constants.add_node_prob:
            Mutation.add_node_mutation(genome)
        elif random.random() < Constants.add_connection_prob:
            Mutation.add_connection_mutation(genome)
        else:
            removable_connections = None
            if random.random() < Constants.mutate_weights_prob:
                Mutation.mutate_weights(genome)
            if random.random() < Constants.mutate_biases_prob:
                Mutation.mutate_biases(genome)
            if random.random() < Constants.mutate_toggle_enable_prob:
                removable_connections = removable_connections or Mutation.find_cons_for_removal(genome)
                Mutation.mutate_toggle_enable(genome, removable_connections)
            if random.random() < Constants.mutate_reenable_prob:
                Mutation.mutate_gene_reenable(genome)
            if random.random() < Constants.mutate_remove_connection_prob:
                removable_connections = removable_connections or Mutation.find_cons_for_removal(genome)
                Mutation.mutate_remove_connection(genome, removable_connections)
            if random.random() < Constants.mutate_remove_node_prob:
                Mutation.mutate_remove_node(genome)
            if random.random() < Constants.mutate_add_gate_prob:
                Mutation.mutate_add_gate(genome)
            if random.random() < Constants.mutate_activation_function_prob:
                Mutation.mutate_activation_function(genome)

    @staticmethod
    def mutate_weights(genome, weight_perturb_value_mod=1.0):
        for connection in genome.connections:
            if random.random() < Constants.weight_perturb_chance:
                perturb_amount = random.uniform(-1, 1) * Constants.weight_perturb_value * weight_perturb_value_mod
                new_weight = connection.weight + perturb_amount
                connection.weight = min(max(new_weight, Constants.min_val), Constants.max_val)
                connection.weight = round(connection.weight, 3)
        genome.create_phenotype()

    @staticmethod
    def mutate_biases(genome):
        for node in genome.nodes:
            if node.node_type.value == "input":
                continue
            if random.random() < Constants.bias_perturb_chance:
                perturb_amount = random.uniform(-1, 1) * Constants.bias_perturb_value
                new_bias = node.bias + perturb_amount
                node.bias = min(max(new_bias, Constants.min_val), Constants.max_val)
                node.bias = round(node.bias, 3)
        genome.create_phenotype()

    @staticmethod
    def mutate_add_gate(genome):
        # Select target connection
        target_connection = random.choice(genome.connections)
        target_node = random.choice(genome.nodes)
        while (target_node.node_id == target_connection.input_node.node_id) or \
                (target_node.node_id == target_connection.output_node.node_id):
            target_node = random.choice(genome.nodes)
        target_connection.gater_node = target_node
        genome.create_phenotype()

    @staticmethod
    def mutate_activation_function(genome):
        from genome import ActivationFunction, ACTIVATION_MAPPING
        target_node = random.choice(genome.nodes)
        while target_node.node_type.value == "input":
            target_node = random.choice(genome.nodes)
        cur_func = target_node.activation_function
        new_func = cur_func
        while new_func == cur_func:
            new_func = ACTIVATION_MAPPING[random.choice(list(ActivationFunction))]
        target_node.activation_function = new_func

    @staticmethod
    def mutate_toggle_enable(genome, eligible_connections):
        eligible_connections += [c for c in genome.connections if not c.is_enabled and c not in eligible_connections]
        if eligible_connections:
            connection = random.choice(eligible_connections)
            connection.is_enabled = not connection.is_enabled
            genome.create_phenotype()

    @staticmethod
    def mutate_gene_reenable(genome):
        disabled_connections = [conn for conn in genome.connections if not conn.is_enabled]
        if disabled_connections:
            connection_to_reenable = random.choice(disabled_connections)
            connection_to_reenable.is_enabled = True
            genome.create_phenotype()

    @staticmethod
    def mutate_remove_connection(genome, eligible_connections):
        if eligible_connections:
            connection_to_remove = random.choice(eligible_connections)
            genome.connections.remove(connection_to_remove)
            genome.create_phenotype()

    @staticmethod
    def mutate_remove_node(genome):
        if not any(node.node_type.value == "hidden" for node in genome.nodes):
            return False  # No hidden nodes to remove

        # Select a random node of type hidden for removal
        node_to_remove = random.choice([node for node in genome.nodes if node.node_type.value == "hidden"])

        gaters = []
        source_nodes = []
        target_nodes = []

        # Find all source nodes and gaters for incoming connections
        for connection in genome.connections:
            if connection.output_node == node_to_remove and connection.input_node != node_to_remove:
                source_nodes.append(connection.input_node)
                if connection.gater_node is not None:
                    gaters.append(connection.gater_node)

        # Find all target nodes and gaters for outgoing connections
        for connection in genome.connections:
            if connection.input_node == node_to_remove and connection.output_node != node_to_remove:
                target_nodes.append(connection.output_node)
                if connection.gater_node is not None:
                    gaters.append(connection.gater_node)

        # Create new connections between each source and target, if not already connected
        new_connections = []
        for source in source_nodes:
            for target in target_nodes:
                existing_connections = [conn for conn in genome.connections if conn.input_node == source and conn.output_node == target]
                if not any(existing_connections):
                    weight = round(random.uniform(-1, 1), 3)
                    connection = genome.add_connection(weight, source, None, target)
                    new_connections.append(connection)
                else:
                    for conn in existing_connections: conn.is_enabled = True
                    new_connections.extend(existing_connections)

        # Assign each gater to a new connection, until no connections are left to gate
        for gater in gaters:
            if len(new_connections) == 0:
                break

            random_connection = random.choice(new_connections)
            random_connection.gater_node = gater
            new_connections.remove(random_connection)

        # Set the gater value of every connection that is gated by the node being removed to None
        for connection in genome.connections:
            if connection.gater_node == node_to_remove:
                connection.gater_node = None

        # Remove connections that previously went to/from the node to be removed
        connections_to_remove = [conn for conn in genome.connections if
                                 conn.input_node == node_to_remove or conn.output_node == node_to_remove]
        for conn in connections_to_remove:
            genome.connections.remove(conn)

        # Remove the node from the genome
        genome.nodes.remove(node_to_remove)
        genome.create_phenotype()
        return True

    @staticmethod
    def find_cons_for_removal(genome):
        source_count = {node: 0 for node in genome.nodes}
        target_count = {node: 0 for node in genome.nodes}

        for conn in genome.connections:
            if conn.is_enabled and conn.input_node.node_id != conn.output_node.node_id:
                source_count[conn.input_node] += 1
                target_count[conn.output_node] += 1

        return [conn for conn in genome.connections if
                source_count[conn.input_node] > 1 and
                (target_count[conn.output_node] > 1 or conn.output_node.node_type.value == "input")]

    @staticmethod
    def add_node_mutation(genome):
        from genome import NodeType, ActivationFunction, ACTIVATION_MAPPING

        num_loops = 0
        max_loops = 1000
        while True:
            num_loops += 1
            if num_loops >= max_loops:
                return False

            # Pick a random connection to split
            old_connection = random.choice(genome.connections)

            # Don't split a disabled connection, a self-connection, or a recurrent connection
            if not old_connection.is_enabled or \
                    (genome.node_geno_to_pheno[old_connection.input_node.node_id] >=
                     genome.node_geno_to_pheno[old_connection.output_node.node_id]):
                continue

            # Disable the old connection
            old_connection.is_enabled = False

            # Create new node
            bias = round(random.uniform(-1, 1), 3)
            activation_function = ACTIVATION_MAPPING[random.choice(list(ActivationFunction))]
            new_node = genome.add_node(NodeType.HIDDEN, activation_function, bias, source_con=old_connection.connection_id)

            genome.add_connection(1, old_connection.input_node, None, new_node)
            genome.add_connection(old_connection.weight, new_node, None, old_connection.output_node)

            genome.create_phenotype()
            return True

    @staticmethod
    def add_connection_mutation(genome):
        num_loops = -1
        max_loops = 1000
        while True:
            num_loops += 1
            if num_loops >= max_loops:
                return False

            # Pick two random nodes
            node1 = random.choice(genome.nodes)
            node2 = random.choice(genome.nodes)

            # Uncomment this to restrict connecting nodes that are on the same depth
            # if node1.depth == node2.depth:
            #     continue

            # Check if these two nodes are already connected
            are_connected = False
            for conn in genome.connections:
                if ((conn.input_node.node_id == node1.node_id and conn.output_node.node_id == node2.node_id) or
                        (conn.input_node.node_id == node2.node_id and conn.output_node.node_id == node1.node_id)):
                    are_connected = True
                    break

            if not are_connected:
                # Add the new connection to the genome
                weight = round(random.uniform(-1, 1), 3)
                # To disable recurrent connections I'd need to do some sort of check to find if node1 or node2 has a
                # shallower depth
                genome.add_connection(weight, node1, None, node2)
            else:
                continue

            genome.create_phenotype()
            return True
