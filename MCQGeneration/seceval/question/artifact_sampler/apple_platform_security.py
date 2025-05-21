from typing import List
from seceval.question.artifact_sampler.default import do_sample_artifacts

from seceval.storage import load_artifacts, load_pages


def artifact_sampler(number: int):
    task_name = "apple_platform_security"

    artifacts = load_artifacts(task_name)
    pages = load_pages(task_name)
    top_level_texts, top_level_backgrounds = do_sample_artifacts(
        lambda x: bool(x.level == 1 and x.page_depth == 1),
        artifacts,
        pages,
        min(number, 20),
    )
    if number > 20:
        texts, backgrounds = do_sample_artifacts(
            lambda x: bool(x.level == 2 and x.page_depth == 1),
            artifacts,
            pages,
            number - 20,
        )
    else:
        texts, backgrounds = [], []
    texts = top_level_texts + texts
    backgrounds = top_level_backgrounds + backgrounds
    return texts, backgrounds
