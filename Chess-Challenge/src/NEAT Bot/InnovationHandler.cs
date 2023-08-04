using System;
using System.Collections.Generic;

namespace Chess_Challenge.NEAT_Bot; 

/**
 * This class should be created as a singleton and passed into each Organism
 */
public class InnovationHandler {
    private int _curOrganismId = 0;
    private int _curNodeId = 0;
    private int _curConnectionId = 0;
    public Dictionary<int, int> NodeIdMapping = new();  // This map has keys as the source connection and values as the corresponding nodeId
    public Dictionary<Tuple<int, int>, int> ConnectionIdMapping = new();  // This map has keys as a tuple of (inputId, outputId) and values as the corresponding connectionId

    public InnovationHandler() { }

    public int GetNextOrganismId() {
        var curId = _curOrganismId;
        _curOrganismId++;
        return curId;
    }
    
    public int GetNextNodeId() {
        var curId = _curNodeId;
        _curNodeId++;
        return curId;
    }
    
    public int GetNextConnectionId() {
        var curId = _curConnectionId;
        _curConnectionId++;
        return curId;
    }
}