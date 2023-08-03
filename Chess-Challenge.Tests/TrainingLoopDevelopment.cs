using Chess_Challenge.NEAT_Bot;

namespace Chess_Challenge.Tests; 

public class TrainingLoopDevelopment {
    [Fact] // This attribute signifies that the method below is a test
    public void MainTest() {
        Trainer.RunTraining(maxGenerations: 1);
    }
    

}