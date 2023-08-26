import json
from genome import NodeType, ACTIVATION_MAPPING, ActivationFunction, Genome
from visualize import visualize_genome


def genome_to_json(genome):
    # Create a dictionary to hold the serialized genome data
    genome_data = {
        'nodes': [],
        'connections': []
    }

    reverse_mapping = {v: k for k, v in ACTIVATION_MAPPING.items()}

    # Serialize nodes
    for node in genome.nodes:
        node_data = {
            'node_id': node.node_id,
            'node_type': node.node_type.value,
            'activation_function': reverse_mapping[node.activation_function].value,
            'bias': node.bias
        }
        genome_data['nodes'].append(node_data)

    # Serialize connections
    for connection in genome.connections:
        connection_data = {
            'connection_id': connection.connection_id,
            'weight': connection.weight,
            'input_node': connection.input_node.node_id,
            'gater_node': connection.gater_node.node_id if connection.gater_node else None,
            'output_node': connection.output_node.node_id,
            'is_enabled': connection.is_enabled
        }
        genome_data['connections'].append(connection_data)

    return genome_data


def json_to_genome(genome_data):
    loaded_genome = Genome(fill_genome=False)

    # Create and add nodes to loaded_genome
    for node_data in genome_data['nodes']:
        node_type = NodeType(node_data['node_type'])
        activation_function_name = node_data['activation_function']
        activation_function = ACTIVATION_MAPPING[ActivationFunction(activation_function_name)]
        bias = node_data['bias']
        node_id = node_data['node_id']
        loaded_genome.add_node(node_type, activation_function, bias, node_id=node_id)

    # Create and add connections to loaded_genome
    for connection_data in genome_data['connections']:
        weight = connection_data['weight']
        input_node_id = connection_data['input_node']
        gater_node_id = connection_data['gater_node']
        output_node_id = connection_data['output_node']
        is_enabled = connection_data['is_enabled']
        connection_id = connection_data['connection_id']

        # Find the corresponding nodes based on their IDs
        input_node = next(node for node in loaded_genome.nodes if node.node_id == input_node_id)
        gater_node = next((node for node in loaded_genome.nodes if node.node_id == gater_node_id), None)
        output_node = next(node for node in loaded_genome.nodes if node.node_id == output_node_id)

        # Add the connection
        connection = loaded_genome.add_connection(weight, input_node, gater_node, output_node,
                                                 connection_id=connection_id)
        connection.is_enabled = is_enabled

    # Initialize its phenotype
    loaded_genome.create_phenotype()
    return loaded_genome


if __name__ == '__main__':
    org_id_to_load = 7853
    with open(f'saved_genomes/2023-08-26__03-31-47_generation_20/{org_id_to_load}.json') as f:
        json_data = json.loads(f.read())
    loaded_genome = json_to_genome(json_data)
    x = 1
