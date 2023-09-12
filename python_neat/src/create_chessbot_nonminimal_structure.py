import random
import json
import os

from genome import ACTIVATION_MAPPING

random.seed(1)

activation_function_strs = [x.value for x in ACTIVATION_MAPPING]

for genome_id in range(200):
    # Initialize lists to store nodes and connections for the new neural network
    new_nodes = []
    new_connections = []

    # Create 285 input nodes
    for i in range(285):
        new_nodes.append({
            'node_id': i,
            'node_type': 'input',
            'activation_function': 'identity',
            'bias': 0.0
        })

    # Create output node
    new_nodes.append({
        'node_id': 285,
        'node_type': 'output',
        'activation_function': 'tanh',
        'bias': round(random.uniform(-1, 1), 3)
    })

    # Node 286 connected to the output
    new_nodes.append({
        'node_id': 286,
        'node_type': 'hidden',
        'activation_function': random.choice(activation_function_strs),
        'bias': round(random.uniform(-1, 1), 3)
    })
    new_connections.append({
        'connection_id': len(new_connections) + 1,
        'weight': round(random.uniform(-1, 1), 3),
        'input_node': 0,
        'gater_node': None,
        'output_node': 286,
        'is_enabled': True
    })
    new_connections.append({
        'connection_id': len(new_connections) + 1,
        'weight': round(random.uniform(-1, 1), 3),
        'input_node': 286,
        'gater_node': None,
        'output_node': 285,
        'is_enabled': True
    })

    # Nodes 1-4, 5-8, 9-12, etc. connected to new hidden nodes
    next_node_id = 287
    for i in range(1, 257, 4):
        new_nodes.append({
            'node_id': next_node_id,
            'node_type': 'hidden',
            'activation_function': random.choice(activation_function_strs),
            'bias': round(random.uniform(-1, 1), 3)
        })
        for j in range(4):
            new_connections.append({
                'connection_id': len(new_connections) + 1,
                'weight': round(random.uniform(-1, 1), 3),
                'input_node': i + j,
                'gater_node': None if j != 0 else 286,  # First node in each group is gated by node 286
                'output_node': next_node_id,
                'is_enabled': True
            })
        next_node_id += 1

    # Hidden nodes connected to a new node
    new_nodes.append({
        'node_id': next_node_id,
        'node_type': 'hidden',
        'activation_function': random.choice(activation_function_strs),
        'bias': round(random.uniform(-1, 1), 3)
    })
    for i in range(287, next_node_id):
        new_connections.append({
            'connection_id': len(new_connections) + 1,
            'weight': round(random.uniform(-1, 1), 3),
            'input_node': i,
            'gater_node': None,
            'output_node': next_node_id,
            'is_enabled': True
        })
    next_node_id += 1

    # Connecting the new hidden node to the output
    new_connections.append({
        'connection_id': len(new_connections) + 1,
        'weight': round(random.uniform(-1, 1), 3),
        'input_node': next_node_id - 1,
        'gater_node': None,
        'output_node': 285,
        'is_enabled': True
    })

    # Nodes 257-260, 261-264, etc. connected to new hidden nodes
    for i in range(257, 277, 4):
        new_nodes.append({
            'node_id': next_node_id,
            'node_type': 'hidden',
            'activation_function': random.choice(activation_function_strs),
            'bias': round(random.uniform(-1, 1), 3)
        })
        for j in range(4):
            new_connections.append({
                'connection_id': len(new_connections) + 1,
                'weight': round(random.uniform(-1, 1), 3),
                'input_node': i + j,
                'gater_node': None,
                'output_node': next_node_id,
                'is_enabled': True
            })
        next_node_id += 1

    # Connecting the 5 new hidden nodes to the output
    for i in range(next_node_id - 5, next_node_id):
        new_connections.append({
            'connection_id': len(new_connections) + 1,
            'weight': round(random.uniform(-1, 1), 3),
            'input_node': i,
            'gater_node': None,
            'output_node': 285,
            'is_enabled': True
        })

    # Nodes 277-280 and 281-284 connected to new hidden nodes
    for i in range(277, 285, 4):
        new_nodes.append({
            'node_id': next_node_id,
            'node_type': 'hidden',
            'activation_function': random.choice(activation_function_strs),
            'bias': round(random.uniform(-1, 1), 3)
        })
        for j in range(4):
            new_connections.append({
                'connection_id': len(new_connections) + 1,
                'weight': round(random.uniform(-1, 1), 3),
                'input_node': i + j,
                'gater_node': None if j not in [0, 3] else 286,  # Nodes 277 and 280 are gated by node 286
                'output_node': next_node_id,
                'is_enabled': True
            })
        next_node_id += 1

    # Connecting the last 2 hidden nodes to the output
    for i in range(next_node_id - 2, next_node_id):
        new_connections.append({
            'connection_id': len(new_connections) + 1,
            'weight':  round(random.uniform(-1, 1), 3),
            'input_node': i,
            'gater_node': None,
            'output_node': 285,
            'is_enabled': True
        })

    new_nn = {
        'nodes': new_nodes,
        'connections': new_connections
    }

    # Save the new neural network to a JSON file
    population_name = "host" if genome_id <= 99 else "parasite"
    output_path = f"saved_genomes/custom_created/{population_name}/"
    os.makedirs(output_path, exist_ok=True)
    output_path += f'{genome_id}.json'
    with open(output_path, "w+") as file:
        json.dump(new_nn, file, indent=4)
