"""
Run experiments given set of hyperparameters.
"""

import os
import shutil

import clize
import mlflow
import tensorflow as tf
from clize.parameters import multi

from scripts import evaluate_model, prepare_data, artifacts_reporter
from ml_intuition.enums import Splits, Experiment
from ml_intuition.data.io import load_processed_h5
from ml_intuition.data.utils import get_mlflow_artifacts_path, parse_train_size
from ml_intuition.data.loggers import log_params_to_mlflow, log_tags_to_mlflow


def run_experiments(*,
                    data_file_path: str = None,
                    ground_truth_path: str = None,
                    dataset_path: str = None,
                    train_size: ('train_size', multi(min=0)),
                    val_size: float = 0.1,
                    stratified: bool = True,
                    background_label: int = 0,
                    channels_idx: int = 0,
                    save_data: bool = False,
                    n_runs: int,
                    dest_path: str,
                    models_path: str,
                    n_classes: int,
                    batch_size: int = 1024,
                    post_noise_sets: ('spost', multi(min=0)),
                    post_noise: ('post', multi(min=0)),
                    noise_params: str = None,
                    use_mlflow: bool = False,
                    experiment_name: str = None,
                    run_name: str = None):
    """
    Function for running experiments given a set of hyperparameters.
    :param data_file_path: Path to the data file. Supported types are: .npy
    :param ground_truth_path: Path to the ground-truth data file.
    :param dataset_path: Path to the already extracted .h5 dataset
    :param train_size: If float, should be between 0.0 and 1.0,
                        if stratified = True, it represents percentage of each
                        class to be extracted,
                 If float and stratified = False, it represents percentage of the
                    whole dataset to be extracted with samples drawn randomly,
                    regardless of their class.
                 If int and stratified = True, it represents number of samples
                    to be drawn from each class.
                 If int and stratified = False, it represents overall number of
                    samples to be drawn regardless of their class, randomly.
                 Defaults to 0.8
    :param val_size: Should be between 0.0 and 1.0. Represents the percentage of
                     each class from the training set to be extracted as a
                     validation set, defaults to 0.1
    :param stratified: Indicated whether the extracted training set should be
                     stratified, defaults to True
    :param background_label: Label indicating the background in GT file
    :param channels_idx: Index specifying the channels position in the provided
                         data
    :param save_data: Whether to save the prepared dataset
    :param n_runs: Number of total experiment runs.
    :param dest_path: Path to where all experiment runs will be saved as
        subfolders in this directory.
    :param models_path: Name of the model, it serves as a key in the
        dictionary holding all functions returning models.
    :param n_classes: Number of classes.
    :param batch_size: Size of the batch for the inference
    :param post_noise_sets: The list of sets to which the noise will be
        injected. One element can either be "train", "val" or "test".
    :param post_noise: The list of names of noise injection methods after
        the normalization transformations.
    :param noise_params: JSON containing the parameter setting of injection methods.
        Exemplary value for this parameter: "{"mean": 0, "std": 1, "pa": 0.1}".
        This JSON should include all parameters for noise injection
        functions that are specified in pre_noise and post_noise arguments.
        For the accurate description of each parameter, please
        refer to the ml_intuition/data/noise.py module.
    :param use_mlflow: Whether to log metrics and artifacts to mlflow.
    :param experiment_name: Name of the experiment. Used only if
        use_mlflow = True
    :param run_name: Name of the run. Used only if use_mlflow = True.
    """
    train_size = parse_train_size(train_size)
    if use_mlflow:
        args = locals()
        mlflow.set_tracking_uri("http://beetle.mlflow.kplabs.pl")
        mlflow.set_experiment(experiment_name)
        mlflow.start_run(run_name=run_name)
        log_params_to_mlflow(args)
        log_tags_to_mlflow(args['run_name'])
        models_path = get_mlflow_artifacts_path(models_path)

    for experiment_id in range(n_runs):
        experiment_dest_path = os.path.join(
            dest_path, 'experiment_' + str(experiment_id))
        model_path = os.path.join(models_path,
                                  'experiment_' + str(experiment_id),
                                  'model_2d')
        if dataset_path is None:
            data_source = os.path.join(models_path,
                                       'experiment_' + str(experiment_id),
                                       'data.h5')
        else:
            data_source = dataset_path
        os.makedirs(experiment_dest_path, exist_ok=True)

        if data_file_path.endswith('.h5') and ground_truth_path is None:
            data_source = load_processed_h5(data_file_path=data_file_path)

        elif not os.path.exists(data_source):
            data_source = prepare_data.main(data_file_path=data_file_path,
                                            ground_truth_path=ground_truth_path,
                                            output_path=data_source,
                                            train_size=train_size,
                                            val_size=val_size,
                                            stratified=stratified,
                                            background_label=background_label,
                                            channels_idx=channels_idx,
                                            save_data=save_data,
                                            seed=experiment_id)

        evaluate_model.evaluate(
            model_path=model_path,
            data=data_source,
            dest_path=experiment_dest_path,
            n_classes=n_classes,
            noise=post_noise,
            noise_sets=post_noise_sets,
            noise_params=noise_params,
            batch_size=batch_size)

        tf.keras.backend.clear_session()

    artifacts_reporter.collect_artifacts_report(experiments_path=dest_path,
                                                dest_path=dest_path,
                                                use_mlflow=use_mlflow)
    if Splits.GRIDS in data_file_path:
        fair_report_path = os.path.join(dest_path, Experiment.REPORT_FAIR)
        artifacts_reporter.collect_artifacts_report(experiments_path=dest_path,
                                                    dest_path=fair_report_path,
                                                    filename=Experiment.INFERENCE_FAIR_METRICS,
                                                    use_mlflow=use_mlflow)
    if use_mlflow:
        mlflow.log_artifacts(dest_path, artifact_path=dest_path)
        shutil.rmtree(dest_path)


if __name__ == '__main__':
    clize.run(run_experiments)
