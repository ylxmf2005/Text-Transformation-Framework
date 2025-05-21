from typing import List
from seceval.question.artifact_sampler.default import do_sample_artifacts

from seceval.storage import load_artifacts, load_pages


def artifact_sampler(number: int):
    task_name = "cs161_textbook"

    artifacts = load_artifacts(task_name)
    pages = load_pages(task_name)
    texts, backgrounds = do_sample_artifacts(
        lambda x: bool(x.level == 2 and x.page_depth == 3),
        artifacts,
        pages,
        number,
    )
    return texts, backgrounds
