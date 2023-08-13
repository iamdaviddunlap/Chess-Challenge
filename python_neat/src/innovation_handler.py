from constants import Constants


class InnovationHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InnovationHandler, cls).__new__(cls)
            cls._curOrganismId = 0
            cls._curNodeId = Constants.inputs_count + Constants.outputs_count
            cls._curConnectionId = 0
            cls.node_id_mapping = {}
            cls.connection_id_mapping = {}
        return cls._instance

    def get_next_organism_id(self):
        cur_id = self._curOrganismId
        self._curOrganismId += 1
        return cur_id

    def assign_node_id(self, source):
        if source in self.node_id_mapping:
            assigned_id = self.node_id_mapping[source]
        else:
            assigned_id = self._curNodeId
            self._curNodeId += 1

            if source is not None:
                self.node_id_mapping[source] = assigned_id

        return assigned_id

    def assign_connection_id(self, connection):
        if connection in self.connection_id_mapping:
            return self.connection_id_mapping[connection]
        else:
            new_id = self._curConnectionId
            self.connection_id_mapping[connection] = new_id
            self._curConnectionId += 1
            return new_id
