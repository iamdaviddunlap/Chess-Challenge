import torch
import torch.nn.functional as F
import networkx as nx
import random
from enum import Enum

from innovation_handler import InnovationHandler
from constants import Constants

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


ACTIVATION_MAPPING = {
    ActivationFunction.IDENTITY: lambda x: x,
    ActivationFunction.SIGMOID: F.sigmoid,
    ActivationFunction.RELU: F.relu,
    ActivationFunction.LEAKY_RELU: F.leaky_relu,
    ActivationFunction.TANH: F.tanh,
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
        self.activations = torch.zeros(len(self.nodes))

        if not fill_genome:
            return

        # Adding Input Nodes
        node_num = 0
        for _ in range(Constants.inputs_count):
            self.add_node(NodeType.INPUT, lambda x: x, 0.0, node_id=node_num)
            node_num += 1

        # Adding Output Nodes and Connections
        for i in range(Constants.outputs_count):
            bias = round(random.uniform(-1, 1), 3)
            self.add_node(NodeType.OUTPUT, lambda x: x, bias, node_id=node_num)
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

        # Create connection matrix with 3 dimensions
        self.connection_matrix = torch.zeros((len(self.nodes), len(self.nodes), 2))
        self.connection_matrix[:, :, 1] = float('nan')

        for connection in self.connections:
            if connection.is_enabled:
                input_node_id = connection.input_node.node_id
                output_node_id = connection.output_node.node_id
                weight = connection.weight

                # Assign the weight to the connection (using the 0th index in the third dimension)
                self.connection_matrix[
                    self.node_geno_to_pheno[input_node_id], self.node_geno_to_pheno[output_node_id], 0] = weight

                if connection.gater_node:
                    # Assign the gate to the connection (using the 1st index in the third dimension)
                    self.connection_matrix[
                        self.node_geno_to_pheno[input_node_id], self.node_geno_to_pheno[output_node_id], 1] = \
                        self.node_geno_to_pheno[connection.gater_node.node_id]

        # Initialize activations
        self.activations = torch.zeros(len(self.nodes))

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
                G.add_edge(input_node_id, output_node_id)

        # Determine activation order for input nodes
        input_nodes_subgraph = nx.DiGraph()
        input_nodes = [node.node_id for node in self.nodes if node.node_type == NodeType.INPUT]
        for input_node_id in input_nodes:
            for successor in G.successors(input_node_id):
                if successor in input_nodes:
                    input_nodes_subgraph.add_edge(input_node_id, successor)
        input_activation_order = list(nx.topological_sort(input_nodes_subgraph))

        # Extend activation order with remaining nodes
        activation_order = input_activation_order[:]
        remaining_nodes = set(G.nodes) - set(input_activation_order)
        loop_counter = 0
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
                    loop_counter = 0
                else:
                    print('determine_activation_order stuck in an unresolved infinite loop!')
            for node_id in list(remaining_nodes):
                predecessors = [p for p in G.predecessors(node_id) if p != node_id]
                if all(predecessor in activation_order for predecessor in predecessors):
                    activation_order.append(node_id)
                    remaining_nodes.remove(node_id)

        self.activation_order = activation_order

    def activate(self, input_activations, max_iterations=10, simulate_only=False):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Move tensors to the GPU
        self.activations = self.activations.to(device)
        self.connection_matrix = self.connection_matrix.to(device)
        input_activations_tensor = torch.tensor(input_activations).to(device)
        old_activations = self.activations.clone()

        # Update activations for input nodes
        inputs_pheno_ids = [self.node_geno_to_pheno[node.node_id] for node in self.nodes if
                            node.node_type == NodeType.INPUT]
        if len(input_activations) != len(inputs_pheno_ids):
            raise Exception(f'Inputs of length {len(input_activations)} don\'t match network with input size '
                            f'{len(inputs_pheno_ids)}')
        self.activations[inputs_pheno_ids] = input_activations_tensor

        # Iterate Through Time Steps
        for _ in range(max_iterations):
            new_activations = self.activations.clone()
            for node_id in self.activation_order:
                phen_id = self.node_geno_to_pheno[node_id]
                node = self.nodes[phen_id]
                gates_mask = ~torch.isnan(self.connection_matrix[:, phen_id, 1])
                incoming_activations = self.connection_matrix[:, phen_id, 0] * new_activations
                incoming_activations[gates_mask] *= new_activations[
                    self.connection_matrix[:, phen_id, 1][gates_mask].long()]
                incoming_activation = torch.sum(incoming_activations)
                new_activation = new_activations[phen_id] + incoming_activation + node.bias
                # Apply activation function
                new_activations[phen_id] = node.activation_function(new_activation)

            # Update activations
            self.activations = new_activations

        output_pheno_ids = [self.node_geno_to_pheno[x.node_id] for x in self.nodes if x.node_type == NodeType.OUTPUT]
        outputs_tensor = self.activations[output_pheno_ids]

        if simulate_only:
            self.activations = old_activations

        return outputs_tensor

    def reset_state(self):
        self.activations = torch.zeros(len(self.nodes))

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
