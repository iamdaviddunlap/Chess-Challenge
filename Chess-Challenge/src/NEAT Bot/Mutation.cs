using System;

namespace Chess_Challenge.NEAT_Bot; 

public static class Mutation {
    
    public static void MutateGenome(Genome genome, double minWeight, double maxWeight, Random random) {
        
        const double mutateWeightsProb = 0.8;
        const double addConnectionProb = 0.3;
        // const double addNodeProb = 0.01;  // This is the val from Ken Stanley, I'm increasing for testing
        const double addNodeProb = 0.3;

        // Check if we should mutate weights
        if (random.NextDouble() < mutateWeightsProb) {
            const double perturbChance = 0.9;
            const double perturbValue = 0.1;
            MutateWeights(genome, perturbChance, perturbValue, minWeight, maxWeight, random);
        }

        // Check if we should add a connection
        if (random.NextDouble() < addConnectionProb) {
            AddConnectionMutation(genome, minWeight, maxWeight, random);
        }

        // Check if we should add a node
        if (random.NextDouble() < addNodeProb) {
            AddNodeMutation(genome, random);
        }
    }
    
    private static void MutateWeights(Genome genome, double perturbChance, double perturbValue, double minWeight, double maxWeight, Random random) {

        foreach (var connection in genome.Connections) {
            // Check if we should perturb this connection weight
            if (random.NextDouble() < perturbChance) {
                // Perturb the weight
                var newWeight = connection.Weight + (random.NextDouble() * 2 - 1) * perturbValue;

                // Ensure the new weight stays within the min and max bounds
                if (newWeight < minWeight) {
                    connection.Weight = minWeight;
                } else if (newWeight > maxWeight) {
                    connection.Weight = maxWeight;
                } else {
                    connection.Weight = newWeight;
                }

                // Round the weight to 3 decimal places
                connection.Weight = Math.Round(connection.Weight, 3);
            }
        }
    }




    private static bool AddConnectionMutation(Genome genome, double minWeight, double maxWeight, Random random) {
        var numLoops = -1;
        const int maxLoops = 1000; // TODO determine this more intelligently?
        while (true) {
            numLoops++;
            if (numLoops >= maxLoops) {
                return false;
            }

            // Pick two random nodes
            var node1 = genome.Nodes[random.Next(genome.Nodes.Count)];
            var node2 = genome.Nodes[random.Next(genome.Nodes.Count)];

            // Uncomment this to restrict connecting nodes that are on the same depth
            // if (node1.Depth == node2.Depth) {
            //     continue;
            // }

            // Check if these two nodes are already connected
            var areConnected = false;
            foreach (var conn in genome.Connections) {
                if ((conn.Nodes.Item1 == node1 && conn.Nodes.Item2 == node2) || (conn.Nodes.Item1 == node2 && conn.Nodes.Item2 == node1)) {
                    areConnected = true;
                    break;
                }
            }

            if (!areConnected) {
                // Add the new connection to the genome
                var weight = Math.Round(random.NextDouble() * (maxWeight - minWeight) + minWeight, 3);
                // Uncomment this to enforce all connections going forward (ie disallowing recurrent connections)
                // if (node1.Depth < node2.Depth) {
                //     genome.AddConnection(node1, node2, weight, true);
                // }
                // else {
                //     genome.AddConnection(node2, node1, weight, true);
                // }
                genome.AddConnection(node1, node2, weight, true);
            }
            else {
                continue;
            }

            return true;
        }
    }

    private static bool AddNodeMutation(Genome genome, Random random) {
        var numLoops = 0;
        const int maxLoops = 1000;
        while (true) {
            numLoops++;
            if (numLoops >= maxLoops) {
                return false;
            }

            // Pick a random connection to split
            var oldConnection = genome.Connections[random.Next(genome.Connections.Count)];

            // Don't split a disabled connection, a self-connection, or a recurrent connection
            if (!oldConnection.IsEnabled || oldConnection.Nodes.Item1.ID >= oldConnection.Nodes.Item2.ID) {
                continue;
            }

            // Disable the old connection
            oldConnection.IsEnabled = false;

            // Create new node
            var newNode = genome.AddNode("hidden", depth: oldConnection.Nodes.Item1.Depth+1, sourceConnection: oldConnection);
        
            // Increment depth for old output if needed
            if (oldConnection.Nodes.Item1.Depth + 1 == oldConnection.Nodes.Item2.Depth) {
                _IncrementNodeDepth(genome, oldConnection.Nodes.Item2);
            }

            genome.AddConnection(oldConnection.Nodes.Item1, newNode, 1, true);
            genome.AddConnection(newNode, oldConnection.Nodes.Item2, oldConnection.Weight, true);

            return true;
        }
    }

    private static void _IncrementNodeDepth(Genome genome, Genome.Node node) {
        node.Depth++;
        foreach (var conn in genome.Connections) {
            if (conn.Nodes.Item1 == node && conn.Nodes.Item2.Depth == node.Depth) {
                _IncrementNodeDepth(genome, conn.Nodes.Item2);
            }
        }
    }
}