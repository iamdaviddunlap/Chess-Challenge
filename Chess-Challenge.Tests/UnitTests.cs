using Xunit;
using Chess_Challenge;
using Chess_Challenge.NEAT_Bot;

public class UnitTests
{

    [Fact] // This attribute signifies that the method below is a test
    public void MainTest() {
        // Create an instance of your mutation operator
        MutationOperator mutationOperator = new MutationOperator();

        // Create a new genome with two nodes and one connection
        Genome genome = new Genome(inputs: 3, outputs: 1);

        Console.WriteLine("Original genome:");
        PrintGenome(genome);

        Random random = new Random(3);
        int numMutations = random.Next(10, 30); // Randomly choose between 1 and 10 mutations

        for (int i = 0; i < numMutations; i++) {
            int mutationChoice = random.Next(3); // Randomly choose between 0 and 2

            switch(mutationChoice) {
                case 0:
                    // Mutate the weights
                    mutationOperator.MutateWeights(genome, 0.7, 0.2);
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
        double[] outputs = genome.ForwardPropagate(inputs);
        
        var x = 1;
    }



    public static void PrintGenome(Genome genome)
    {
        Console.WriteLine("Nodes:");
        foreach (Node node in genome.Nodes)
        {
            Console.WriteLine($"  ID: {node.ID}, Type: {node.Type}, Depth: {node.Depth}");
        }

        Console.WriteLine("Connections:");
        foreach (Connection connection in genome.Connections)
        {
            Node node1 = connection.Nodes.Item1;
            Node node2 = connection.Nodes.Item2;

            Console.WriteLine($"  Nodes: {node1.ID}, {node2.ID}, Weight: {connection.Weight}, Enabled: {connection.IsEnabled}, Innovation: {connection.InnovationNumber}");
        }
    }

}