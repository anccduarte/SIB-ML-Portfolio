
import numpy as np
import sys
sys.path.append("../data")
from dataset import Dataset
from split import train_test_split
from typing import Callable

def cross_validate(model,
                   dataset: Dataset,
                   cv: int = 5,
                   test_size: float = 0.3,
                   scoring: Callable = None) -> dict:
    """
    Implements a k-fold cross-validation algorithm. Each fold is established randomly. Returns a
    dictionary containing 3 keys:
    1. seeds: The seeds used in the train-test split
    2. train: The scores attained with training data
    3. test: The scores obtained with testing data

    Parameters
    ----------
    model: estimator
        An instance of a classifier/regressor
    dataset: Dataset
        A Dataset object
    cv: int (default=5)
        The number of folds used in cross-validation
    test_size: float (default=0.3)
        The proportion of the dataset to be used for testing
    scoring: callable (default=None)
        The scoring function used to evaluate the performance of the model (if None, uses the
        model's scoring function)
    """
    scores = {"seeds": [], "train": [], "test": []}
    for i in range(cv):
        # generate seed for train_test_split and add it to scores
        seed = np.random.randint(0, 1000)
        scores["seeds"] += [seed]
        # split data in train and test
        ds_train, ds_test = train_test_split(dataset=dataset, test_size=test_size, random_state=seed)
        # fit the model on training data
        model.fit(ds_train)
        # if scoring is None, use the model's scoring function
        if scoring is None:
            train_score = model.score(ds_train)
            test_score = model.score(ds_test)
        # otherwise, use the provided scoring function
        else:
            train_score = score(ds_train.y, model.predict(ds_test))
            test_score = score(ds_test.y, model.predict(ds_test))
        # add train_score and test_score to scores
        scores["train"] += [train_score]
        scores["test"] += [test_score]
    return scores


if __name__ == "__main__":

    TEST_PATHS = ["../io", "../linear_model", "../metrics", "../statistics"]
    sys.path.extend(TEST_PATHS)
    # from accuracy import accuracy
    from csv_file import read_csv_file
    from logistic_regression import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    path_to_file = "../../../datasets/breast/breast-bin.csv"
    breast = read_csv_file(file=path_to_file, sep=",", features=False, label=True)
    breast.X = StandardScaler().fit_transform(breast.X)
    
    model = LogisticRegression()
    cv = cross_validate(model=model, dataset=breast) # scoring=accuracy
    print(f"Cross-validation seeds and scores:\n{cv}")
    print(f"Mean score on trainig data: {np.mean(cv['train'])*100:.2f}%")
    print(f"Mean score on testing data: {np.mean(cv['test'])*100:.2f}%")

