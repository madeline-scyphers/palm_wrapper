import datetime as dt
from pathlib import Path

import yaml

__all__ = ["config", "get_wrapper_config", "USER_CODE_MODULE"]

current_dir = Path(__file__).resolve().parent

USER_CODE_MODULE = current_dir / "user_module.f90"

TEMPLATE_DIR = str((current_dir / "palm_config_template.txt").resolve())


def get_config(file: str = "wrapper_config.yaml") -> dict:
    with open(current_dir / file, "r") as f:
        config = yaml.safe_load(f)
    return config


config = get_config()
del get_config
del current_dir


def _validate_config_constraints(ground_ratio, house_ratio, mean_lai, plot_footprint, **kwargs):
    assert ground_ratio + house_ratio <= 1, f"{ground_ratio=}, {house_ratio=}, {mean_lai=}, {plot_footprint=}"
    assert ground_ratio + house_ratio + .6*house_ratio <= .6, f"{ground_ratio=}, {house_ratio=}, {mean_lai=}, {plot_footprint=}"

    assert .1 <= house_ratio <= .8, f"{ground_ratio=}, {house_ratio=}, {mean_lai=}, {plot_footprint=}"  # Ratio of urban area that is house (not ground, not trees)
    assert .25 <= ground_ratio <= .8, f"{ground_ratio=}, {house_ratio=}, {mean_lai=}, {plot_footprint=}"  # Ratio of urban area that is ground (not house, not trees)
    assert 350 <= plot_footprint <= 950, f"{ground_ratio=}, {house_ratio=}, {mean_lai=}, {plot_footprint=}"  # Size of a plot of land (area of a house and its ground it sits on)
    assert 2.0 <= mean_lai <= 6.0, f"{ground_ratio=}, {house_ratio=}, {mean_lai=}, {plot_footprint=}"  # The mean LAI of the canopy. There will be random perturbations to this


def get_wrapper_config(
    domain_x=96,  # 192,
    # domain_y=216,  # 432,
    domain_y=432,
    # dx=3,
    # dy=3,
    # dz=3,
    dx=5,
    dy=5,
    dz=5,
    urban_ratio=0.5,
    # house_plot_ratio=2/7,
    plot_footprint=700,
    # plot_ratio=0.70,
    ground_ratio=0.35,
    house_ratio=0.14,
    mean_lai=3,
    output_start_time=0,
    output_end_time=300,
    template_path=TEMPLATE_DIR,
    job_name=None,
    _validate=True,
    **kwargs
):
    if _validate:
        _validate_config_constraints(ground_ratio, house_ratio, mean_lai, plot_footprint)
    job_name = job_name if job_name is not None else dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    plot_ratio = ground_ratio + house_ratio
    try:
        house_plot_ratio = house_ratio / plot_ratio
    except ZeroDivisionError:
        house_plot_ratio = 0
    config = {
        "job_name": job_name,
        "output_start_time": output_start_time,
        "output_end_time": output_end_time,
        "template_path": template_path,
        "domain": {"x": int(domain_x), "y": int(domain_y), "dx": dx, "dy": dy, "dz": dz, "urban_ratio": urban_ratio, "stack_height": 940 }, #750 / (dz * 3)},
        "house": {
            "footprint": int(plot_footprint * house_plot_ratio),  # in square meters
            "height": 20 / (dz * 3),
        },
        "plot": {"plot_footprint": plot_footprint, "plot_ratio": plot_ratio},
        "canopy": {"mean_lai": mean_lai},
    }
    return config
