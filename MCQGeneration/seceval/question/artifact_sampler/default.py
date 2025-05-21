import random
from typing import Callable, List
import re
from seceval.entity import (
    PageItem,
    TextArtifact,
    find_artifact_descendant,
    get_artifact_hierarchy,
    find_page_descendant,
    get_page_hierarchy,
)

import logging

logger = logging.getLogger(__name__)
from seceval.storage import load_artifacts, load_pages


def default_sampler(number: int, task_name: str):
    # we fix the seed to make sure the sampling is deterministic
    artifacts = load_artifacts(task_name)
    pages = load_pages(task_name)
    return do_sample_artifacts(lambda x: True, artifacts, pages, number)


def do_sample_artifacts(
    sample_filter: Callable[[TextArtifact], bool],
    artifacts: List[TextArtifact],
    pages: List[PageItem],
    number: int,
):
    sample_from = list(filter(sample_filter, artifacts))
    logger.info(f"Sampling {number} artifacts from {len(sample_from)} artifacts")
    if number == -1:
        number = len(sample_from)
    samples = random.sample(sample_from, number)

    backgrounds = []
    texts = []
    for sample in samples:
        decendant = find_artifact_descendant(artifacts, sample)
        artifact_hierarchy = get_artifact_hierarchy(artifacts, sample)
        for page in pages:
            if page.id == sample.page_id:
                sample_page = page
                break
        sample_page = list(filter(lambda x: x.id == sample.page_id, pages))[0]
        page_hierarchy = get_page_hierarchy(pages, sample_page)
        page_hierarchy_text = "->".join([page.uri for page in page_hierarchy])
        artifact_hierarchy_text = "->".join(
            [artifact.title for artifact in artifact_hierarchy]
        )
        decendant_text = "\n".join([artifact.text for artifact in decendant])
        text = artifact_hierarchy_text + "\n" + sample.text + "\n" + decendant_text

        # segment the decendant_text into 8192 characters per segment
        segment_length = 8192
        for i in range(0, len(text), segment_length):
            segment = text[i : i + segment_length]
            if len(segment) < 4096 and i != 0:
                continue
            texts.append(segment)
            background = f"These texts were extracted from the web page {sample.page_uri}, following a fixed order determined by the page hierarchy: {page_hierarchy_text}\n semgent {i//segment_length}"
            if sample.level > 1:
                backgrounds.append(background)
            else:
                backgrounds.append("")

    return texts, backgrounds
