from abc import ABC, abstractmethod
from seceval.entity import PageItem, TextArtifact, gen_uuid
from seceval.parser import get_parser_class_by_mime
from seceval.loader.base import LoaderBase
from seceval.crawler import TypedContent
from typing import Dict, List, Tuple
from enum import Enum
import glob
import mimetypes
import os
import logging

logger = logging.getLogger(__name__)


class LoaderType(str, Enum):
    WEB = "WEB"
    FILE = "FILE"


class FileLoader(LoaderBase):
    # Define instance variables with type hints
    task_type: LoaderType = LoaderType.FILE
    task_name: str
    dirname: str
    filename_pattern: str
    recursive: bool = False

    def create_dir_pages_recursive(
        self, dir_path: str, dir_page_items: Dict[str, PageItem]
    ):
        if not dir_path or dir_path in dir_page_items:
            return
        parent_dir_path = os.path.dirname(dir_path)
        if parent_dir_path and parent_dir_path not in dir_page_items:
            self.create_dir_pages_recursive(parent_dir_path, dir_page_items)
        dir_page_items[dir_path] = PageItem(
            id=gen_uuid(),
            parent_id=dir_page_items[os.path.dirname(dir_path)].id
            if parent_dir_path
            else None,
            depth=dir_path.count("/") + 1,
            uri=dir_path,
            file_path=dir_path,
            type="inode/directory",
        )

    def load(self) -> Tuple[List[PageItem], List[TextArtifact]]:
        """
        Scan all files by glob using dirname and filename_pattern.
        Should be implemented by subclasses to return a list of TextArtifact instances.
        """
        self.dirname = self.dirname.rstrip("/")
        pattern = (
            os.path.join(self.dirname, "**", self.filename_pattern)
            if self.recursive
            else os.path.join(self.dirname, self.filename_pattern)
        )
        file_paths = glob.glob(pattern, recursive=self.recursive)

        logger.info(f"Found {len(file_paths)} files by pattern {pattern}")
        dir_page_items: Dict[str, PageItem] = {}

        page_items: List[PageItem] = []
        artifacts: List[TextArtifact] = []
        for file_path in file_paths:
            mime_type = mimetypes.guess_type(file_path)[0]
            if mime_type is None:
                logger.warning(f"Unknown mime type for {file_path}")
                continue

            relative_file_path = file_path[len(self.dirname) + 1 :]
            relative_parent_dir_path = os.path.dirname(relative_file_path)
            self.create_dir_pages_recursive(relative_parent_dir_path, dir_page_items)
            with open(file_path, "rb") as f:
                typed_content = TypedContent(mime_type=mime_type, content=f.read())
                depth = relative_file_path.count("/") + 1
                item = PageItem(
                    id=gen_uuid(),
                    parent_id=dir_page_items[relative_parent_dir_path].id
                    if relative_parent_dir_path
                    else None,
                    uri=relative_file_path,
                    depth=depth,
                    content=typed_content,
                    file_path=file_path,
                    type=typed_content.mime_type,
                )
                if self.filter_item(item, depth):
                    item.content = self.transform_content(typed_content, 0)
                    artifacts.extend(
                        get_parser_class_by_mime(typed_content.mime_type)(
                            self.parser_profile
                        ).parse(item)
                    )
                    page_items.append(item)
            page_items.extend(dir_page_items.values())

        return page_items, artifacts
