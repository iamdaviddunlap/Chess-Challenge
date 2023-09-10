import numpy as np
import networkx as nx
import random
import warnings
from enum import Enum

from innovation_handler import InnovationHandler
from constants import Constants
from visualize import visualize_genome

random.seed(Constants.random_seed)


class NodeType(Enum):
    INPUT = "input"
    OUTPUT = "output"
    HIDDEN = "hidden"


class ActivationFunction(Enum):
    IDENTITY = "identity"
    SIGMOID = "sigmoid"
    RELU = "relu"
    LEAKY_RELU = "leaky_relu"
    TANH = "tanh"


def sigmoid(x):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        result = 1 / (1 + np.exp(-x))

        if w:
            # Ignore warnings (caused when np.exp(-x) is inf or -inf. This isn't a problem because the sigmoid is just
            # exactly 0.0 or 1.0 in those cases)
            pass

    return result


def relu(x):
    return np.maximum(0, x)


def leaky_relu(x, negative_slope=0.01):
    return np.where(x > 0, x, x * negative_slope)


ACTIVATION_MAPPING = {
    ActivationFunction.IDENTITY: lambda x: x,
    ActivationFunction.SIGMOID: sigmoid,
    ActivationFunction.RELU: relu,
    ActivationFunction.LEAKY_RELU: leaky_relu,
    ActivationFunction.TANH: np.tanh,
}


class Node:
    def __init__(self, node_id, node_type, activation_function, bias):
        self.node_id = node_id
        self.node_type = node_type
        self.activation_function = activation_function
        self.bias = bias

    def __str__(self):
        return f"[{self.node_type.value} {self.node_id} {{{self.bias}}}]"


class Connection:
    def __init__(self, connection_id, weight, input_node, gater_node, output_node):
        self.connection_id = connection_id
        self.weight = weight
        self.input_node = input_node
        self.gater_node = gater_node
        self.output_node = output_node
        self.is_enabled = True

    def __str__(self):
        if self.is_enabled:
            return f"{self.connection_id}: {self.input_node} -> {self.output_node} :: {self.weight}"
        else:
            return f"{self.connection_id}: X| {self.input_node} -> {self.output_node} :: {self.weight} |X"


class Genome:
    def __init__(self, fill_genome=True):
        self.nodes = []
        self.connections = []
        self.activations = np.zeros(len(self.nodes))
        self.device = "cpu"

        if not fill_genome:
            return

        # Adding Input Nodes
        node_num = 0
        for _ in range(Constants.inputs_count):
            self.add_node(NodeType.INPUT, ActivationFunction.IDENTITY, 0.0, node_id=node_num)
            node_num += 1

        # Adding Output Nodes and Connections
        for i in range(Constants.outputs_count):
            bias = round(random.uniform(-1, 1), 3)
            self.add_node(NodeType.OUTPUT, ActivationFunction.IDENTITY, bias, node_id=node_num)
            node_num += 1
            for j in range(len(self.nodes) - (i + 1)):
                cur_in = self.nodes[j]
                cur_out = self.nodes[-1]
                weight = round(random.uniform(-1, 1), 3)
                self.add_connection(weight, cur_in, None, cur_out)

        self.create_phenotype()

    def add_node(self, node_type, activation_function, bias, source_con=None, node_id=None):
        if node_id is None:
            node_id = InnovationHandler().assign_node_id(source=source_con)
        node = Node(node_id, node_type, activation_function, bias)
        self.nodes.append(node)
        return node

    def add_connection(self, weight, input_node, gater_node, output_node, connection_id=None, is_enabled=True):
        if connection_id is None:
            connection_id = InnovationHandler().assign_connection_id(
                connection=(input_node.node_id, output_node.node_id))
        connection = Connection(connection_id, weight, input_node, gater_node, output_node)
        connection.is_enabled = is_enabled
        self.connections.append(connection)
        return connection

    def create_phenotype(self):
        self.determine_activation_order()
        self.node_pheno_to_geno = {pheno: geno for pheno, geno in enumerate(self.activation_order)}
        self.node_geno_to_pheno = {v: k for k, v in self.node_pheno_to_geno.items()}
        self.node_geno_to_nodes_lst_idx = {node.node_id: idx for idx, node in enumerate(self.nodes)}

        # Create connection matrix with 3 dimensions
        self.connection_matrix = np.zeros((len(self.nodes), len(self.nodes), 2))
        self.connection_matrix[:, :, 1] = np.nan

        for connection in self.connections:
            if connection.is_enabled:
                input_node_id = connection.input_node.node_id
                output_node_id = connection.output_node.node_id
                weight = connection.weight

                # Assign the weight to the connection
                self.connection_matrix[
                    self.node_geno_to_pheno[input_node_id], self.node_geno_to_pheno[output_node_id], 0] = weight

                if connection.gater_node:
                    # Assign the gate to the connection
                    self.connection_matrix[
                        self.node_geno_to_pheno[input_node_id], self.node_geno_to_pheno[output_node_id], 1] = \
                        self.node_geno_to_pheno[connection.gater_node.node_id]

        self.inputs_mask = np.array(
            [self.node_geno_to_pheno[node.node_id] for node in self.nodes if node.node_type == NodeType.INPUT])
        self.outputs_mask = np.array(
            [self.node_geno_to_pheno[node.node_id] for node in self.nodes if node.node_type == NodeType.OUTPUT])
        self.gates_mask = ~np.isnan(self.connection_matrix[:, :, 1])
        self.activations = np.zeros(len(self.nodes))

    def determine_activation_order(self):
        # Initialize directed graph
        G = nx.DiGraph()

        # Add nodes to the graph
        for node in self.nodes:
            G.add_node(node.node_id)

        # Add connections as edges in the graph
        for connection in self.connections:
            if connection.is_enabled:
                input_node_id = connection.input_node.node_id
                output_node_id = connection.output_node.node_id
                if input_node_id != output_node_id:  # ignore self-connections for determining activation order
                    G.add_edge(input_node_id, output_node_id)

        # Determine activation order for input nodes
        input_nodes_subgraph = nx.DiGraph()
        input_nodes = [node.node_id for node in self.nodes if node.node_type == NodeType.INPUT]
        for input_node_id in input_nodes:
            for successor in G.successors(input_node_id):
                if successor in input_nodes:
                    input_nodes_subgraph.add_edge(input_node_id, successor)
        try:
            input_activation_order = list(nx.topological_sort(input_nodes_subgraph))
        except Exception as e:
            # There are cycles in the input so there's no ideal order. Just activate them in node_id order
            input_activation_order = input_nodes

        # Extend activation order with remaining nodes
        activation_order = input_activation_order[:]
        remaining_nodes = set(G.nodes) - set(input_activation_order)
        loop_counter = 0
        least_preds = 100000
        least_preds_node = None
        while remaining_nodes:
            loop_counter += 1
            if loop_counter >= (len(self.nodes) * 100):
                # We're in an infinite loop! We must resolve it
                remaining_input_nodes = set(input_nodes) - set(activation_order)
                if len(remaining_input_nodes) > 0:
                    # We have input nodes not yet in the activation_order
                    num_preds = {node_id: len(list(G.predecessors(node_id))) for node_id in remaining_input_nodes}
                    node_with_least_predecessors = min(num_preds, key=num_preds.get)
                    # Add it to the activation_order
                    activation_order.append(node_with_least_predecessors)
                    remaining_nodes.remove(node_with_least_predecessors)
                    least_preds = 100000
                    least_preds_node = None
                    loop_counter = 0
                else:
                    if least_preds_node is None: raise Exception('Stuck in loop, and haven\'t yet found a suitable node to add')
                    activation_order.append(least_preds_node)
                    remaining_nodes.remove(least_preds_node)
                    least_preds = 100000
                    least_preds_node = None
                    loop_counter = 0
            for node_id in list(remaining_nodes):
                predecessors = [p for p in G.predecessors(node_id) if p != node_id]
                if len(predecessors) < least_preds:
                    least_preds = len(predecessors)
                    least_preds_node = node_id
                if all(predecessor in activation_order for predecessor in predecessors):
                    activation_order.append(node_id)
                    remaining_nodes.remove(node_id)
                    loop_counter = 0
                    least_preds = 100000
                    least_preds_node = None

        self.activation_order = activation_order

    def genetic_difference(self, genome2):
        genome1_innovation_numbers = set(connection.connection_id for connection in self.connections)
        genome2_innovation_numbers = set(connection.connection_id for connection in genome2.connections)

        smaller_max_innovation_number = min(max(genome1_innovation_numbers), max(genome2_innovation_numbers))

        matching_innovation_numbers = genome1_innovation_numbers & genome2_innovation_numbers

        disjoint_count = sum(
            1 for n in genome1_innovation_numbers - matching_innovation_numbers if n <= smaller_max_innovation_number) + \
                         sum(1 for n in genome2_innovation_numbers - matching_innovation_numbers if
                             n <= smaller_max_innovation_number)

        excess_count = sum(
            1 for n in genome1_innovation_numbers - matching_innovation_numbers if n > smaller_max_innovation_number) + \
                       sum(1 for n in genome2_innovation_numbers - matching_innovation_numbers if
                           n > smaller_max_innovation_number)

        weight_difference_sum = 0
        gater_difference_count = 0
        total_gates = 0
        for innovation_number in matching_innovation_numbers:
            genome1_conn = [connection for connection in self.connections if connection.connection_id == innovation_number][0]
            genome2_conn = [connection for connection in genome2.connections if connection.connection_id == innovation_number][0]
            weight_difference_sum += abs(genome1_conn.weight - genome2_conn.weight)
            if (genome1_conn.gater_node is not None) or (genome2_conn.gater_node is not None):
                total_gates += 1
                genome1_gater_node_id = genome1_conn.gater_node.node_id if genome1_conn.gater_node else None
                genome2_gater_node_id = genome2_conn.gater_node.node_id if genome2_conn.gater_node else None
                if genome1_gater_node_id != genome2_gater_node_id:
                    gater_difference_count += 1

        average_weight_difference = weight_difference_sum / len(matching_innovation_numbers) \
            if matching_innovation_numbers else 0

        scaled_gates_difference = (gater_difference_count / total_gates) if total_gates > 0 else 0

        shared_node_ids = [node.node_id for node in self.nodes if any(node2.node_id == node.node_id for node2 in genome2.nodes)]
        bias_difference_sum = 0
        for shared_node_id in shared_node_ids :
            genome1_node = [node for node in self.nodes if node.node_id == shared_node_id][0]
            genome2_node = [node for node in genome2.nodes if node.node_id == shared_node_id][0]
            bias_difference_sum += abs(genome1_node.bias - genome2_node.bias)

        average_bias_difference = bias_difference_sum / len(shared_node_ids) if shared_node_ids else 0
        average_combined_difference = (average_weight_difference + average_bias_difference) / 2.0

        n = max(len(self.connections), len(genome2.connections))

        genetic_difference = ((Constants.excess_coeff * excess_count) / n) + \
                             ((Constants.disjoint_coeff * disjoint_count) / n) + \
                             (Constants.weight_coeff * average_combined_difference) + \
                             (Constants.gates_coeff * scaled_gates_difference)

        return genetic_difference

    def activate(self, input_activations, max_iterations=5, simulate_only=False):
        if simulate_only:
            old_activations = np.copy(self.activations)

        try:
            self.activations[self.inputs_mask] = input_activations
        except ValueError as e:
            raise Exception(f'Inputs of length {len(input_activations)} don\'t match network with input size '
                            f'{len(self.inputs_mask)} :: {e}')

        # Iterate Through Time Steps
        for i in range(max_iterations):
            new_activations = np.copy(self.activations)
            for node_id in self.activation_order:
                phen_id = self.node_geno_to_pheno[node_id]
                node = self.nodes[self.node_geno_to_nodes_lst_idx[node_id]]
                gates_mask = self.gates_mask[:, phen_id]
                incoming_activations = self.connection_matrix[:, phen_id, 0] * new_activations
                incoming_activations[gates_mask] *= new_activations[
                    self.connection_matrix[:, phen_id, 1][gates_mask].astype(np.longlong)]
                incoming_activation = np.sum(incoming_activations)
                new_activation = new_activations[phen_id] + incoming_activation + node.bias
                new_activation = np.maximum(new_activation, -1e12)
                new_activation = np.minimum(new_activation, 1e12)
                # Apply activation function
                new_activations[phen_id] = ACTIVATION_MAPPING[node.activation_function](new_activation)

            # Update activations
            self.activations = new_activations

        outputs_array = self.activations[self.outputs_mask]

        if simulate_only:
            self.activations = old_activations

        return outputs_array

    def reset_state(self):
        self.activations = np.zeros(len(self.nodes))

    def clone(self):
        # Create a new Genome object without filling it
        cloned_genome = Genome(fill_genome=False)

        # Mapping to keep track of the new nodes corresponding to the old nodes
        node_mapping = {}

        # Clone nodes
        for node in self.nodes:
            cloned_node = cloned_genome.add_node(
                node_type=node.node_type,
                activation_function=node.activation_function,
                bias=node.bias,
                node_id=node.node_id)
            node_mapping[node.node_id] = cloned_node

        # Clone connections
        for connection in self.connections:
            input_node = node_mapping[connection.input_node.node_id]
            output_node = node_mapping[connection.output_node.node_id]
            gater_node = node_mapping[connection.gater_node.node_id] if connection.gater_node else None
            cloned_connection = cloned_genome.add_connection(
                weight=connection.weight,
                input_node=input_node,
                gater_node=gater_node,
                output_node=output_node)
            cloned_connection.connection_id = connection.connection_id
            cloned_connection.is_enabled = connection.is_enabled

        # Reconstruct the phenotype
        cloned_genome.create_phenotype()

        return cloned_genome

    def to_device(self, device):
        pass
