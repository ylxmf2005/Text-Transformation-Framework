from typing import List

from bs4 import BeautifulSoup
from seceval.convert import html_to_md
from seceval.crawler import TypedContent
from seceval.loader.base.web import WebLoader
from seceval.entity import PageItem, TextArtifact
from seceval.loader.base import LoaderBase, LoaderType
import re


class MozillaSecLoader(WebLoader):
    task_name: str = "mozilla_security"
    base_url: str = "https://infosec.mozilla.org"
    start_urls: List[str] = ["https://infosec.mozilla.org/guidelines/"]
    max_depth: int = 2

    def transform_content(self, content: TypedContent, depth: int = 0) -> TypedContent:
        assert content.mime_type.startswith("text/html")
        soup = BeautifulSoup(content.content, "html.parser")
        article_element = soup.find("div", {"id": "main_content_wrap"})

        text = html_to_md(str(article_element))
        content.content = text.encode()
        content.mime_type = content.mime_type.replace("text/html", "text/markdown")
        return content

    def filter_url(self, url: str, parent_url: str, depth: int):
        if depth == 1:
            return url.startswith(parent_url)
        return False

    def filter_item(self, item: PageItem, depth: int):
        return depth != 1
