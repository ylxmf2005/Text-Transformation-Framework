from typing import List
from seceval.question.artifact_sampler.default import do_sample_artifacts

from seceval.storage import load_artifacts, load_pages


def artifact_sampler(number: int):
    task_name = "cwe"
    cwe_top25 = [
        "CWE 269:",
        "CWE 918:",
        "CWE 276:",
        "CWE 362:",
        "CWE 77:",
        "CWE 306:",
        "CWE 89:",
        "CWE 190:",
        "CWE 22:",
        "CWE 416:",
        "CWE 476:",
        "CWE 94:",
        "CWE 20:",
        "CWE 125:",
        "CWE 434:",
        "CWE 798:",
        "CWE 862:",
        "CWE 119:",
        "CWE 863:",
        "CWE 502:",
        "CWE 78:",
        "CWE 352:",
        "CWE 287:",
        "CWE 787:",
        "CWE 79:",
    ]
    artifacts = load_artifacts(task_name)
    pages = load_pages(task_name)

    top25_texts, top25_backgrounds = do_sample_artifacts(
        lambda x: bool(
            x.level == 1 and x.page_depth == 1 and x.title.startswith(tuple(cwe_top25))
        ),
        artifacts,
        pages,
        min(number, 25),
    )
    if number > 25:
        texts, backgrounds = do_sample_artifacts(
            lambda x: bool(
                x.level == 1
                and x.page_depth == 1
                and not x.title.startswith(tuple(cwe_top25))
            ),
            artifacts,
            pages,
            number - 25,
        )
    else:
        texts, backgrounds = [], []

    texts = top25_texts + texts
    backgrounds = top25_backgrounds + backgrounds
    return texts, backgrounds
