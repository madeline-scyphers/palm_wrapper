from __future__ import annotations

from pathlib import Path

from .domain import Domain

current_dir = Path(__file__).resolve().parent

USER_CODE_MODULE = current_dir / "user_module.f90"


def generate_job_config(config: dict) -> str:
    with open(config["template_path"]) as template:
        job_config = template.read()
    job_cfg = job_config.format(
        domain_x=config["domain"]["x"] - 1,
        domain_y=config["domain"]["y"] - 1,
        output_start_time=config["output_start_time"],
        output_end_time=config["output_end_time"],
        dx=config["domain"]["dx"],
        dy=config["domain"]["dy"],
        dz=config["domain"]["dz"],
    )
    return job_cfg


def generate_user_module(domain: Domain) -> str:
    with open(USER_CODE_MODULE) as template:
        user_module = template.read()
    domain_y = domain.full_y
    model_y = domain.temp_y
    cutoff = domain_y - model_y
    user_module = user_module.format(urban_edge=cutoff)
    return user_module
