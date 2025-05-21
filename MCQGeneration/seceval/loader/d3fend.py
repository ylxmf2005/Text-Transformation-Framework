from seceval.convert import html_to_md
from seceval.loader.base.web import WebLoader
from seceval.entity import PageItem, TextArtifact
from seceval.loader.base import LoaderBase, LoaderType
from seceval.crawler import TypedContent
from typing import List
import re


class D3FENDLoader(WebLoader):
    task_name: str = "d3fend"
    base_url: str = "https://d3fend.mitre.org/"
    start_urls: List[str] = ["https://d3fend.mitre.org/"]
    max_depth: int = 4
    use_browser: bool = True

    def transform_content(self, content: TypedContent, depth: int) -> TypedContent:
        assert content.mime_type.startswith("text/html")

        md = html_to_md(content.content.decode("utf-8"))
        patterns = [
            r"(?s)(# .*?)## Digital Artifact Relationships:",
            r"(?s)(# .*?)close",
        ]
        for pattern in patterns:
            match = re.search(pattern, md)
            if match:
                md = match.group(1)
                break
        content.content = md.encode()
        content.mime_type = content.mime_type.replace("text/html", "text/markdown")
        return content

    def filter_url(self, url: str, parent_url: str, depth: int):
        if url.endswith(".json"):
            return False
        if depth == 1:
            return re.search(r"/tactic/d3f:(\w+)", url)
        elif depth >= 2 and depth <= 3:
            return re.search(r"/technique/d3f:(\w+)", url) and url != parent_url
        else:
            return False

    # override in subclass
    def filter_item(self, item: PageItem, depth: int = 0):
        return depth != 0
