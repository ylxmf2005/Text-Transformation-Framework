from typing import List
from seceval.question.artifact_sampler.default import do_sample_artifacts

from seceval.storage import load_artifacts, load_pages


def artifact_sampler(number: int):
    task_name = "d3fend"

    artifacts = load_artifacts(task_name)
    pages = load_pages(task_name)
    texts, backgrounds = do_sample_artifacts(
        lambda x: bool(x.level == 1 and x.page_depth == 2),
        artifacts,
        pages,
        number,
    )
    return texts, backgrounds
