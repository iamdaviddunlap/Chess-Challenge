using System;
using System.Collections.Generic;
using System.Linq;
using Chess_Challenge.NEAT_Bot;

namespace Chess_Challenge.NEAT_Bot {
    public class Node {
        public int ID { get; set; }
        public string Type { get; set; }
        public double Value { get; set; }
        public int Depth { get; set; }
    }

    public class Connection {
        public Tuple<Node, Node> Nodes { get; private set; }
        public double Weight { get; set; }
        public bool IsEnabled { get; set; }
        public int InnovationNumber { get; set; }

        public Connection(Node node1, Node node2, double weight, bool isEnabled, int innovationNumber) {
            Nodes = new Tuple<Node, Node>(node1, node2);
            Weight = weight;
            IsEnabled = isEnabled;
            InnovationNumber = innovationNumber;
        }
    }
}

public class MutationOperator {
    public void MutateWeights(Genome genome, double perturbChance, double perturbValue, double minWeight, double maxWeight, int? randomSeed = null) {
        Random random = randomSeed.HasValue ? new Random(randomSeed.Value) : new Random();

        foreach (Connection connection in genome.Connections) {
            // Check if we should perturb this connection weight
            if (random.NextDouble() < perturbChance) {
                // Perturb the weight
                double newWeight = connection.Weight + (random.NextDouble() * 2 - 1) * perturbValue;

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




    public bool AddConnectionMutation(Genome genome, double minWeight, double maxWeight, int? randomSeed = null) {
        var numLoops = -1;
        const int maxLoops = 1000; // TODO determine this more intelligently?
        Random random = randomSeed.HasValue ? new Random(randomSeed.Value) : new Random();
        while (true) {
            numLoops++;
            if (numLoops >= maxLoops) {
                return false;
            }

            // Pick two random nodes
            Node node1 = genome.Nodes[random.Next(genome.Nodes.Count)];
            Node node2 = genome.Nodes[random.Next(genome.Nodes.Count)];

            // Uncomment this to restrict connecting nodes that are on the same depth
            // if (node1.Depth == node2.Depth) {
            //     continue;
            // }

            // Check if these two nodes are already connected
            var areConnected = false;
            foreach (Connection conn in genome.Connections) {
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

    public bool AddNodeMutation(Genome genome, int? randomSeed = null) {
        var numLoops = 0;
        const int maxLoops = 1000;
        Random random = randomSeed.HasValue ? new Random(randomSeed.Value) : new Random();
        while (true) {
            numLoops++;
            if (numLoops >= maxLoops) {
                return false;
            }

            // Pick a random connection to split
            Connection oldConnection = genome.Connections[random.Next(genome.Connections.Count)];

            if (!oldConnection.IsEnabled) {
                continue;
            }

            // Disable the old connection
            oldConnection.IsEnabled = false;

            // Create new node
            Node newNode = genome.AddNode("hidden", depth: oldConnection.Nodes.Item1.Depth+1);
        
            // Increment depth for old output if needed
            if (oldConnection.Nodes.Item1.Depth + 1 == oldConnection.Nodes.Item2.Depth) {
                IncrementNodeDepth(genome, oldConnection.Nodes.Item2);
            }

            genome.AddConnection(oldConnection.Nodes.Item1, newNode, 1, true);
            genome.AddConnection(newNode, oldConnection.Nodes.Item2, oldConnection.Weight, true);

            return true;
        }
    }

    private void IncrementNodeDepth(Genome genome, Node node) {
        node.Depth++;
        foreach (var conn in genome.Connections) {
            if (conn.Nodes.Item1 == node && conn.Nodes.Item2.Depth == node.Depth) {
                IncrementNodeDepth(genome, conn.Nodes.Item2);
            }
        }
    }
}
