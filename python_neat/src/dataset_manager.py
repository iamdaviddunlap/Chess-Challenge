import numpy as np
import torch
import matplotlib.pyplot as plt


class DatasetManager:
    _instance = None
    _xor_dataset = None
    _concentric_circle_dataset = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatasetManager, cls).__new__(cls)
        return cls._instance

    def xor_dataset(self, device="cpu"):
        if self._xor_dataset is not None:
            np.random.shuffle(self._xor_dataset)
            return torch.tensor(self._xor_dataset).to(device).float()

        self._xor_dataset = np.array([
            [0, 0, 1, 0],
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 1, 0]
        ])

        np.random.shuffle(self._xor_dataset)
        return torch.tensor(self._xor_dataset).to(device).float()

    def concentric_circle_dataset(self, device="cpu", n_points=50, noise=0.1):
        if self._concentric_circle_dataset is not None:
            np.random.shuffle(self._concentric_circle_dataset)
            return torch.tensor(self._concentric_circle_dataset).to(device).float()

        theta = np.linspace(0, 2 * np.pi, n_points)
        r_inner = 1
        r_middle = 2
        r_outer = 3

        # Generate inner circle points
        x_inner = (r_inner + noise * np.random.randn(n_points)) * np.cos(theta)
        y_inner = (r_inner + noise * np.random.randn(n_points)) * np.sin(theta)
        label_inner = np.array([[1, 0, 0]] * n_points)

        # Generate middle circle points
        x_middle = (r_middle + noise * np.random.randn(n_points)) * np.cos(theta)
        y_middle = (r_middle + noise * np.random.randn(n_points)) * np.sin(theta)
        label_middle = np.array([[0, 1, 0]] * n_points)

        # Generate outer circle points
        x_outer = (r_outer + noise * np.random.randn(n_points)) * np.cos(theta)
        y_outer = (r_outer + noise * np.random.randn(n_points)) * np.sin(theta)
        label_outer = np.array([[0, 0, 1]] * n_points)

        # Combine the datasets
        X = np.column_stack((np.concatenate((x_inner, x_middle, x_outer)),
                             np.concatenate((y_inner, y_middle, y_outer))))
        y = np.vstack((label_inner, label_middle, label_outer))

        self._concentric_circle_dataset = np.column_stack((X, y))
        np.random.shuffle(self._concentric_circle_dataset)

        return torch.tensor(self._concentric_circle_dataset).to(device).float()


def plot_concentric_circle_dataset(dataset):
    X = dataset[:, :2]
    y_one_hot = dataset[:, 2:]

    # Convert one-hot encoding to label index (0, 1, or 2)
    y = np.argmax(y_one_hot, axis=1)

    plt.scatter(X[y==0][:, 0], X[y==0][:, 1], label='Inner Circle', c='b')
    plt.scatter(X[y==1][:, 0], X[y==1][:, 1], label='Middle Circle', c='g')
    plt.scatter(X[y==2][:, 0], X[y==2][:, 1], label='Outer Circle', c='r')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.legend()
    plt.title('Concentric Circles with Noise')
    plt.show()


if __name__ == '__main__':
    plot_concentric_circle_dataset(DatasetManager().concentric_circle_dataset())
