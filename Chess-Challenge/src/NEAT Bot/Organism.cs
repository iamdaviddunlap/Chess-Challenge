using System;
using System.Collections.Generic;
using System.Dynamic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public class Organism {

    public Genome Genome;
    public double Fitness { get; set; }
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
    
    public Organism Reproduce(Random random, Organism? coParent = null) {
        Genome offspringGenome;
        if (coParent == null) {
            // Asexual reproduction
            offspringGenome = Genome.Clone();
            Mutation.MutateGenome(offspringGenome, random);
            return new Organism(offspringGenome, _innovationHandler);
        }
        // Sexual reproduction
        if(random.NextDouble() < Constants.MateAvgGenesProb) {
            // Pass selection function that averages two genes
            offspringGenome = MateMultipoint(random, coParent, (p1, p2, rnd) => Math.Round((p1 + p2) / 2.0, 3));
        } else {
            // Pass selection function that selects either one or the other gene
            offspringGenome = MateMultipoint(random, coParent, (p1, p2, rnd) => rnd.NextDouble() < 0.5 ? p1 : p2);
        }

        return new Organism(offspringGenome, _innovationHandler);
    }
    
    private Genome MateMultipoint(Random random, Organism coParent, Func<double, double, Random, double> selectionFunc) {
        var offspringGenome = new Genome(_innovationHandler, random, fillGenome: false);
        
        // Determine the more fit parent
        Organism moreFitParent = Fitness > coParent.Fitness ? this : coParent;
        bool thisIsMoreFit = moreFitParent == this;
        
        // Handle hidden nodes. Only take disjoint/excess nodes from the fitter parent
        foreach (var nodeId in moreFitParent.Genome.Nodes.Select(n => n.ID)) {
            Genome.Node? parentNode1 = (thisIsMoreFit ? this : coParent).Genome.Nodes.FirstOrDefault(n => n.ID == nodeId);
            Genome.Node? parentNode2 = (thisIsMoreFit ? coParent : this).Genome.Nodes.FirstOrDefault(n => n.ID == nodeId);
            
            Genome.Node newNode;
            if (parentNode1 != null && parentNode2 != null) { // Matching nodes
                var bias = selectionFunc(parentNode1.Bias, parentNode2.Bias, random);
                newNode = new Genome.Node { ID = nodeId, Type = parentNode1.Type, Depth = parentNode1.Depth, Bias = bias};
            } else { // Disjoint or excess node from fitter parent
                newNode = parentNode1 ?? parentNode2;
            }

            offspringGenome.AddNode(newNode.Type, parentNode1.Depth, nodeId: newNode.ID, bias: newNode.Bias);
        }
        
        var genome2InnovationNumbers = coParent.Genome.Connections.Select(c => c.InnovationNumber).ToList();

        // Identify matching connections
        var matchingConnections = Genome.Connections
            .Where(c => genome2InnovationNumbers.Contains(c.InnovationNumber))
            .ToList();

        // Handle matching connections
        foreach (var matchingConnection in matchingConnections) {
            var coParentGene = coParent.Genome.Connections.First(c => c.InnovationNumber == matchingConnection.InnovationNumber);
            var inNode = offspringGenome.GetNodeById(matchingConnection.Nodes.Item1.ID);
            var outNode = offspringGenome.GetNodeById(matchingConnection.Nodes.Item2.ID);
            var weightToUse = selectionFunc(matchingConnection.Weight, coParentGene.Weight, random);
            var connToUse = new Genome.Connection(inNode, outNode, innovationNumber: matchingConnection.InnovationNumber,
                isEnabled: matchingConnection.IsEnabled && coParentGene.IsEnabled, weight: weightToUse);
            var doEnable = connToUse.IsEnabled;
            if (!doEnable && random.NextDouble() > Constants.InheritDisableChance) {
                // Chance to re-enable disabled connection
                doEnable = true;
            }
            offspringGenome.AddConnection(inNode, outNode, connToUse.Weight, doEnable);
        }

        // Add any disjoint/excess nodes from the fitter parent
        foreach (var connection in moreFitParent.Genome.Connections) {
            if (matchingConnections.All(c => c.InnovationNumber != connection.InnovationNumber)) {
                var inNode = offspringGenome.GetNodeById(connection.Nodes.Item1.ID);
                var outNode = offspringGenome.GetNodeById(connection.Nodes.Item2.ID);
                offspringGenome.AddConnection(inNode, outNode, connection.Weight, connection.IsEnabled);
            }
        }

        return offspringGenome;
    }

    public override string ToString() {
        return $"Organism #{OrganismId}";
    }
}

public class Genome {
        public List<Connection> Connections { get; set; }
        public List<Node> Nodes { get; set; }

        private readonly InnovationHandler _innovationHandler;
        private Random Random;

        public Genome(InnovationHandler innovationHandler, Random random, bool fillGenome = true) {
            _innovationHandler = innovationHandler;
            this.Random = random;
            Connections = new List<Connection>();
            Nodes = new List<Node>();
            if (!fillGenome) return;
            for (var i = 0; i < Constants.InputsCount; i++) {
                AddNode("input", depth: 0, bias: 1.0);
            }
            for (var i = 0; i < Constants.OutputsCount; i++) {
                var bias = Math.Round(random.NextDouble() * 2 - 1, 3);
                AddNode("output", depth: 1, bias: bias);
                for (var j = 0; j < Nodes.Count - (i + 1); j++) {
                    var curIn = Nodes[j];
                    var curOut = Nodes[^1];
                    var weight = Math.Round(random.NextDouble() * 2 - 1, 3);
                    AddConnection(curIn, curOut, weight, true);
                }
            }
        }
        
        public Node? GetNodeById(int id) {
            return Nodes.FirstOrDefault(node => node.ID == id);
        }
        
        public Genome Clone() {
            Genome clonedGenome = new Genome(_innovationHandler, Random, fillGenome: false);
        
            // Cloning Nodes
            foreach (var node in Nodes) {
                clonedGenome.AddNode(node.Type, node.Depth, node.Bias, nodeId: node.ID);
            }
        
            // Cloning Connections
            foreach (var connection in Connections) {
                var node1 = clonedGenome.Nodes.First(n => n.ID == connection.Nodes.Item1.ID);
                var node2 = clonedGenome.Nodes.First(n => n.ID == connection.Nodes.Item2.ID);
                clonedGenome.AddConnection(node1, node2, connection.Weight, connection.IsEnabled, connId: connection.InnovationNumber);
            }

            return clonedGenome;
        }

        public double GeneticDifference(Genome genome2) {
            var genome1InnovationNumbers = new HashSet<int>(Connections.Select(c => c.InnovationNumber));
            var genome2InnovationNumbers = new HashSet<int>(genome2.Connections.Select(c => c.InnovationNumber));

            // Calculate the smaller max innovation number
            int maxInnovationNumber = Math.Min(genome1InnovationNumbers.Max(), genome2InnovationNumbers.Max());

            var matchingInnovationNumbers = genome1InnovationNumbers.Intersect(genome2InnovationNumbers).ToList();

            int disjointCount = genome1InnovationNumbers.Except(matchingInnovationNumbers).Count(n => n <= maxInnovationNumber)
                                + genome2InnovationNumbers.Except(matchingInnovationNumbers).Count(n => n <= maxInnovationNumber);

            int excessCount = genome1InnovationNumbers.Except(matchingInnovationNumbers).Count(n => n > maxInnovationNumber)
                              + genome2InnovationNumbers.Except(matchingInnovationNumbers).Count(n => n > maxInnovationNumber);

            double weightDifferenceSum = 0;
            foreach (var innovationNumber in matchingInnovationNumbers) {
                var genome1Weight = Connections.First(c => c.InnovationNumber == innovationNumber).Weight;
                var genome2Weight = genome2.Connections.First(c => c.InnovationNumber == innovationNumber).Weight;
                weightDifferenceSum += Math.Abs(genome1Weight - genome2Weight);
            }
            double averageWeightDifference = matchingInnovationNumbers.Count > 0 ? weightDifferenceSum / matchingInnovationNumbers.Count : 0;
            
            var sharedNodes = Nodes.Where(node1 => genome2.Nodes.Any(node2 => node2.ID == node1.ID)).ToList();
            double biasDifferenceSum = 0;
            foreach (var sharedNode in sharedNodes) {
                var genome1Bias = Nodes.First(n => n.ID == sharedNode.ID).Bias;
                var genome2Bias = genome2.Nodes.First(n => n.ID == sharedNode.ID).Bias;
                biasDifferenceSum += Math.Abs(genome1Bias - genome2Bias);
            }
            double averageBiasDifference = sharedNodes.Count > 0 ? biasDifferenceSum / sharedNodes.Count : 0;
            double averageCombinedDifference = (averageWeightDifference + averageBiasDifference) / 2.0;

            int n = Math.Max(Connections.Count, genome2.Connections.Count);

            double geneticDistance = ((Constants.ExcessCoeff * excessCount) / n) + 
                                     ((Constants.DisjointCoeff * disjointCount) / n) + 
                                     (Constants.WeightCoeff * averageCombinedDifference);
            return geneticDistance;
        }


        public Connection AddConnection(Node node1, Node node2, double weight, bool isEnabled, int connId = -1) {
            var connKey = new Tuple<int, int>(node1.ID, node2.ID);
            var innovationNumber = connId == -1 ? _innovationHandler.AssignConnectionId(connKey) : connId;

            var conn = new Connection(node1, node2, weight, isEnabled, innovationNumber: innovationNumber);
            Connections.Add(conn);
            return conn;
        }
        
        public Node AddNode(string type, int depth, double bias, int nodeId = -1, Connection? sourceConnection = null) {
            if(nodeId == -1) {
                if (sourceConnection == null) {
                    nodeId = Nodes.Count;
                }
                else {
                    nodeId = _innovationHandler.AssignNodeId(
                        new Tuple<int, int>(sourceConnection.Nodes.Item1.ID, sourceConnection.Nodes.Item2.ID));
                }
            }
            var node = new Node { ID = nodeId, Type = type, Depth = depth, Bias = bias};
            Nodes.Add(node);
            return node;
        }

        public double[] Activate(double[] inputs, int timestepsPerActivation = 1) {
            // TODO use bias
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
            
            public double Bias { get; set; }

            public override string ToString() {
                return $"[{Type} {ID} {{{Bias}}}]";
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
                    return $"{InnovationNumber}: {Nodes.Item1} -> {Nodes.Item2} :: {Weight}";
                }
                else {
                    return $"{InnovationNumber}: X| {Nodes.Item1} -> {Nodes.Item2} :: {Weight} |X";
                }
            }
        }

}