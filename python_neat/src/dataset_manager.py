import numpy as np


class DatasetManager:
    _instance = None
    _dataset = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatasetManager, cls).__new__(cls)
        return cls._instance

    def xor_dataset(self):
        if self._dataset is not None:
            np.random.shuffle(self._dataset)
            return self._dataset

        # Create the XOR truth table dataset with a bias bit
        self._dataset = np.array([
            [0, 0, 1, 0],
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 1, 0]
        ])

        np.random.shuffle(self._dataset)
        return self._dataset
