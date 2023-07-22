using System;
using System.Collections.Generic;
using System.Linq;

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
        
        public Connection(Node node1, Node node2, double weight, bool isEnabled, int innovationNumber)
        {
            Nodes = new Tuple<Node, Node>(node1, node2);
            Weight = weight;
            IsEnabled = isEnabled;
            InnovationNumber = innovationNumber;
        }
    }

    public class Genome {
        public List<Connection> Connections { get; set; }
        public List<Node> Nodes { get; set; }
        
        public double InitialWeight { get; set; }

        private int CurInnovationNumber;
        
        public Genome(int inputs, int outputs, double initialWeight = 0.5) {
            Connections = new List<Connection>();
            Nodes = new List<Node>();
            InitialWeight = initialWeight;
            CurInnovationNumber = 0;
            for (var i = 0; i < inputs; i++) {
                AddNode("input", depth: 0);
            }
            for (var i = 0; i < outputs; i++) {
                AddNode("output", depth: 1);
                for (var j = 0; j < Nodes.Count-(i+1); j++) {
                    var curIn = Nodes[j];
                    var curOut = Nodes[^1];
                    AddConnection(curIn, curOut, initialWeight, true);
                }
            }
        }

        public Connection AddConnection(Node node1, Node node2, double weight, bool isEnabled) {
            CurInnovationNumber++;
            var conn = new Connection(node1, node2, weight, isEnabled, innovationNumber: CurInnovationNumber);
            Connections.Add(conn);
            return conn;
        }
        
        public Node AddNode(string type, int depth) {
            var node = new Node { ID = Nodes.Count, Type = type, Depth = depth};
            Nodes.Add(node);
            return node;
        }
        
        public double[] ForwardPropagate(double[] inputs) {
            if (inputs.Length != Nodes.Count(n => n.Type == "input")) {
                throw new ArgumentException("Input length must be equal to the number of input nodes");
            }
            
            // Assign input values
            for (int i = 0; i < inputs.Length; i++) {
                Nodes[i].Value = inputs[i];
            }
            
            // Sort nodes by depth
            var orderedNodes = Nodes.OrderBy(n => n.Depth).ToList();
            
            // Propagate values
            foreach (var node in orderedNodes) {
                if (node.Type == "input") continue; // Skip input nodes
                node.Value = 0; // Reset value
                
                // Sum the product of the incoming connection weights and the source node values
                foreach (var conn in Connections.Where(c => c.Nodes.Item2.ID == node.ID && c.IsEnabled)) {
                    node.Value += conn.Weight * conn.Nodes.Item1.Value;
                }
                
                // Apply activation function (here using sigmoid)
                node.Value = 1.0 / (1.0 + Math.Exp(-node.Value));
            }

            // Return output values
            return Nodes.Where(n => n.Type == "output").Select(n => n.Value).ToArray();
        }
    }

    public class MutationOperator {
        private static int randomSeed = 1;
        public void MutateWeights(Genome genome, double perturbChance, double perturbValue) {
            Random random = new Random(randomSeed);

            foreach (Connection connection in genome.Connections) {
                // Check if we should perturb this connection weight
                if (random.NextDouble() < perturbChance) {
                    // Perturb the weight
                    connection.Weight += (random.NextDouble() * 2 - 1) * perturbValue;
                }
            }
        }

        public bool AddConnectionMutation(Genome genome, double minWeight, double maxWeight) {
            var numLoops = -1;
            const int maxLoops = 1000; // TODO determine this more intelligently?
            Random random = new Random(randomSeed);
            while (true) {
                numLoops++;
                if (numLoops > maxLoops) {
                    return false;
                }

                // Pick two random nodes
                Node node1 = genome.Nodes[random.Next(genome.Nodes.Count)];
                Node node2 = genome.Nodes[random.Next(genome.Nodes.Count)];
        
                if (node1.Depth == node2.Depth) {
                    continue;
                }

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
                    var weight = random.NextDouble() * (maxWeight - minWeight) + minWeight;
                    if (node1.Depth < node2.Depth) {
                        genome.AddConnection(node1, node2, weight, true);
                    }
                    else {
                        genome.AddConnection(node2, node1, weight, true);
                    }
                }
                else {
                    continue;
                }

                return true;
            }
        }

        public bool AddNodeMutation(Genome genome) {
            var numLoops = 0;
            const int maxLoops = 1000;
            Random random = new Random(randomSeed);
            while (true) {
                numLoops++;
                if (numLoops > maxLoops) {
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
                if (conn.Nodes.Item1 == node && conn.Nodes.Item2.Depth <= node.Depth) {
                    IncrementNodeDepth(genome, conn.Nodes.Item2);
                }
            }
        }
    }
}
