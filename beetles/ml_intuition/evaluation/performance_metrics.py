"""
All metrics that are calculated on the model's output.
"""
from typing import Dict, List

import numpy as np
from sklearn import metrics
from sklearn.metrics import confusion_matrix

from ml_intuition.data import utils


def mean_per_class_accuracy(y_true: np.ndarray,
                            y_pred: np.ndarray) -> np.ndarray:
    """
    Calculate mean per class accuracy based on the confusion matrix.

    :param y_true: Labels as a one-dimensional numpy array.
    :param y_pred: Model's predictions as a one-dimensional numpy array.
    """
    conf_matrix = confusion_matrix(y_true, y_pred)
    return conf_matrix.diagonal() / conf_matrix.sum(axis=1)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, metrics: list) -> \
        Dict[str, List[float]]:
    """
    Compute all metrics on predicted labels and labels.

    :param y_true: Labels as a one-dimensional numpy array.
    :param y_pred: Model's predictions as a one-dimensional numpy array.
    :param metrics: List of metrics functions.
    """
    return {metric_function.__name__:
                [metric_function(y_true, y_pred)] for metric_function in
            metrics}


DEFAULT_METRICS = [
    metrics.accuracy_score,
    metrics.balanced_accuracy_score,
    metrics.cohen_kappa_score,
    mean_per_class_accuracy,
]

DEFAULT_FAIR_METRICS = [
    metrics.accuracy_score,
    metrics.balanced_accuracy_score,
    metrics.cohen_kappa_score
]


def get_model_metrics(y_true, y_pred, metrics_to_compute: List = None) \
        -> Dict[str, List[float]]:
    """
    Calculate provided metrics and store them in a Dict
    :param y_true: True labels
    :param y_pred: Predicted labels
    :param inference_time: Prediction time, defaults to None
    :param metrics_to_compute: Metrics which will be computed, defaults to None
    :return: Dictionary with metric name as key and metric value as value
    """
    metrics_to_compute = DEFAULT_METRICS if metrics_to_compute is None else \
        metrics_to_compute
    model_metrics = compute_metrics(y_true=y_true,
                                    y_pred=y_pred,
                                    metrics=metrics_to_compute)
    if mean_per_class_accuracy.__name__ in model_metrics:
        per_class_acc = {'Class_' + str(i):
                             [item] for i, item in enumerate(
            *model_metrics[mean_per_class_accuracy.__name__])}
        model_metrics.update(per_class_acc)
        model_metrics = utils.restructure_per_class_accuracy(model_metrics)
    return model_metrics


def get_fair_model_metrics(conf_matrix, labels_in_train) -> Dict[str, List[float]]:
    """
    Recalculate model metrics discarding classes which where not present in the
    training set
    :param conf_matrix: Original confusion matrix containing all classes
    :param labels_in_train: Labels which were present in the training set
    :return: Recalculated metrics as Dict
    """
    conf_matrix = conf_matrix[labels_in_train, :]
    conf_matrix = conf_matrix[:, labels_in_train]
    all_preds = []
    all_targets = []
    for row_id in range(conf_matrix.shape[0]):
        preds = []
        targets = []
        for column_id in range(conf_matrix.shape[1]):
            for i in range(int(conf_matrix[row_id, column_id])):
                preds.append(column_id)
            targets = [row_id for _ in range(len(preds))]
        all_preds.append(preds)
        all_targets.append(targets)
    y_pred = np.concatenate(all_preds, axis=0)
    y_true = np.concatenate(all_targets, axis=0)
    return get_model_metrics(y_true, y_pred,
                             metrics_to_compute=DEFAULT_FAIR_METRICS)
