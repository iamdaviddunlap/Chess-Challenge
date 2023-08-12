from src.innovation_handler import InnovationHandler
import torch
import torch.nn.functional as F
import networkx as nx


class Node:
    def __init__(self, node_id, node_type, activation_function, bias):
        self.node_id = node_id
        self.node_type = node_type
        self.activation_function = activation_function
        self.bias = bias

    def __str__(self):
        return f"[{self.node_type} {self.node_id} {{{self.bias}}}]"


class Connection:
    def __init__(self, connection_id, weight, input_node, gater_node, output_node):
        self.connection_id = connection_id
        self.weight = weight
        self.input_node = input_node
        self.gater_node = gater_node
        self.output_node = output_node


class Genome:
    def __init__(self):
        self.nodes = []
        self.connections = []
        self.activations = torch.zeros(len(self.nodes))
        self.innovation_handler = InnovationHandler()

    def add_node(self, node_type, activation_function, bias, source_con=None, node_id=None):
        if node_id is None:
            node_id = self.innovation_handler.assign_node_id(source=source_con)
        node = Node(node_id, node_type, activation_function, bias)
        self.nodes.append(node)

    def add_connection(self, weight, input_node, gater_node, output_node):
        connection_id = self.innovation_handler.assign_connection_id(connection=(input_node.node_id, output_node.node_id))
        connection = Connection(connection_id, weight, input_node, gater_node, output_node)
        self.connections.append(connection)

    def create_phenotype(self):
        self.determine_activation_order()
        self.node_pheno_to_geno = {pheno: geno for pheno, geno in enumerate(self.activation_order)}
        self.node_geno_to_pheno = {v: k for k, v in self.node_pheno_to_geno.items()}

        # Create connection matrix with 3 dimensions
        self.connection_matrix = torch.zeros((len(self.nodes), len(self.nodes), 2))
        self.connection_matrix[:, :, 1] = float('nan')

        for connection in self.connections:
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
            input_node_id = connection.input_node.node_id
            output_node_id = connection.output_node.node_id
            G.add_edge(input_node_id, output_node_id)

        # Determine activation order for input nodes
        input_nodes_subgraph = nx.DiGraph()
        input_nodes = [node.node_id for node in self.nodes if node.node_type == 'input']
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
                print('determine_activation_order stuck in an infinite loop!')
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
        inputs_pheno_ids = [self.node_geno_to_pheno[node.node_id] for node in self.nodes if node.node_type == 'input']
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

        output_pheno_ids = [self.node_geno_to_pheno[x.node_id] for x in self.nodes if x.node_type == 'output']
        outputs_tensor = self.activations[output_pheno_ids]

        if simulate_only:
            self.activations = old_activations

        return outputs_tensor

    def reset_state(self):
        self.activations = torch.zeros(len(self.nodes))


def main():
    # Create Genome
    genome = Genome()

    # Create Nodes
    genome.add_node('input', lambda x: x, 0.0)
    genome.add_node('input', lambda x: x, 0.0)
    genome.add_node('input', lambda x: x, 0.0)
    genome.add_node('output', F.sigmoid, 10.679)
    genome.add_node('hidden', F.sigmoid, -1.328)

    # Create Connections
    nodes = genome.nodes
    genome.add_connection(5.594, nodes[0], nodes[2], nodes[3])  # Example of using a gater node
    genome.add_connection(-4.893, nodes[1], None, nodes[3])
    genome.add_connection(0.079, nodes[2], None, nodes[0])
    genome.add_connection(-2.472, nodes[3], None, nodes[2])
    genome.add_connection(4.36, nodes[3], None, nodes[3])
    genome.add_connection(-1.311, nodes[0], None, nodes[4])
    genome.add_connection(8.205, nodes[4], None, nodes[3])
    genome.add_connection(-2.4, nodes[2], None, nodes[4])
    genome.add_connection(0.558, nodes[4], None, nodes[4])

    # Create Phenotype
    genome.create_phenotype()

    # Determine Activation Order
    genome.determine_activation_order()

    # Activate the Network
    input_activations = [0.0, 0.0, 1.0]
    genome.activate(input_activations)

    print("Activations:", genome.activations)


if __name__ == "__main__":
    main()
