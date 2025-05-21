from typing import List
from seceval.convert import html_to_md
from seceval.crawler import TypedContent
from seceval.loader.base.web import WebLoader
from seceval.entity import PageItem, TextArtifact
from seceval.loader.base import LoaderBase, LoaderType
import re


class ATTCKLoader(WebLoader):
    task_name: str = "attck"
    base_url: str = "https://attack.mitre.org"
    start_urls: List[str] = ["https://attack.mitre.org"]
    max_depth: int = 4

    def transform_content(self, content: TypedContent, depth: int = 0) -> TypedContent:
        assert content.mime_type.startswith("text/html")
        text = html_to_md(content.content.decode())
        patterns = [r"(?s)(# .*?)## References", r"(?s)(# .*?)×"]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                text = match.group(1)
                break
        content.content = text.encode()
        content.mime_type = content.mime_type.replace("text/html", "text/markdown")
        return content

    def filter_url(self, url: str, parent_url: str, depth: int):
        if depth == 1:
            return re.search(r"/tactics/TA[0-9]{4}", url)
        elif depth == 2:
            match = re.search(r"/techniques/T[0-9]{4}", url)
            return match and match.end() == len(url)
        elif depth == 3:
            return re.search(r"/techniques/T[0-9]{4}/[0-9]{3}", url)
        else:
            return False

    def filter_item(self, item: PageItem, depth: int = 0):
        return depth != 1
