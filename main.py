from __future__ import annotations

import datetime as dt
from locale import normalize
import logging
import os
import shutil
from pathlib import Path
from pprint import pformat

import click
from palm_wrapper.job_submission import run
# from optiwrap import read_experiment_config
import yaml
from boa import load_yaml

ONE_MIN = 60
TEN_MIN = 10 * ONE_MIN
ONE_HOUR = 60 * ONE_MIN

OUTPUT_START_TIME = 6 * ONE_HOUR
OUTPUT_END_TIME = 6 * ONE_HOUR + 3 * TEN_MIN

# OUTPUT_START_TIME = 0
# OUTPUT_END_TIME = int(2 * ONE_MIN)

JOB_RUN_TIMEOUT_SCALER = 3

log_dir = Path().resolve() / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_dir / f'{dt.datetime.now().strftime("%Y%m%dT%H%M%S")}.log',
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler())

summary = """
----------------- JOB WRAPPER CONFIG -----------------

"""


def read_experiment_config(config_file):
    """
    Read experiment configuration yml file for setting up the optimization.
    yml file contains the list of parameters, and whether each parameter is a fixed
    parameter or a range parameter. Fixed parameters have a value specified, and range
    parameters have a range specified.

    Parameters
    ----------
    config_file : str
        File path for the experiment configuration file

    Returns
    -------
    loaded_configs: dict
    """

    # Load the experiment config yml file
    with open(config_file, "r") as yml_config:
        loaded_configs = yaml.safe_load(yml_config)

    # Format parameters for Ax experiment
    for param in loaded_configs.get("parameters", {}).keys():
        loaded_configs["parameters"][param][
            "name"
        ] = param  # Add "name" attribute for each parameter
    # Parameters from dictionary to list
    loaded_configs["search_space_parameters"] = list(loaded_configs.get("parameters", {}).values())
    return loaded_configs


@click.command()
@click.option(
    "-n",
    "--job_name",
    type=str,
    default="ex1" + dt.datetime.now().strftime("%Y%m%dT%H%M%S"),
    help="Which job name this job is in a run of jobs.",
)
@click.option(
    "-cf",
    "--config_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=str(Path(__file__).parent.parent / "wrapper_config.yaml"),
    help="Path to configuration YAML file.",
)
@click.option(
    "-id",
    "--input_dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    # default=str(Path(__file__).parent.parent / "wrapper_config.yaml"),
    help="Path to input directory",
)
def main(job_name, config_file, input_dir=None):
    config = load_yaml(config_file, normalize=False)
    model_options = config.get("model_options", {})
    model_options["job_name"] = job_name
    params = config.get("parameters", {})
    input_dir = input_dir if input_dir is not None else Path(config["optimization_options"].get("input_dir", ""))
    wrapper_config = run_job(ex_settings=config["optimization_options"], input_dir=input_dir, **model_options, **params)

    logging.info("\nWrapper Config: \n%s", pformat(wrapper_config))
    logging.info("written to directory: %s", input_dir)

    logging.info("\nscript done")


def run_job(job_name, ex_settings, input_dir, **kwargs):
    working_dir = Path(ex_settings.get("working_dir", "~/palm"))
    wrapper_config = {}
    try:
        os.chdir(working_dir.expanduser())

        wrapper_config = run.get_config(
            job_name=job_name, **kwargs
        )
        run.create_input_files(wrapper_config, input_dir)

    except TypeError as e:
        logging.exception(e)

        input_dir_to_remove = input_dir / wrapper_config["job_name"]
        if input_dir_to_remove.exists():
            shutil.rmtree(input_dir_to_remove)

    return wrapper_config


if __name__ == "__main__":
    logging.info("Starting script at %s", dt.datetime.now().strftime("%Y%m%dT%H%M%S"))

    main()
