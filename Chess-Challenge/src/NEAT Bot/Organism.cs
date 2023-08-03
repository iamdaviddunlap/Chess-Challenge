using System;
using System.Collections.Generic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public class Organism {

    public Genome Genome;
    public int Fitness { get; set; }
    public int SpeciesId { get; set; }

    public Organism(Genome genome) {
        Genome = genome;
        Fitness = -1;
        SpeciesId = -1;
    }
}

public class Genome {
        public List<Connection> Connections { get; set; }
        public List<Node> Nodes { get; set; }
        
        public double InitialWeight { get; set; }

        private int _curInnovationNumber;

        public Genome(int inputs, int outputs, double minWeight = -1, double maxWeight = 1, int? randomSeed = null) {
            Random random = randomSeed.HasValue ? new Random(randomSeed.Value) : new Random();

            Connections = new List<Connection>();
            Nodes = new List<Node>();
            _curInnovationNumber = 0;
            for (var i = 0; i < inputs; i++) {
                AddNode("input", depth: 0);
            }
            for (var i = 0; i < outputs; i++) {
                AddNode("output", depth: 1);
                for (var j = 0; j < Nodes.Count-(i+1); j++) {
                    var curIn = Nodes[j];
                    var curOut = Nodes[^1];
                    var weight = Math.Round(random.NextDouble() * (maxWeight - minWeight) + minWeight, 3);
                    AddConnection(curIn, curOut, weight, true);
                }
            }
        }

        public Connection AddConnection(Node node1, Node node2, double weight, bool isEnabled) {
            _curInnovationNumber++;
            var conn = new Connection(node1, node2, weight, isEnabled, innovationNumber: _curInnovationNumber);
            Connections.Add(conn);
            return conn;
        }
        
        public Node AddNode(string type, int depth) {
            var node = new Node { ID = Nodes.Count, Type = type, Depth = depth};
            Nodes.Add(node);
            return node;
        }

        public double[] Activate(double[] inputs, int timestepsPerActivation = 1) {
            if (inputs.Length != Nodes.Count(n => n.Type == "input")) {
                throw new ArgumentException("Input length must be equal to the number of input nodes");
            }
    
            // Assign input values
            for (int i = 0; i < inputs.Length; i++) {
                Nodes[i].Value = inputs[i];
            }
    
            // Sort nodes by depth
            var orderedNodes = Nodes.OrderBy(n => n.Depth).ToList();
    
            // Activate the network for a fixed number of time steps
            for (int t = 0; t < timestepsPerActivation; t++) {
                // Propagate values
                foreach (var node in orderedNodes) {
                    if (node.Type != "input") {
                        node.Value = 0; // Reset value
                    }

                    // Sum the product of the incoming connection weights and the source node values
                    foreach (var conn in Connections.Where(c => c.Nodes.Item2.ID == node.ID && c.IsEnabled)) {
                        node.Value += conn.Weight * conn.Nodes.Item1.Value;
                    }
            
                    // Apply activation function (here using sigmoid)
                    if (node.Type != "input") {
                        node.Value = 1.0 / (1.0 + Math.Exp(-node.Value));
                    }
                }
            }

            // Return output values
            return Nodes.Where(n => n.Type == "output").Select(n => n.Value).ToArray();
        }
        
        public void ResetState() {
            foreach (var node in Nodes) {
                node.Value = 0;
            }
        }

    }