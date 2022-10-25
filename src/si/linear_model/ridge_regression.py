
import numpy as np
import sys
PATHS = ["../data", "../metrics"]
sys.path.extend(PATHS)
from dataset import Dataset
from mse import mse
from typing import Union

class RidgeRegression:

    """
    RidgeRegression is a linear model using the L2 regularization.
    This model solves the linear regression problem using an adapted Gradient Descent technique.
    """

    def __init__(self, l2_penalty: float, alpha: float, max_iter: int, tolerance: Union[int, float], adaptative_alpha: bool):
        """
        RidgeRegression is a linear model using the L2 regularization.
        This model solves the linear regression problem using an adapted Gradient Descent technique.

        Parameters
        ----------
        l2_penalty: float
            The L2 regularization parameter
        alpha: float
            The learning rate
        max_iter: int
            The maximum number of iterations
        tolerance: int | float
            Tolerance for stopping gradient descent
        adaptative_alpha: bool
            Whether an adaptative alpha is used in the gradient descent

        Attributes
        ----------
        fitted: bool
            Whether the model is already fitted
        theta: np.ndarray
            Model parameters, namely the coefficients of the linear model
            For example, x0 * theta[0] + x1 * theta[1] + ...
        theta_zero: float
            Model parameter, namely the intercept of the linear model
            For example, theta_zero * 1
        cost_history: dict
            A dictionary containing the values of the cost function (J function) at each iteration
            of the algorithm (gradient descent)
        """
        # parameters
        if l2_penalty <= 0:
            raise ValueError("The value of 'l2_penalty' must be positive.")
        if alpha <= 0:
            raise ValueError("The value of 'alpha' must be positive.")
        if max_iter < 1:
            raise ValueError("The value of 'max_iter' must be a positive integer.")
        if tolerance <= 0:
            raise ValueError("The value of 'tolerance' must be positive.")
        self.l2_penalty = l2_penalty # lambda
        self.alpha = alpha
        self.max_iter = max_iter
        self.tolerance = tolerance
        self.adaptative_alpha = adaptative_alpha
        # attributes
        self.fitted = False
        self.theta = None
        self.theta_zero = None
        self.cost_history = {}

    def _gradient_descent_iter(self, dataset: Dataset, m: int) -> None:
        """
        Performs one iteration of the gradient descent algorithm. The algorithm goes as follows:
        1. Predicts the outputs of the dataset
            -> X @ theta + theta_zero
        2. Computes the gradient vector and adjusts it according to the value of alpha
            -> (alpha / m) * (y_pred - y_true) @ X
        3. Computes the penalization term
            -> alpha * (l2 / m)
        4. Updates theta
            -> theta = theta - gradient - penalization
        5. Updates theta_zero
            -> theta_zero = theta_zero - (alpha / m) * SUM[y_pred - y_true] * X(0), X(0) = [1,1,...,1]

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (the dataset to fit the model to)
        m: int
            The number of rows of the Dataset object
        """
        # predicted y
        y_pred = np.dot(dataset.X, self.theta) + self.theta_zero
        # computing the gradient vector given a learning rate alpha
        # vector of shape (n_features,) -> gradient[k] updates self.theta[k]
        gradient = (self.alpha / m) * np.dot(y_pred - dataset.y, dataset.X)
        # computing the penalization term
        penalization_term = self.theta * self.alpha * (self.l2_penalty / m)
        # updating the model parameters (theta and theta_zero)
        self.theta = self.theta - gradient - penalization_term
        self.theta_zero = self.theta_zero - (self.alpha * (1 / m)) * np.sum(y_pred - dataset.y)

    def _regular_fit(self, dataset: Dataset) -> "RidgeRegression":
        """
        Fits the model to the dataset. Does not update the learning rate (self.alpha). Covergence is attained 
        whenever the difference of cost function values between iterations is less than self.tolerance.
        Returns self (fitted model).

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (the dataset to fit the model to)
        """
        # get the shape of the dataset
        m, n = dataset.shape()
        # initialize the model parameters (it can be initialized randomly using a range of values)
        self.theta = np.zeros(n)
        self.theta_zero = 0
        # main loop -> gradient descent
        i = 0
        converged = False
        while i < self.max_iter and not converged:
            # compute gradient descent iteration (update model parameters)
            self._gradient_descent_iter(dataset, m)
            # add new entry to self.cost_history
            self.cost_history[i] = self.cost(dataset)
            # verify convergence
            converged = abs(self.cost_history[i] - self.cost_history.get(i-1, np.inf)) < self.tolerance
            i += 1
        return self

    def _adaptative_fit(self, dataset: Dataset) -> "RidgeRegression":
        """
        Fits the model to the dataset. Updates the learning rate (self.alpha), by halving it every
        time the difference of cost function values between iterations is less than self.tolerance.
        Returns self (fitted model).

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (the dataset to fit the model to)
        """
        # get the shape of the dataset
        m, n = dataset.shape()
        # initialize the model parameters (it can be initialized randomly using a range of values)
        self.theta = np.zeros(n)
        self.theta_zero = 0
        # main loop -> gradient descent
        for i in range(self.max_iter):
            # compute gradient descent iteration (update model parameters)
            self._gradient_descent_iter(dataset, m)
            # add new entry to self.cost_history
            self.cost_history[i] = self.cost(dataset)
            # update learning rate
            is_lower = abs(self.cost_history[i] - self.cost_history.get(i-1, np.inf)) < self.tolerance
            if is_lower: self.alpha //= 2
        return self

    def fit(self, dataset: Dataset) -> "RidgeRegression":
        """
        Fits the model to the dataset. If self.adaptative_alpha is True, fits the model by updating the
        learning rate (alpha). Returns self (fitted model).

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (the dataset to fit the model to)
        """
        self.fitted = True
        return self._adaptative_fit(dataset) if self.adaptative_alpha else self._regular_fit(dataset)

    def predict(self, dataset: Dataset) -> np.ndarray:
        """
        Predicts and returns the output of the dataset.

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (the dataset to predict the output of)
        """
        if not self.fitted:
            raise Warning("Fit 'RidgeRegression' before calling 'predict'.")
        return np.dot(dataset.X, self.theta) + self.theta_zero

    def score(self, dataset: Dataset) -> float:
        """
        Computes and returns the Mean Square Error (MSE) of the model on the dataset.

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (the dataset to compute the MSE on)
        """
        if not self.fitted:
            raise Warning("Fit 'RidgeRegression' before calling 'score'.")
        y_pred = self.predict(dataset)
        return mse(dataset.y, y_pred)

    def cost(self, dataset: Dataset) -> float:
        """
        Computes and returns the value of the cost function (J function) of the model on the dataset
        using L2 regularization.

        Parameters
        ----------
        dataset: Dataset
            A Dataset object (the dataset to compute the cost function on)
        """
        if not self.fitted:
            raise Warning("Fit 'RidgeRegression' before calling 'cost'.")
        y_pred = self.predict(dataset)
        return (np.sum((y_pred - dataset.y) ** 2) + (self.l2_penalty * np.sum(self.theta ** 2))) / (2 * len(dataset.y))


if __name__ == "__main__":

    TEST_PATHS = ["../io", "../model_selection"]
    sys.path.extend(TEST_PATHS)
    from csv_file import read_csv_file
    from sklearn.preprocessing import StandardScaler
    from split import train_test_split

    path_to_file = "../../../datasets/cpu/cpu.csv"
    cpu = read_csv_file(file=path_to_file, sep=",", features=True, label=True)
    cpu.X = StandardScaler().fit_transform(cpu.X)
    cpu_trn, cpu_tst = train_test_split(cpu, test_size=0.3, random_state=2)
    cpu_ridge = RidgeRegression(l2_penalty=1, alpha=0.001, max_iter=2000, tolerance=1, adaptative_alpha=True)
    cpu_ridge = cpu_ridge.fit(cpu_trn)
    predictions = cpu_ridge.predict(cpu_tst)
    print(predictions)

