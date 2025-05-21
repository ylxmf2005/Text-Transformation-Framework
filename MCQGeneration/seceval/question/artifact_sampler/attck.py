import random
from typing import List
import re
from seceval.entity import (
    TextArtifact,
    find_artifact_descendant,
    get_artifact_hierarchy,
    find_page_descendant,
    get_page_hierarchy,
)
from seceval.question.artifact_sampler.default import do_sample_artifacts

from seceval.storage import load_artifacts, load_pages


def artifact_sampler(number: int):
    task_name = "attck"

    artifacts = load_artifacts(task_name)
    pages = load_pages(task_name)
    texts, backgrounds = do_sample_artifacts(
        lambda x: bool(x.level == 1 and x.page_depth == 3),
        artifacts,
        pages,
        number,
    )
    return texts, backgrounds
