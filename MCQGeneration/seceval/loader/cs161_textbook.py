from typing import List

from bs4 import BeautifulSoup
from seceval.convert import html_to_md
from seceval.crawler import TypedContent
from seceval.loader.base.web import WebLoader
from seceval.entity import PageItem, TextArtifact
from seceval.loader.base import LoaderBase, LoaderType
import re


class CS161Textbook(WebLoader):
    task_name: str = "cs161_textbook"
    base_url: str = "https://textbook.cs161.org/"
    start_urls: List[str] = ["https://textbook.cs161.org/"]
    max_depth: int = 3
    parser_profile = {
        "max_header_level": 1,
    }

    def transform_content(self, content: TypedContent, depth: int = 0) -> TypedContent:
        assert content.mime_type.startswith("text/html")
        soup = BeautifulSoup(content.content, "html.parser")
        article_element = soup.find("div", {"id": "main-content-wrap"})

        text = html_to_md(str(article_element))
        content.content = text.encode()
        content.mime_type = content.mime_type.replace("text/html", "text/markdown")
        return content

    def filter_url(self, url: str, parent_url: str, depth: int):
        if depth == 1 and url.endswith("/") and url.startswith(parent_url):
            return True
        elif depth == 2:
            return (
                url.startswith(parent_url)
                and url[len(parent_url) + 1 :].count("/") == 1
                and url[len(parent_url) + 1 :].count("#") == 0
                and url.endswith(".html")
            )
        return False

    def filter_item(self, item: PageItem, depth: int = 0):
        return depth != 0
