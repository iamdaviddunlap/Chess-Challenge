from visualize import visualize_genome
from json_converter import genome_to_json
from organism import Organism
from genome import Genome
from mutation_handler import Mutation


def main():
    # Create Genome
    genome1 = Genome()
    organism1 = Organism(genome1)
    Mutation.mutate_genome(genome1)
    Mutation.mutate_genome(genome1)
    Mutation.mutate_genome(genome1)
    Mutation.mutate_genome(genome1)
    Mutation.mutate_add_gate(genome1)
    visualize_genome(organism1.genome)

    genome2 = Genome()
    organism2 = Organism(genome2)
    Mutation.mutate_genome(genome2)
    Mutation.mutate_genome(genome2)
    Mutation.mutate_genome(genome2)
    Mutation.mutate_genome(genome2)
    Mutation.mutate_add_gate(genome2)
    visualize_genome(organism2.genome)

    child1 = organism1.reproduce()
    child2 = organism1.reproduce(organism2)
    visualize_genome(child1.genome)
    visualize_genome(child2.genome)
    x = 1

    # # Create Phenotype
    # genome.create_phenotype()
    #
    # visualize_genome(genome)
    #
    # with open('genome.json', 'w+') as f:
    #     f.write(genome_to_json(genome))
    #
    # # Determine Activation Order
    # genome.determine_activation_order()
    #
    # # Activate the Network
    # result1 = genome.activate([0.0, 0.0, 1.0])
    # genome.reset_state()
    # result2 = genome.activate([1.0, 1.0, 1.0])
    #
    # print("Activations:", genome.activations)


if __name__ == "__main__":
    main()
