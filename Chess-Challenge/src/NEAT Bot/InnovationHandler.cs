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
    public Dictionary<Tuple<int, int>, int> NodeIdMapping = new();
    public Dictionary<Tuple<int, int>, int> ConnectionIdMapping = new();

    public InnovationHandler(int numInputs, int numOutputs) {
        _curNodeId = numInputs + numOutputs;
    }

    public int GetNextOrganismId() {
        var curId = _curOrganismId;
        _curOrganismId++;
        return curId;
    }
    
    public int AssignNodeId(Tuple<int, int> source) {
        int assignedId;
        if (NodeIdMapping.TryGetValue(source, out var value)) {
            // If the source connection is already in the map, use the same innovation number
            assignedId = value;
        } else {
            // If not, get a new innovation number and add it to the map
            assignedId = _curNodeId;
            NodeIdMapping[source] = assignedId;
            _curNodeId++;
        }
        return assignedId;
    }
    
    public int AssignConnectionId(Tuple<int, int> connection) {
        if (ConnectionIdMapping.TryGetValue(connection, out var value)) {
            // If the connection is already in the map, return its ID
            return value;
        } else {
            // If not, create a new ID and add it to the map
            int newId = _curConnectionId;
            ConnectionIdMapping[connection] = newId;
            _curConnectionId++;
            return newId;
        }
    }
}