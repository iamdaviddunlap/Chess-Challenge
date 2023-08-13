import json
import torch.nn.functional as F


def genome_to_json(genome):
    # Serialize nodes
    nodes_json = [
        {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "activation_function": node.activation_function.__name__,
            "bias": node.bias
        }
        for node in genome.nodes
    ]

    # Serialize connections
    connections_json = [
        {
            "connection_id": connection.connection_id,
            "weight": connection.weight,
            "input_node": connection.input_node.node_id,
            "gater_node": connection.gater_node.node_id if connection.gater_node else None,
            "output_node": connection.output_node.node_id
        }
        for connection in genome.connections
    ]

    # Combine nodes and connections into a single dictionary
    genome_json = {
        "nodes": nodes_json,
        "connections": connections_json
    }

    # Convert the dictionary to a JSON string
    return json.dumps(genome_json)


def json_to_genome(json_str, empty_genome):
    # Parse the JSON string into a dictionary
    genome_data = json.loads(json_str)

    genome = empty_genome

    # Deserialize nodes
    for node_data in genome_data["nodes"]:
        activation_function = getattr(F, node_data["activation_function"])
        genome.add_node(
            node_data["node_type"],
            activation_function,
            node_data["bias"],
            node_id=node_data["node_id"]
        )

    # Build a mapping of node IDs to Node objects
    node_id_to_obj = {node.node_id: node for node in genome.nodes}

    # Deserialize connections
    for connection_data in genome_data["connections"]:
        input_node = node_id_to_obj[connection_data["input_node"]]
        gater_node = node_id_to_obj[connection_data["gater_node"]] if connection_data["gater_node"] else None
        output_node = node_id_to_obj[connection_data["output_node"]]
        genome.add_connection(
            connection_data["weight"],
            input_node,
            gater_node,
            output_node
        )

    return genome
