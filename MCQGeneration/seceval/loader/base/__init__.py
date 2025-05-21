from abc import ABC, abstractmethod
from seceval.crawler import TypedContent
from seceval.entity import PageItem, TextArtifact
from typing import Any, Dict, List, Tuple
from enum import Enum
from seceval.storage import save_artifacts


class PageType(str, Enum):
    PDF = "PDF"
    HTML = "HTML"
    TEXT = "TEXT"
    MD = "MD"


class LoaderType(str, Enum):
    WEB = "WEB"
    FILE = "FILE"


class LoaderBase:
    page_type: str
    task_name: str
    parser_profile: Dict[str, Any] = {}

    # override in subclass
    def transform_content(self, content: TypedContent, depth: int = 0) -> TypedContent:
        return content

    # override in subclass
    def filter_item(self, item: PageItem, depth: int = 0):
        return True

    @abstractmethod
    def load(self) -> Tuple[List[PageItem], List[TextArtifact]]:
        pass
