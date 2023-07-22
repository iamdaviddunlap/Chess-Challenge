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

        // Mutate the weights
        mutationOperator.MutateWeights(genome, 0.7, 0.2);
        Console.WriteLine("After weight mutation:");
        PrintGenome(genome);
        
        // Add a new node
        mutationOperator.AddNodeMutation(genome);
        Console.WriteLine("After node addition:");
        PrintGenome(genome);
        
        // Add a new node
        mutationOperator.AddNodeMutation(genome);
        Console.WriteLine("After node addition:");
        PrintGenome(genome);

        // Add a new connection
        var res_addconn1 = mutationOperator.AddConnectionMutation(genome, -1, 1);
        Console.WriteLine("After connection addition:");
        PrintGenome(genome);
        
        // Add a new connection
        var res_addconn2 = mutationOperator.AddConnectionMutation(genome, -1, 1);
        Console.WriteLine("After connection addition:");
        PrintGenome(genome);
        
        // Add a new connection
        var res_addconn3 = mutationOperator.AddConnectionMutation(genome, -1, 1);
        Console.WriteLine("After connection addition:");
        PrintGenome(genome);
        
        // Add a new connection
        var res_addconn4 = mutationOperator.AddConnectionMutation(genome, -1, 1);
        Console.WriteLine("After connection addition:");
        PrintGenome(genome);
        
        // Add a new connection
        var res_addconn5 = mutationOperator.AddConnectionMutation(genome, -1, 1);
        Console.WriteLine("After connection addition:");
        PrintGenome(genome);
        
        // Add a new connection
        var res_addconn6 = mutationOperator.AddConnectionMutation(genome, -1, 1);
        Console.WriteLine("After connection addition:");
        PrintGenome(genome);
        
        // Add a new connection
        var res_addconn7 = mutationOperator.AddConnectionMutation(genome, -1, 1);
        Console.WriteLine("After connection addition:");
        PrintGenome(genome);
        
        // Add a new connection
        var res_addconn8 = mutationOperator.AddConnectionMutation(genome, -1, 1);
        Console.WriteLine("After connection addition:");
        PrintGenome(genome);

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