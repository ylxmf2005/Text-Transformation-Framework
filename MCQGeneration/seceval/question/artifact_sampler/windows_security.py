from typing import List
from seceval.question.artifact_sampler.default import do_sample_artifacts

from seceval.storage import load_artifacts, load_pages


def artifact_sampler(number: int):
    task_name = "windows_security"

    artifacts = load_artifacts(task_name)
    pages = load_pages(task_name)

    top_texts, top_backgrounds = do_sample_artifacts(
        lambda x: bool(
            x.page_depth == 2 and x.level == 1 and x.page_type == "text/markdown"
        ),
        artifacts,
        pages,
        min(number, 32),
    )
    if number > 32:
        texts, backgrounds = do_sample_artifacts(
            lambda x: bool(
                x.page_depth == 3 and x.level == 1 and x.page_type == "text/markdown"
            ),
            artifacts,
            pages,
            number - 32,
        )
    else:
        texts, backgrounds = [], []
    texts = top_texts + texts
    backgrounds = top_backgrounds + backgrounds
    return texts, backgrounds
