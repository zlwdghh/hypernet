"""
All I/O related functions
"""

import csv
import os
from typing import Dict, List, Tuple, Union

import h5py
import numpy as np
from libtiff import TIFF
import tensorflow as tf

import ml_intuition.enums as enums


def save_metrics(dest_path: str, file_name: str, metrics: Dict[str, List]):
    """
    Save given dictionary of metrics.

    :param dest_path: Destination path.
    :param file_name: Name to save the file.
    :param metrics: Dictionary containing all metrics.
    """
    with open(os.path.join(dest_path, file_name), 'w') as file:
        write = csv.writer(file)
        write.writerow(metrics.keys())
        write.writerows(zip(*metrics.values()))


def extract_set(data_path: str, dataset_key: str) -> Dict[str, Union[np.ndarray, float]]:
    """
    Function for loading a h5 format dataset as a dictionary
        of samples, labels, min and max values.

    :param data_path: Path to the dataset.
    :param dataset_key: Key for dataset.
    """
    raw_data = h5py.File(data_path, 'r')
    dataset = {
        enums.Dataset.DATA: raw_data[dataset_key][enums.Dataset.DATA][:],
        enums.Dataset.LABELS: raw_data[dataset_key][enums.Dataset.LABELS][:],
        enums.DataStats.MIN: raw_data.attrs[enums.DataStats.MIN],
        enums.DataStats.MAX: raw_data.attrs[enums.DataStats.MAX]
    }
    raw_data.close()
    return dataset


def load_npy(data_file_path: str, gt_input_path: str) -> Tuple[
        np.ndarray, np.ndarray]:
    """
    Load .npy data and GT from specified paths

    :param data_file_path: Path to the data .npy file
    :param gt_input_path: Path to the GT .npy file
    :return: Tuple with loaded data and GT
    """
    return np.load(data_file_path), np.load(gt_input_path)


def load_satellite_h5(data_file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load hyperspectral cube and ground truth transformation matrix from .h5 file
    :param data_file_path: Path to the .h5 file
    :return: Hyperspectral cube and transformation matrix, both as np.ndarray
    """
    with h5py.File(data_file_path, 'r') as file:
        cube = file[enums.SatelliteH5Keys.CUBE][:]
        cube_to_gt_transform = file[enums.SatelliteH5Keys.GT_TRANSFORM_MAT][:]
    return cube, cube_to_gt_transform


def load_tiff(file_path: str) -> np.ndarray:
    """
    Load tiff image into np.ndarray
    :param file_path: Path to the .tiff file
    :return: Loaded image as np.ndarray
    """
    tiff = TIFF.open(file_path)
    return tiff.read_image()


def save_md5(output_path, train_x, train_y, val_x, val_y, test_x, test_y):
    """
    Save provided data as .md5 file
    :param output_path: Path to the filename
    :param train_x: Train set
    :param train_y: Train labels
    :param val_x: Validation set
    :param val_y: Validation labels
    :param test_x: Test set
    :param test_y: Test labels
    :return:
    """
    data_file = h5py.File(output_path, 'w')

    train_min, train_max = np.amin(train_x), np.amax(train_x)
    data_file.attrs.create(enums.DataStats.MIN, train_min)
    data_file.attrs.create(enums.DataStats.MAX, train_max)

    train_group = data_file.create_group(enums.Dataset.TRAIN)
    train_group.create_dataset(enums.Dataset.DATA, data=train_x)
    train_group.create_dataset(enums.Dataset.LABELS, data=train_y)

    val_group = data_file.create_group(enums.Dataset.VAL)
    val_group.create_dataset(enums.Dataset.DATA, data=val_x)
    val_group.create_dataset(enums.Dataset.LABELS, data=val_y)

    test_group = data_file.create_group(enums.Dataset.TEST)
    test_group.create_dataset(enums.Dataset.DATA, data=test_x)
    test_group.create_dataset(enums.Dataset.LABELS, data=test_y)
    data_file.close()


def read_min_max(path: str) -> Tuple[float, float]:
    """
    Read min and max value from a .csv file
    :param path:
    :return: Tuple with min and max
    """
    min_, max_ = np.loadtxt(path)
    return min_, max_


def load_pb(path_to_pb: str) -> tf.GraphDef:
    """
    Load .pb file as a graph
    :param path_to_pb: Path to the .pb file
    :return: Loaded graph
    """
    with tf.gfile.GFile(path_to_pb, "rb") as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
    with tf.Graph().as_default() as graph:
        tf.import_graph_def(graph_def, name='')
        return graph
