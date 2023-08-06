using System;
using System.Collections.Generic;
using System.Linq;

namespace Chess_Challenge.NEAT_Bot; 

public static class GameController {

    ///  Play game between two players. The return value is the fitness reward for the host
    public static int PlayGame(Organism host, Organism parasite, bool hostIsWhite, Random random) {
        int result;
        
        // result = hostIsWhite ? PlayChess(host, parasite) : PlayChess(parasite, host);
        //
        // // Reverse the score if the host is playing as the black player
        // if (!hostIsWhite) {
        //     result = -result;
        // }
        // result = PlayRandom(host, parasite, random);  // TODO don't use PlayRandom!
        result = PlayXOR(host, parasite, random);  // TODO don't use PlayXOR!
        
        return result;
    }

    /// Simulate a game of chess. Returns 1 if white wins, 0 if draw, -1 if black wins
    private static int PlayChess(Organism whitePlayer, Organism blackPlayer) {
        return -1;  // TODO implement PlayChess
    }

    public static double XORSinglePlayer(Organism player, Random random) {
        // Define XOR dataset.
        List<Tuple<double[], double[]>> dataset = new List<Tuple<double[], double[]>> {
    new Tuple<double[], double[]>(new double[] {0.7579625669778175}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.372636837782547}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.622349546980271}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.21370213815850958}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.5970092294881852}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.8301403938249521}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.18734369772657078}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.4490036206275461}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.9485769258278152}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.21234857899201987}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.2130269367916422}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.23747986677422647}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.2524722458110579}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.9047708891297063}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.6470601264958944}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.10054030014412517}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.7756207440157152}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.0792497884788155}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.12452857741354606}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.29423554002937397}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.6505689594777663}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.271895206950328}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.205954694016731}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.06884377696219492}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.2745381192373534}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {1.1137340322456202}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.021461369426508045}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {1.4389513859268985}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.12514358096746156}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.1524418601903789}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.32867033888793007}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.09336693592329179}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.2449350432079899}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.2897719278936823}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.39244439026163935}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.8787573133895367}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.49091939590150024}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.4747793048902432}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.6597907773773435}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.9887842112631492}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.4790342936896753}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.09633829996327607}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.07039521444807212}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.24574360487647484}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.8610133014479161}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.3986348722854537}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.21100434003053878}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.09748633755558918}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {-0.05946056823311747}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {0.39556196062403665}, new double[] {1.0, 0.0}),
    new Tuple<double[], double[]>(new double[] {2.3437858918237553}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.610444168828941}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.708423016406377}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {0.9867763820081217}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.5777826259861256}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.1839772746801707}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.516519459755261}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.890858230235432}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.1189671395547496}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.8430586390580235}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.9381066280312946}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.704420115640428}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.8206149801174851}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.8978153596600564}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.5197872478870584}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.599434675037712}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.9587045132793142}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.051093525793219}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.263451479399853}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.9352250981835968}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.9184320580132121}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.6801795056604822}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.7042910845093109}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.6322371739550565}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.083015118531693}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.3516085480507}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.6712184184085777}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.236026982522783}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.7976925801844903}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.1151354183127067}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.9411709821728722}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.03082187774426}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.5734201586348058}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.5508422329129368}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.6974331068124933}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.187219738652468}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.4594986499737317}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.0812464201159275}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.760523405386325}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.1960165536446579}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.7591463618131893}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.9324850930744275}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {3.0908535629259517}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.169880244518054}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.0344473497596436}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.5944766679493227}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {1.5885227182081954}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {0.8552883807502583}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.2731567593677138}, new double[] {0.0, 1.0}),
    new Tuple<double[], double[]>(new double[] {2.0061673646897065}, new double[] {0.0, 1.0}),
    };

        // Randomize the dataset order.
        dataset = dataset.OrderBy(x => random.Next()).ToList();
        
        // Track score of the player.
        double playerLoss = 0.0;

        // Iterate over dataset.
        foreach (var item in dataset) {
            var inputs = item.Item1;
            var correctOutput = item.Item2;

            // Activate genomes with inputs and calculate the absolute difference from correct XOR output.
            var playerOutput = player.Genome.Activate(inputs);

            for (int i = 0; i < correctOutput.Length; i++) {
                playerLoss += Math.Abs(correctOutput[i] - playerOutput[i]);
            }
        }

        return playerLoss;
    }

    private static int PlayXOR(Organism hostPlayer, Organism parasitePlayer, Random random) {

        double hostLoss = XORSinglePlayer(hostPlayer, random);
        double parasiteLoss = XORSinglePlayer(parasitePlayer, random);

        // Return 1 if host player is closer to correct XOR output, -1 otherwise.
        if (Math.Abs(hostLoss - parasiteLoss) < 0.0001) {
            return 0;
        }
        if (hostLoss < parasiteLoss) {
            return 1;
        }
        return -1;
    }
    
    private static int PlayRandom(Organism hostPlayer, Organism parasitePlayer, Random random) {
        return random.Next(-1, 2);  // Generates random numbers -1, 0, or 1
    }
}