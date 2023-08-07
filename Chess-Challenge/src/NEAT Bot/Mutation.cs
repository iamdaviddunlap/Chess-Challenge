using System;
using System.Collections.Generic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public static class Mutation {
    
    public static void MutateGenome(Genome genome, Random random) {
        
        if (random.NextDouble() < Constants.AddNodeProb) {  // Check if we should add a node
            AddNodeMutation(genome, random);
        } else if (random.NextDouble() < Constants.AddConnectionProb) {
            AddConnectionMutation(genome, random);
        } else {
            // Do any number of other non-structural mutations
            List<Genome.Connection> removableConnections = null;
            if (random.NextDouble() < Constants.MutateWeightsProb) {
                MutateWeights(genome, random);
            }
            if (random.NextDouble() < Constants.MutateBiasesProb) { 
                MutateBiases(genome, random);
            }
            if (random.NextDouble() < Constants.MutateToggleEnableProb) {
                removableConnections ??= FindConsForRemoval(genome, random);
                MutateToggleEnable(genome, removableConnections, random);
            }
            if (random.NextDouble() < Constants.MutateReenableProb) {
                MutateGeneReenable(genome, random);
            }
            if (random.NextDouble() < Constants.MutateRemoveConnectionProb) {
                removableConnections ??= FindConsForRemoval(genome, random);
                MutateRemoveConnection(genome, removableConnections, random);
            }
        }
    }
    
    public static void MutateWeights(Genome genome, Random random) {

        foreach (var connection in genome.Connections) {
            // Check if we should perturb this connection weight
            if (random.NextDouble() < Constants.WeightPerturbChance) {
                // Perturb the weight
                var perturbAmount = (random.NextDouble() * 2 - 1) * Constants.WeightPerturbValue;
                var newWeight = connection.Weight + perturbAmount;

                // Ensure the new weight stays within the min and max bounds
                if (newWeight < Constants.MinVal) {
                    connection.Weight = Constants.MinVal;
                } else if (newWeight > Constants.MaxVal) {
                    connection.Weight = Constants.MaxVal;
                } else {
                    connection.Weight = newWeight;
                }

                // Round the weight to 3 decimal places
                connection.Weight = Math.Round(connection.Weight, 3);
            }
        }
    }
    
    public static void MutateBiases(Genome genome, Random random) {
        foreach (var node in genome.Nodes) {
            // Skip input nodes
            if (node.Type == "input") {
                continue;
            }

            // Check if we should perturb this node's bias
            if (random.NextDouble() < Constants.BiasPerturbChance) {
                // Perturb the bias
                var perturbAmount = (random.NextDouble() * 2 - 1) * Constants.BiasPerturbValue;
                var newBias = node.Bias + perturbAmount;

                // Ensure the new bias stays within the min and max bounds
                if (newBias < Constants.MinVal) {
                    node.Bias = Constants.MinVal;
                } else if (newBias > Constants.MaxVal) {
                    node.Bias = Constants.MaxVal;
                } else {
                    node.Bias = newBias;
                }

                // Round the bias to 3 decimal places
                node.Bias = Math.Round(node.Bias, 3);
            }
        }
    }

    public static void MutateToggleEnable(Genome genome,  List<Genome.Connection> eligibleConnections, Random random) {
        
        // Add currently disabled connections to eligible ones for toggling enable
        eligibleConnections.AddRange(genome.Connections.FindAll(c => !c.IsEnabled));
        
        // If there are any eligible connections
        if (eligibleConnections.Count <= 0) return;
        // Pick one at random and remove it
        var connection = eligibleConnections[random.Next(eligibleConnections.Count)];
    
        // Toggle the IsEnabled attribute
        connection.IsEnabled = !connection.IsEnabled;
    }

    public static void MutateGeneReenable(Genome genome, Random random) {
        // Find all disabled connections
        var disabledConnections = genome.Connections.Where(conn => !conn.IsEnabled).ToList();

        // If there are any disabled connections
        if (disabledConnections.Count > 0) {
            // Pick one at random and enable it
            var connectionToReenable = disabledConnections[random.Next(disabledConnections.Count)];
            connectionToReenable.IsEnabled = true;
        }
    }
    
    public static void MutateRemoveConnection(Genome genome, List<Genome.Connection> eligibleConnections, Random random) {

        // If there are any eligible connections
        if (eligibleConnections.Count <= 0) return;
        // Pick one at random and remove it
        var connectionToRemove = eligibleConnections[random.Next(eligibleConnections.Count)];
        genome.Connections.Remove(connectionToRemove);
    }

    private static List<Genome.Connection> FindConsForRemoval(Genome genome, Random random) {
        // Create dictionaries to count how many times each node appears as a source and a target
        Dictionary<Genome.Node, int> sourceCount = new Dictionary<Genome.Node, int>();
        Dictionary<Genome.Node, int> targetCount = new Dictionary<Genome.Node, int>();

        foreach (var conn in genome.Connections) {
            var sourceNode = conn.Nodes.Item1;
            var targetNode = conn.Nodes.Item2;

            if (sourceCount.ContainsKey(sourceNode)) {
                sourceCount[sourceNode]++;
            } else {
                sourceCount[sourceNode] = 1;
            }

            if (targetCount.ContainsKey(targetNode)) {
                targetCount[targetNode]++;
            } else {
                targetCount[targetNode] = 1;
            }
        }

        // Filter out the connections where both the source and the target appear more than once
        var eligibleConnections = genome.Connections.Where(conn => 
            sourceCount[conn.Nodes.Item1] > 1 && targetCount[conn.Nodes.Item2] > 1).ToList();
        
        return eligibleConnections;
    }
    
    private static bool AddConnectionMutation(Genome genome, Random random) {
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
                var weight = Math.Round(random.NextDouble() * 2 - 1, 3);
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
            var bias = Math.Round(random.NextDouble() * 2 - 1, 3);
            var newNode = genome.AddNode("hidden", depth: oldConnection.Nodes.Item1.Depth+1, sourceConnection: oldConnection, bias: bias);
        
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
            if (conn.Nodes.Item1 == node && conn.Nodes.Item2.Depth == node.Depth && conn.Nodes.Item1.ID != conn.Nodes.Item2.ID) {
                _IncrementNodeDepth(genome, conn.Nodes.Item2);
            }
        }
    }
}