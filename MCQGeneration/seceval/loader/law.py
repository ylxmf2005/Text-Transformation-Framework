from bs4 import BeautifulSoup
from seceval.crawler import TypedContent
from seceval.parser import html
from seceval.loader.base.web import WebLoader
from seceval.entity import TextArtifact
from seceval.loader.base import LoaderBase, LoaderType
from seceval.convert import html_to_main_text, html_to_md
from typing import List
import re


class LawLoader(WebLoader):
    task_name: str = "law"
    base_url: str = "https://www.gov.cn/"
    start_urls: List[str] = [
        "https://www.gov.cn/zhengce/zhengceku/2021-07/14/content_5624965.htm",
        "https://www.gov.cn/zhengce/content/2021-08/17/content_5631671.htm",
        "https://www.gov.cn/zhengce/zhengceku/2022-01/04/content_5666430.htm",
        "https://www.oscca.gov.cn/sca/xxgk/2023-06/04/content_1057225.shtml",
        "https://www.gov.cn/xinwen/2016-11/07/content_5129723.htm",
        "https://www.gov.cn/xinwen/2022-09/14/content_5709805.htm",
        "https://www.gov.cn/xinwen/2021-06/11/content_5616919.htm",
    ]
    max_depth: int = 1
    use_browser: bool = False

    def transform_content(self, content: TypedContent, depth: int) -> TypedContent:
        assert content.mime_type.startswith("text/html")
        soup = BeautifulSoup(content.content, "html.parser")
        article_element = soup.find("div", {"class": "pages_content"})
        if article_element is None:
            text = html_to_main_text(content.content.decode())
        else:
            text = html_to_md(str(article_element))
        assert text is not None
        content.content = text.encode("utf-8")
        content.mime_type = content.mime_type.replace("text/html", "text/plain")
        return content
