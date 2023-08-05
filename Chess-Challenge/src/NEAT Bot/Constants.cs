namespace Chess_Challenge.NEAT_Bot; 

public static class Constants {
    public const int PopulationSize = 20;
    public const int InputsCount = 3;
    public const int OutputsCount = 1;
    public const double MinVal = -99.999;
    public const double MaxVal = 99.999;

    public const int NumHallOfFameParasites = 8;
    public const int NumChampionParasites = 4;

    public const double MutateWeightsProb = 0.8;
    public const double AddConnectionProb = 0.3;
    // public const double AddNodeProb = 0.01;  // This is the val from Ken Stanley, I'm increasing for testing
    public const double AddNodeProb = 0.3;
    public const double WeightPerturbChance = 0.9;
    public const double WeightPerturbValue = 2.5;

    // A difference of 1.0 in weights is like having 2 genes not shared between the organisms
    public const double DisjointCoeff = 2.0;
    public const double ExcessCoeff = 2.0;
    public const double WeightCoeff = 1.0;
}