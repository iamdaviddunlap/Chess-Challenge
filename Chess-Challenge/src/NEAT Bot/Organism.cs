using System;
using System.Collections.Generic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public class Organism {

    public Genome Genome;
    public int Fitness { get; set; }
    public int SpeciesId { get; set; }

    public int OrganismId;

    private readonly InnovationHandler _innovationHandler;

    public Organism(Genome genome, InnovationHandler innovationHandler) {
        Genome = genome;
        _innovationHandler = innovationHandler;
        Fitness = -1;
        SpeciesId = -1;
        OrganismId = _innovationHandler.GetNextOrganismId();
    }
}

public class Genome {
        public List<Connection> Connections { get; set; }
        public List<Node> Nodes { get; set; }

        private readonly InnovationHandler _innovationHandler;
        private Random Random;

        public Genome(int inputs, int outputs, InnovationHandler innovationHandler, Random random, double minWeight = -1, double maxWeight = 1) {
            _innovationHandler = innovationHandler;
            this.Random = random;
            Connections = new List<Connection>();
            Nodes = new List<Node>();
            for (var i = 0; i < inputs; i++) {
                AddNode("input", depth: 0);
            }
            for (var i = 0; i < outputs; i++) {
                AddNode("output", depth: 1);
                for (var j = 0; j < Nodes.Count-(i+1); j++) {
                    var curIn = Nodes[j];
                    var curOut = Nodes[^1];
                    var weight = Math.Round(Random.NextDouble() * (maxWeight - minWeight) + minWeight, 3);
                    AddConnection(curIn, curOut, weight, true);
                }
            }
        }

        public Connection AddConnection(Node node1, Node node2, double weight, bool isEnabled) {
            var connKey = new Tuple<int, int>(node1.ID, node2.ID);
            var innovationNumber = _innovationHandler.AssignConnectionId(connKey);

            var conn = new Connection(node1, node2, weight, isEnabled, innovationNumber: innovationNumber);
            Connections.Add(conn);
            return conn;
        }
        
        public Node AddNode(string type, int depth, Connection? sourceConnection = null) {
            int nodeId;
            if (sourceConnection == null) {
                nodeId = Nodes.Count;
            }
            else {
                nodeId = _innovationHandler.AssignNodeId(
                    new Tuple<int, int>(sourceConnection.Nodes.Item1.ID, sourceConnection.Nodes.Item2.ID));
            }
            var node = new Node { ID = nodeId, Type = type, Depth = depth};
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
        
        public class Node {
            public int ID { get; set; }
            public string Type { get; set; }
            public double Value { get; set; }
            public int Depth { get; set; }
            
            public override string ToString() {
                return $"[{Type} {ID}]";
            }
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
            
            public override string ToString() {
                if (IsEnabled) {
                    return $"{Nodes.Item1} -> {Nodes.Item2}";
                }
                else {
                    return $"X| {Nodes.Item1} -> {Nodes.Item2} |X";
                }
            }
        }

}