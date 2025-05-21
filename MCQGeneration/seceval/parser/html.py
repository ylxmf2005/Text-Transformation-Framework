from seceval.entity import PageItem, TextArtifact, gen_uuid
from typing import List
from seceval.parser.md import MdParser
from seceval.convert import html_to_md
from typing import Dict, Any


class HtmlParser(MdParser):
    def __init__(self, profile: Dict[str, Any] = {}):
        pass

    def parse(self, item: PageItem):
        assert item.content is not None
        content = item.content
        item.content.content = html_to_md(item.content.content.decode("utf-8")).encode(
            "utf-8"
        )
        item.content.mime_type = item.content.mime_type.replace(
            "text/html", "text/markdown"
        )
        return super().parse(item)
