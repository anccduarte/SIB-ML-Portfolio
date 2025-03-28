
import numpy as np
import sys
sys.path.append("../data")
from copy import deepcopy
from cross_validate import cross_validate
from dataset import Dataset
from typing import Callable


# -- CHECK PARAMETERS

def check_params(dataset: Dataset, cv: int, n_iter: int, test_size: float):
    """
    Checks the values of numeric parameters.

    Parameters
    ----------
    dataset: Dataset
        A Dataset object
    cv: int
        The number of folds used in cross-validation
    n_iter: int
        The number of random hyperparameter combinations to test
    test_size: float
        The proportion of the dataset to be used for testing
    """
    if cv < 1 or cv > dataset.shape()[0]:
        raise ValueError("The value of 'cv' must be an integer belonging to [1, dim_0(dataset)].")
    if n_iter < 1:
        raise ValueError("The value of 'n_iter' must be a positive integer.")
    if test_size <= 0 or test_size >= 1:
        raise ValueError("The value of 'test_size' must be in (0, 1).")


# -- RANDOMIZED-SEARCH

def randomized_search_cv(model: "estimator",
                         dataset: Dataset,
                         parameter_distribution: dict,
                         cv: int = 5,
                         random_state: int = None,
                         n_iter: int = 10,
                         test_size: float = 0.3,
                         scoring: Callable = None) -> list[dict]:
    """
    Implements a randomized search algorithm with cross-validation for hyperparameter optimization.
    Contrary to grid-search, it uses a fixed number of hyperparameter combinations randomly sampled
    from an hyperparameter distribution. Returns a list of dictionaries, each representing one
    combination of hyperparameters. Each dictionary contains 4 keys:
    1. seeds: The seeds used in the train-test split
    2. train: The scores attained with training data
    3. test: The scores obtained with testing data
    4. parameters: The combination of hyperparameters

    Parameters
    ----------
    model: estimator
        An instance of a classifier/regressor
    dataset: Dataset
        A Dataset object
    parameter_distribution: dict
        Dictionary with the names of the parameters to be tested as keys, and lists of parameter
        settings to try as values
    cv: int (default=5)
        The number of folds used in cross-validation
    random_state: int (default=None)
        Controls seed generation for splitting the data and rules hyperparameter choice over a
        distribution of hyperparameters (allows for reproducible output). If 'int', all combinations
        of hyperparameters are tested using the same train-test split when cross-validating the model.
        In this case, distinct choices of hyperparameter combinations between iterations are ensured
        by doing random_state := random_state + 1 every time the model is cross-validated
    n_iter: int (default=10)
        The number of random hyperparameter combinations to test
    test_size: float (default=0.3)
        The proportion of the dataset to be used for testing
    scoring: callable (default=None)
        Scoring function used to evaluate the performance of the model (if None, uses the model's
        scoring function)
    """
    # check values of numeric parameters
    check_params(dataset, cv, n_iter, test_size)
    # check if the model has all the parameters in parameter_distribution
    for param in parameter_distribution:
        if not hasattr(model, param):
            e_msg = f"The model {model.__class__.__name__} does not have the parameter '{param}'."
            raise AttributeError(e_msg)
    # initialize scores -> to return
    scores = []
    # cross-validate the model <n_iter> times
    for i in range(n_iter):
        # initilize new instance of 'model' (deepcopy) at each iteration
        Model = deepcopy(model)
        # initialize 'parameters' -> add to scores
        parameters = {}
        # initialize seed for choosing hyperparameters (if 'int', random_state += 1)
        seed_hyper = random_state if random_state is None else random_state + i
        # set parameter configuration to cross-validate the model, and add it to parameters
        for param in parameter_distribution:
            value = np.random.RandomState(seed=seed_hyper).choice(parameter_distribution[param])
            setattr(Model, param, value)
            parameters[param] = value
        # cross-validate the model
        score = cross_validate(Model, dataset, cv, random_state, test_size, scoring)
        # add the parameter configuration to score (new key)
        score["parameters"] = parameters
        # add the score to scores
        scores += [score]
    return scores


if __name__ == "__main__":

    TEST_PATHS = ["../io", "../linear_model"]
    sys.path.extend(TEST_PATHS)
    from csv_file import read_csv_file
    from logistic_regression import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    def print_scores(scores):
        for score in scores:
            print(f"Hyperparameters: {score['parameters']}")
            print(f"Mean score on trainig data: {np.mean(score['train'])*100:.2f}%")
            print(f"Mean score on testing data: {np.mean(score['test'])*100:.2f}%")
            print("")

    path_to_file = "../../../datasets/breast/breast-bin.csv"
    breast = read_csv_file(file=path_to_file, sep=",", features=False, label=True)
    breast.X = StandardScaler().fit_transform(breast.X)
    
    params = {"l2_penalty": np.linspace(1,10,10),
              "alpha": np.linspace(0.001,0.0001,100),
              "max_iter": np.arange(1000,2000,50)}
    model = LogisticRegression()
    gs = randomized_search_cv(model=model,
                              dataset=breast,
                              parameter_distribution=params,
                              cv=3,
                              random_state=2,
                              n_iter=10,
                              test_size=0.3)
    print_scores(gs)

