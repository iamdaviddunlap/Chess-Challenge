namespace Chess_Challenge.NEAT_Bot; 

public static class Constants {
    public const int PopulationSize = 50;
    public const int InputsCount = 3;
    public const int OutputsCount = 1;
    public const double MinVal = -99.999;
    public const double MaxVal = 99.999;
    // public const double MinVal = -1.999;
    // public const double MaxVal = 1.999;


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

    public static double SpeciesCompatThresh = 6.0;  // Ken Stanley set this to 6.0
    public const double SpeciesCompatModifier = 0.3; // TOD0 use this; every generation the SpeciesCompatThresh is adjusted by this much
    public const int SpeciesCountTarget = 10;  // I haven't tuned this

    public const double FitnessRewardWin = 2.0;
    public const double FitnessRewardDraw = 1.0;
    public const double FitnessRewardLoss = 0.0;

    public const int MinAsexualOffspring = 3;
    public const double SpeciesElitePercentage = 0.2;
    public const double InheritDisableChance = 0.75;

    public const double MateMultipointProb = 0.6;  // Ken Stanley used 0.6
    public const double MateMultipointAvgProb = 0.2;  // Ken Stanley used 0.4
    public const double MateSinglepointProb = 0.2; // Ken Stanley used 0, ie turned this off
}