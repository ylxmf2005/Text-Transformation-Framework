import re

from pydantic import BaseModel
from seceval.crawler import browser_crawl_urls, crawl_urls, TypedContent
from seceval.convert import html_to_md, html_to_urls
from seceval.entity import TextArtifact, gen_uuid, PageItem
from seceval.loader.base import LoaderBase, LoaderType
from seceval.parser import get_parser_class_by_mime
import asyncio
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class WebLoader(LoaderBase):
    task_type: LoaderType = LoaderType.WEB
    task_name: str
    base_url: str
    start_urls: List[str]
    max_depth: int
    batch_size: int = 30
    use_browser: bool = False

    def extract_url(self, html: str, current_url: str, depth: int):
        return html_to_urls(html, self.base_url, current_url)

    # override in subclass
    def filter_url(self, url: str, parent_url: str, depth: int):
        return True

    def crawl_item(self, items: List[PageItem], depth: int, browser: bool = False):
        loop = asyncio.get_event_loop()
        urls = [x.uri for x in items]
        if browser:
            contents = browser_crawl_urls(urls, 10)
        else:
            contents = crawl_urls(urls, 10)
        for idx, content in enumerate(contents):
            if content:  # Check if the content is not empty
                items[idx].content = content
                items[idx].type = content.mime_type
            else:
                logger.error(f"Failed to crawl item {items[idx].id}")
                items[idx].content = TypedContent(mime_type="text/plain", content=b"")
                items[idx].type = "error"
        return items

    def load(self) -> Tuple[List[PageItem], List[TextArtifact]]:
        result_artifacts: List[TextArtifact] = []
        result_items: List[PageItem] = []
        current_items = [
            PageItem(id=gen_uuid(), uri=url, depth=1) for url in self.start_urls
        ]

        for i in range(self.max_depth):
            depth = i + 1
            logger.info(f"Crawling {len(current_items)} items, depth {depth}")
            for i in range(0, len(current_items), self.batch_size):
                self.crawl_item(
                    current_items[i : i + self.batch_size], depth, self.use_browser
                )

            next_items = []
            for item in current_items:
                assert item.content is not None
                if item.type.startswith("text/html"):
                    # only propagate text/html
                    next_items.extend(
                        map(
                            lambda url: PageItem(
                                id=gen_uuid(),
                                uri=url,
                                parent_id=item.id,
                                depth=depth + 1,
                            ),
                            filter(
                                lambda url: self.filter_url(url, item.uri, depth),
                                self.extract_url(
                                    item.content.content.decode("utf-8"),
                                    item.uri,
                                    depth,
                                ),
                            ),
                        )
                    )

                if self.filter_item(item, depth):
                    item.content = self.transform_content(item.content, depth)
                    result_artifacts.extend(
                        get_parser_class_by_mime(item.content.mime_type)(
                            self.parser_profile
                        ).parse(item)
                    )
                    result_items.append(item)
            current_items = next_items

        logger.info(f"{len(result_artifacts)} text artifacts loaded")
        return result_items, result_artifacts
