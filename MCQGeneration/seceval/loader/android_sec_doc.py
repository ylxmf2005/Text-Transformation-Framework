from typing import List

from bs4 import BeautifulSoup
from seceval.convert import html_to_md
from seceval.crawler import TypedContent
from seceval.loader.base.web import WebLoader
from seceval.entity import PageItem, TextArtifact
from seceval.loader.base import LoaderBase, LoaderType
import re


class AndroidSecLoader(WebLoader):
    task_name: str = "android_sec_doc"
    base_url: str = "https://source.android.com/"
    start_urls: List[str] = [
        "https://source.android.com/docs/security/overview",
        "https://source.android.com/docs/security/features",
    ]
    max_depth: int = 3

    def transform_content(self, content: TypedContent, depth: int = 0) -> TypedContent:
        assert content.mime_type.startswith("text/html")
        soup = BeautifulSoup(content.content, "html.parser")
        article_elements = soup.find_all("article")

        articles_md = []
        for article in article_elements:
            article_html = str(article)
            article_md = html_to_md(article_html)
            articles_md.append(article_md)

        text = "\n\n".join(articles_md)
        text = text.replace("  * AOSP \n  * Docs \n  * Security \n\n", "")
        content.content = text.encode()
        content.mime_type = content.mime_type.replace("text/html", "text/markdown")
        return content

    def filter_url(self, url: str, parent_url: str, depth: int):
        if url.endswith("acknowledgements"):
            return False
        if depth <= 2:
            return (
                url.startswith(parent_url)
                and url[len(parent_url) :].count("/") == 1
                and url[len(parent_url) :].count("#") == 0
            )
        return False
