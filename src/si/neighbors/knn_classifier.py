
import numpy as np
import sys
PATHS = ["../data", "../metrics", "../statistics"]
sys.path.extend(PATHS)
from accuracy import accuracy
from dataset import Dataset
from distances import euclidean_distance
from typing import Callable, Union

class KNNClassifier:

    """
    Implements the K-Nearest Neighbors classifier. Distances between test examples and examples
    present in the training data can be computed using one of two distinct formulas:
        - euclidean_distance: sqrt(SUM[(pi - qi)^2])
        - manhattan_distance: SUM[abs(pi - qi)]
    """

    def __init__(self, k: int = 4, weighted: bool = False, distance: Callable = euclidean_distance):
        """
        Implements the K-Nearest Neighbors classifier. Distances between test examples and examples
        present in the training data can be computed using one of two distinct formulas:
            - euclidean_distance: sqrt(SUM[(pi - qi)^2])
            - manhattan_distance: SUM[abs(pi - qi)]

        Parameters
        ----------
        k: int (default=4)
            Number of neighbors to be used
        weighted: bool (default=False)
            Whether to weigh closest neighbors when predicting labels
        distance: callable (default=euclidean_distance)
            Function used to compute the distances

        Attributes
        ----------
        fitted: bool
            Whether the model is already fitted
        weights_vector: np.ndarray
            The weights to give to each closest neighbor when predicting labels (only applicable
            when 'weights' is True)
        dataset: Dataset
            A Dataset object (training data)
        """
        # parameters
        if k < 1:
            raise ValueError("The value of 'k' must be greater than 0.")
        self.k = k
        self.weighted = weighted
        self.distance = distance
        # attributes
        self.fitted = False
        if self.weighted:
            self.weights_vector = np.arange(self.k,0,-1)
        self.dataset = None

    def fit(self, dataset: Dataset) -> "KNNClassifier":
        """
        Stores the training dataset. Returns self.

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (training data)
        """
        self.dataset = dataset
        self.fitted = True
        return self

    def _get_closest_label(self, sample: np.ndarray) -> Union[int, str]:
        """
        Returns the predicted label of the sample given as input. The label is determined by
        majority vote over the labels of the sample's <self.k> closest neighbors.

        Parameters
        ----------
        sample: np.ndarray
            The sample to be assigned to a label
        """
        # compute the distances between a sample and each example in the training dataset
        distances = self.distance(sample, self.dataset.X)
        # determine the indexes of the <k> nearest examples
        k_nearest_neighbors = np.argsort(distances)[:self.k]
        # get the classes corresponding to the previous indexes
        knn_labels = self.dataset.y[k_nearest_neighbors]
        # transform labels vector to account for weights (if applicable)
        if self.weighted:
            knn_labels = np.repeat(knn_labels, self.weights_vector)
        # get the most frequent class in the selected <k> examples
        labels, counts = np.unique(knn_labels, return_counts=True)
        return labels[np.argmax(counts)]

    def predict(self, dataset: Dataset) -> np.ndarray:
        """
        Predicts and returns the labels of the dataset given as input.

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (testing data)
        """
        if not self.fitted:
            raise Warning("Fit 'KNNClassifier' before calling 'predict'.")
        return np.apply_along_axis(self._get_closest_label, axis=1, arr=dataset.X)

    def score(self, dataset: Dataset) -> float:
        """
        Calculates the error between the predicted and true classes. To compute the error, it
        uses the accuracy score: (TP+TN)/(TP+FP+TN+FN). Returns the accuracy score.
    
        Parameters
        ----------
        dataset: Dataset
            A Dataset object (testing data)
        """
        if not self.fitted:
            raise Warning("Fit 'KNNClassifier' before calling 'score'.")
        y_pred = self.predict(dataset)
        return accuracy(dataset.y, y_pred)


if __name__ == "__main__":

    TEST_PATHS = ["../io", "../model_selection"]
    sys.path.extend(TEST_PATHS)
    from csv_file import read_csv_file
    from distances import manhattan_distance
    from split import train_test_split

    print("EX1")
    ds = Dataset.from_random(n_examples=10, n_features=10, label=True, seed=0)
    print(ds.get_classes())
    trn, tst = train_test_split(dataset=ds, test_size=0.3, random_state=42)
    knn = KNNClassifier(k=3, weighted=False, distance=manhattan_distance)
    knn.fit(trn)
    y_pred = knn.predict(tst)
    #print(y_pred)
    accuracy_score = knn.score(tst)
    print(f"Accuracy score: {accuracy_score*100:.2f}%")

    print("\nEX2 - iris")
    path_to_file = "../../../datasets/iris/iris.csv"
    iris = read_csv_file(file=path_to_file, sep=",", features=True, label=True)
    print(iris.get_classes())
    iris_trn, iris_tst = train_test_split(dataset=iris, test_size=0.3, random_state=42)
    iris_knn = KNNClassifier(k=4, weighted=True, distance=euclidean_distance)
    iris_knn.fit(iris_trn)
    y_iris_pred = iris_knn.predict(iris_tst)
    #print(y_iris_pred)
    iris_score = iris_knn.score(iris_tst)
    print(f"Accuracy score: {iris_score*100:.2f}%")

