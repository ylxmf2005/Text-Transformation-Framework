from typing import Any, Dict
from seceval.entity import PageItem
from seceval.parser.html import HtmlParser
from seceval.parser.md import MdParser
from seceval.parser.pdf import PDFParser
from seceval.parser.text import TextParser
from seceval.parser.xml import XmlParser
import logging

logger = logging.getLogger(__name__)


class DummyParser:
    def __init__(self, profile: Dict[str, Any] = {}):
        pass

    def parse(self, item: PageItem):
        return []


def get_parser_class_by_mime(mime_type: str):
    if mime_type.startswith("text/html"):
        return HtmlParser
    elif mime_type.startswith("text/markdown"):
        return MdParser
    elif mime_type.startswith("application/pdf"):
        return PDFParser
    elif mime_type.startswith(("application/xml", "text/xml")):
        return XmlParser
    elif "text" in mime_type:
        return TextParser
    else:
        logger.warning(f"Unsupported MIME type: {mime_type}, use DummyParser instead")
        return DummyParser
