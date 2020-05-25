"""
Perform the inference of the model on the testing dataset.
"""

import os

import clize
import numpy as np
import tensorflow as tf
from clize.parameters import multi
from sklearn import metrics

from ml_intuition import enums
from ml_intuition.data import io, transforms, utils
from ml_intuition.data.noise import get_noise_functions
from ml_intuition.data.utils import predict_with_model_in_batches
from ml_intuition.evaluation.performance_metrics import (
    compute_metrics, mean_per_class_accuracy)
from ml_intuition.evaluation.time_metrics import timeit


def evaluate(*,
             data,
             model_path: str,
             dest_path: str,
             n_classes: int,
             noise: ('post', multi(min=0)),
             noise_sets: ('spost', multi(min=0)),
             noise_params: str = None):
    """
    Function for evaluating the trained model.

    :param model_path: Path to the model.
    :param data: Either path to the input data or the data dict.
    :param dest_path: Directory in which to store the calculated matrics
    :param n_classes: Number of classes.
    :param noise: List containing names of used noise injection methods
        that are performed after the normalization transformations.
    :param noise_sets: List of sets that are affected by the noise injecton.
        For this module single element can be "test".
    :param noise_params: JSON containing the parameters
        setting of noise injection methods.
        Examplary value for this parameter: "{"mean": 0, "std": 1, "pa": 0.1}".
        This JSON should include all parameters for noise injection
        functions that are specified in the noise argument.
        For the accurate description of each parameter, please
        refer to the ml_intuition/data/noise.py module.
    """
    if type(data) is str:
        test_dict = io.extract_set(data, enums.Dataset.TEST)
    else:
        test_dict = data[enums.Dataset.TEST]
    min_max_path = os.path.join(os.path.dirname(model_path), "min-max.csv")
    if os.path.exists(min_max_path):
        min_value, max_value = io.read_min_max(min_max_path)
    else:
        min_value, max_value = data[enums.DataStats.MIN], \
            data[enums.DataStats.MAX]
    transformations = [transforms.SpectralTransform(),
                       transforms.OneHotEncode(n_classes=n_classes),
                       transforms.MinMaxNormalize(min_=min_value, max_=max_value)]
    transformations = transformations + get_noise_functions(noise, noise_params) \
        if enums.Dataset.TEST in noise_sets else transformations

    for f_transform in transformations:
        test_dict[enums.Dataset.DATA], test_dict[enums.Dataset.LABELS] = \
            f_transform(test_dict[enums.Dataset.DATA],
                        test_dict[enums.Dataset.LABELS])

    model = tf.keras.models.load_model(model_path, compile=True)
    predict = timeit(predict_with_model_in_batches)
    y_pred, inference_time = predict(model, test_dict[enums.Dataset.DATA])

    y_true = np.argmax(test_dict[enums.Dataset.LABELS], axis=-1)

    custom_metrics = [
        metrics.accuracy_score,
        metrics.balanced_accuracy_score,
        metrics.cohen_kappa_score,
        mean_per_class_accuracy,
        metrics.confusion_matrix
    ]
    model_metrics = compute_metrics(y_true=y_true,
                                    y_pred=y_pred,
                                    metrics=custom_metrics)
    model_metrics['inference_time'] = [inference_time]
    per_class_acc = {'Class_' + str(i):
                     [item] for i, item in enumerate(
        *model_metrics[mean_per_class_accuracy.__name__])}
    model_metrics.update(per_class_acc)

    np.savetxt(os.path.join(dest_path,
                            metrics.confusion_matrix.__name__ + '.csv'),
               *model_metrics[metrics.confusion_matrix.__name__], delimiter=',',
               fmt='%d')

    del model_metrics[metrics.confusion_matrix.__name__]
    model_metrics = utils.restructure_per_class_accuracy(model_metrics)

    io.save_metrics(dest_path=dest_path,
                    file_name=enums.Experiment.INFERENCE_METRICS,
                    metrics=model_metrics)


if __name__ == '__main__':
    clize.run(evaluate)
