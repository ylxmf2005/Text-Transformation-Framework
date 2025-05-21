import importlib
import re
from seceval.question.artifact_sampler.default import default_sampler
from seceval.storage import load_artifacts, load_pages
from functools import partial
import random
import logging

logger = logging.getLogger(__name__)


def get_sampler(task_name: str):
    # import seceval.question.artifact_sampler.<task_name>
    try:
        sampler_module = importlib.import_module(
            f"seceval.question.artifact_sampler.{task_name}"
        )
        return sampler_module.artifact_sampler
    except ModuleNotFoundError:
        logger.warning(f"Sampler for {task_name} not found, using default sampler")
        return partial(default_sampler, task_name=task_name)
