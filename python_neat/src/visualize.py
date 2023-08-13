import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap


def cubic_bezier_midpoint(P0, P1, P2, P3):
    t = 0.5
    x_t = (
        ((1 - t) ** 3) * P0[0]
        + 3 * ((1 - t) ** 2) * t * P1[0]
        + 3 * (1 - t) * (t ** 2) * P2[0]
        + (t ** 3) * P3[0]
    )
    y_t = (
        ((1 - t) ** 3) * P0[1]
        + 3 * ((1 - t) ** 2) * t * P1[1]
        + 3 * (1 - t) * (t ** 2) * P2[1]
        + (t ** 3) * P3[1]
    )
    return (x_t, y_t)


def visualize_genome(genome, filename=None, show_plot=True, display_gates=False):
    from genome import NodeType
    """ Create a png to visualize the given genome. Note that display_gates if False by default because the code to
    display them doesn't work very well. """
    # Create a custom color map that goes from blue to gray to red
    custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', ['blue', 'red'])

    # Create a NetworkX directed graph
    G = nx.DiGraph()

    # Add nodes to the graph with attributes for positioning and bias
    for node in genome.nodes:
        if node.node_type.name == NodeType.INPUT.name:
            layer = 0
        elif node.node_type.name == NodeType.OUTPUT.name:
            layer = 2
        else:  # hidden nodes
            layer = 1

        G.add_node(node.node_id, layer=layer, type=node.node_type, bias=node.bias)

    # Add connections as edges in the graph with weights
    for connection in genome.connections:
        G.add_edge(connection.input_node.node_id, connection.output_node.node_id, weight=connection.weight)

    # Determine positions for the nodes with added randomness
    pos = {}
    layers = [[], [], []]  # input, hidden, output
    for node_id, data in G.nodes(data=True):
        layers[data['layer']].append(node_id)

    for i, layer in enumerate(layers):
        for j, node_id in enumerate(layer):
            x = i
            y = j / len(layer) + np.random.uniform(-0.05, 0.05) # Add randomness to the y-coordinate
            pos[node_id] = (x, y)

    # Determine node colors based on bias
    biases = [data['bias'] for _, data in G.nodes(data=True)]
    node_colors = custom_cmap((np.array(biases) + abs(min(biases))) / (max(biases) - min(biases)))

    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color=node_colors)

    # Determine edge colors based on weight
    edge_weights = [data['weight'] for _, _, data in G.edges(data=True)]
    edge_colors = custom_cmap((np.array(edge_weights) + abs(min(edge_weights))) / (max(edge_weights) - min(edge_weights)))

    # Draw the edges with splines and gates

    for (u, v, data), color in zip(G.edges(data=True), edge_colors):
        connection = next(
            (c for c in genome.connections if c.input_node.node_id == u and c.output_node.node_id == v),
            None)
        if connection and connection.is_enabled:
            if u == v:  # self-connection (loop)
                connectionstyle = 'arc3,rad=0.5'  # more pronounced curvature for loops
            else:
                connectionstyle = 'arc3,rad=0.2'  # normal curvature

            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=1.0, alpha=0.5, edge_color=[color],
                                   connectionstyle=connectionstyle)

            node_radius = 0.05

            # Control points for cubic Bezier curve
            P0 = pos[u]
            P3 = pos[v]
            curvature = 0.2  # The same curvature radius used in connectionstyle
            offset_y = (P3[1] - P0[1]) * curvature
            P1 = ((P0[0] + P3[0]) / 2, (P0[1] + P3[1]) / 2 + offset_y)
            P2 = P1  # Using the same point for P1 and P2 to create symmetric curvature

            midpoint = cubic_bezier_midpoint(P0, P1, P2, P3)

            if display_gates:  # Only display gates if display_gates is True
                # Check if there is a gater node and draw the gate
                connection = next(
                    (c for c in genome.connections if c.input_node.node_id == u and c.output_node.node_id == v),
                    None)
                if connection and connection.gater_node:
                    x_gate, y_gate = midpoint  # Midpoint of the x and y coordinates
                    x_gater, y_gater = pos[connection.gater_node.node_id]  # Gater node coordinates

                    # Calculate direction from midpoint to gater node
                    direction_x = x_gater - x_gate
                    direction_y = y_gater - y_gate

                    # Normalize the direction
                    length = (direction_x ** 2 + direction_y ** 2) ** 0.5
                    direction_x /= length
                    direction_y /= length

                    # Offset the gate line by the radius of the nodes
                    x_gate -= direction_x * node_radius
                    y_gate -= direction_y * node_radius

                    plt.plot([x_gate, x_gater], [y_gate, y_gater], 'gray', linestyle='dotted')

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=12)
    plt.axis('off')

    if filename is not None:
        plt.savefig(filename, format='PNG')

    if show_plot:
        plt.show()
