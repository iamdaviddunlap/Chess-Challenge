using System.Drawing;
using System.Drawing.Imaging;
using Chess_Challenge.NEAT_Bot;
using Color = System.Drawing.Color;
using Rectangle = System.Drawing.Rectangle;

namespace Chess_Challenge.Tests; 

public class UnitTests
{

    [Fact] // This attribute signifies that the method below is a test
    public void MainTest() {

        int randomSeed = 1;
        
        // Create an instance of your mutation operator
        MutationOperator mutationOperator = new MutationOperator();
    
        // Create a new genome with two nodes and one connection
        Genome genome = new Genome(inputs: 3, outputs: 1, randomSeed: randomSeed);
    
        Console.WriteLine("Original genome:");
        PrintGenome(genome);
    
        Random random = new Random(1);
        int numMutations = random.Next(30, 40); // Randomly choose between 1 and 10 mutations
    
        for (int i = 0; i < numMutations; i++) {
            int mutationChoice = random.Next(3); // Randomly choose between 0 and 2
    
            switch(mutationChoice) {
                case 0:
                    // Mutate the weights
                    mutationOperator.MutateWeights(genome, 0.7, 0.1, -1, 1);
                    Console.WriteLine("After weight mutation:");
                    PrintGenome(genome);
                    break;
                case 1:
                    // Add a new node
                    mutationOperator.AddNodeMutation(genome);
                    Console.WriteLine("After node addition:");
                    PrintGenome(genome);
                    break;
                case 2:
                    // Add a new connection
                    mutationOperator.AddConnectionMutation(genome, -1, 1);
                    Console.WriteLine("After connection addition:");
                    PrintGenome(genome);
                    break;
            }
        }
    
        // Set some input values
        double[] inputs = {0.2, 0.4, 0.6};
    
        // Propagate the values through the network
        double[] outputs = genome.Activate(inputs);
    
        DrawNetwork(genome, "network.png");
    }
    
    [Fact]
    public void RecurrentNetworkXORTest() {
        // Create an instance of your mutation operator
        MutationOperator mutationOperator = new MutationOperator();

        // Create a new genome with two nodes and one connection
        Genome genome = new Genome(inputs: 3, outputs: 1, randomSeed: 1);
        mutationOperator.AddNodeMutation(genome: genome, randomSeed: 5);
        genome.AddConnection(genome.Nodes[5-1], genome.Nodes[3-1], 1, true);
        genome.AddConnection(genome.Nodes[3-1], genome.Nodes[5-1], 1, true);
        genome.AddConnection(genome.Nodes[1-1], genome.Nodes[5-1], 1, true);
        PrintGenome(genome);
        
        // Loop through the weights and set them up to be the weights for XOR (found online a model with a recurrent
        //   connection and the weights for an XOR model
        List<double> new_weights = new List<double> { 12.46, -1, -7.47, 10.99, 11.78, 8.01, -3.67, -3.14 };
        for (int i = 0; i < genome.Connections.Count; i++) {
            genome.Connections[i].Weight = new_weights[i];
        }
        Console.WriteLine("After weight assignments for XOR:");
        PrintGenome(genome);

        // Set the input values to explore the full truth table. Note that the 3rd input is a bias node
        double[] inputs1 = {0, 0, 1};
        double[] inputs2 = {1, 0, 1};
        double[] inputs3 = {0, 1, 1};
        double[] inputs4 = {1, 1, 1};

        // Propagate the values through the network
        double zeroZeroOut = genome.Activate(inputs1)[0];
        double oneZeroOut = genome.Activate(inputs2)[0];
        double zeroOneOut = genome.Activate(inputs3)[0];
        double oneOneOut = genome.Activate(inputs4)[0];
        
        // Check that this network produces the correct outputs for XOR
        Assert.Equal(0, zeroZeroOut, precision: 1);
        Assert.Equal(1, oneZeroOut, precision: 1);
        Assert.Equal(1, zeroOneOut, precision: 1);
        Assert.Equal(0, oneOneOut, precision: 1);
    }

    public void DrawNetwork(Genome genome, string filename) 
    {
        int width = 2000;
        int height = 2000;
        int radius = 50;
        var bitmap = new Bitmap(width, height);
        var g = Graphics.FromImage(bitmap);

        // Calculate the positions of the nodes in the image
        var positions = CalculatePositions(genome, width, height);

        // Draw the connections
        DrawConnections(g, genome, positions);

        // Draw the nodes
        DrawNodes(g, genome, positions, radius);

        // Save the image
        bitmap.Save(filename, ImageFormat.Png);
    }

    private Dictionary<Node, Point> CalculatePositions(Genome genome, int width, int height)
    {
        var positions = new Dictionary<Node, Point>();
        var nodeDepths = genome.Nodes.Select(node => node.Depth).Distinct().ToList();
        var maxDepth = nodeDepths.Max();
        var depthOffsets = nodeDepths.ToDictionary(depth => depth, depth => depth.GetHashCode() % 2);

        foreach (var depth in nodeDepths)
        {
            var nodesAtDepth = genome.Nodes.Where(node => node.Depth == depth).ToList();
            var verticalSpacing = CalculateVerticalSpacing(height, nodesAtDepth.Count);

            for (var i = 0; i < nodesAtDepth.Count; i++)
            {
                var node = nodesAtDepth[i];
                int x = (depth + 1) * (width / (maxDepth + 2)) ;
                int y = (i + 1) * verticalSpacing + depthOffsets[depth]*50;
                positions[node] = new Point(x, y);
            }
        }
        return positions;
    }

    private int CalculateVerticalSpacing(int height, int count)
    {
        return height / (count + 1);
    }

    private void DrawConnections(Graphics g, Genome genome, Dictionary<Node, Point> positions)
    {
        // Assume these are the known min and max weights; adjust if needed.
        var minWeight = -1.0;
        var maxWeight = 1.0;

        foreach (var connection in genome.Connections)
        {
            if (!connection.IsEnabled)
            {
                continue;
            }

            var node1Pos = positions[connection.Nodes.Item1];
            var node2Pos = positions[connection.Nodes.Item2];

            // Calculate depth difference and curvature factor
            var depthDifference = Math.Abs(connection.Nodes.Item1.Depth - connection.Nodes.Item2.Depth);
            var curvatureFactor = depthDifference * 50; // Change this value to adjust curvature

            // Define points for bezier curve
            Point start = node1Pos;
            Point control1 = new Point((node1Pos.X + node2Pos.X) / 2, node1Pos.Y - curvatureFactor);
            Point control2 = new Point((node1Pos.X + node2Pos.X) / 2, node2Pos.Y + curvatureFactor);
            Point end = node2Pos;

            // Calculate line thickness and color based on weight
            float thickness = Math.Abs((float)connection.Weight) * 5; // Change this to adjust line thickness
            float t = (float)((connection.Weight - minWeight) / (maxWeight - minWeight));
            int red = (int)(255 * (1 - t));
            int green = (int)(255 * t);
            red = Math.Max(0, Math.Min(255, red));
            green = Math.Max(0, Math.Min(255, green));
            Color color = Color.FromArgb(red, green, 0); // Interpolate between red and green


            // Create a pen with the calculated thickness and color
            using (Pen pen = new Pen(color, thickness))
            {
                // Draw bezier curve
                g.DrawBezier(pen, start, control1, control2, end);
            }

            // Draw the weight of the connection
            var weightPos = new Point((node1Pos.X + node2Pos.X) / 2, (node1Pos.Y + node2Pos.Y) / 2);
            g.DrawString(Math.Round(connection.Weight, 2).ToString(), new System.Drawing.Font("Arial", 16), Brushes.Black, weightPos);
        }
    }


    private void DrawNodes(Graphics g, Genome genome, Dictionary<Node, Point> positions, int radius)
    {
        foreach (var node in genome.Nodes)
        {
            var pos = positions[node];
            g.FillEllipse(Brushes.Blue, pos.X - radius / 2, pos.Y - radius / 2, radius, radius);

            // Draw the ID of the node
            var format = new StringFormat() { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center };
            g.DrawString(node.ID.ToString(), new System.Drawing.Font("Arial", 16), Brushes.White, new Rectangle(pos.X - radius / 2, pos.Y - radius / 2, radius, radius), format);
        }
    }

    public static void PrintGenome(Genome genome) {
        Console.WriteLine("Nodes:");
        foreach (Node node in genome.Nodes) {
            Console.WriteLine($"  ID: {node.ID}, Type: {node.Type}, Depth: {node.Depth}");
        }

        Console.WriteLine("Connections:");
        foreach (Connection connection in genome.Connections) {
            Node node1 = connection.Nodes.Item1;
            Node node2 = connection.Nodes.Item2;

            Console.WriteLine($"  Nodes: {node1.ID}, {node2.ID}, Weight: {connection.Weight}, Enabled: {connection.IsEnabled}, Innovation: {connection.InnovationNumber}");
        }
    }

}