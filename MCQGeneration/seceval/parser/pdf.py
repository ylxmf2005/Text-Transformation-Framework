import re
import seceval.crawler as crawler
from seceval.convert import html_to_md, any_to_html, html_to_text
from seceval.entity import PageItem, TextArtifact, gen_uuid
from seceval.parser.html import HtmlParser
import os
from seceval.loader.base import LoaderBase, PageType
import logging
from io import BytesIO
from pydantic import BaseModel
from tempfile import NamedTemporaryFile
from typing import Dict, List, Any, Callable, Optional

logger = logging.getLogger(__name__)


class TableOfContentItem(BaseModel):
    id: str = ""
    parent_id: Optional[str] = ""
    title: str
    page_number_range: List[int]
    level: int = 0


class PDFParser:
    """
    toc_page_number_range:  number of pages that contains the table of content
    content_base_page_index: page index of the first page of the content
    toc_base_page_index: page index of the first page number of the table of content
    """

    toc_page_number_range: List[int]
    content_base_page_index: int
    toc_base_page_index: int
    get_page_text: Callable[[str, int], str]

    def __init__(self, profile: Dict[str, Any] = {}):
        self.toc_base_page_index = profile.get("toc_base_page_index", 0)
        self.content_base_page_index = profile.get("content_base_page_index", 0)
        self.toc_page_number_range = profile.get("toc_page_number_range", [2, 3, 4])
        self.get_page_text = profile.get(
            "get_page_text", lambda text, depth: html_to_text(text)
        )

    def parse_table_of_content(self, toc_text: str, pdf_html: List[Dict[str, Any]]):
        result: List[TableOfContentItem] = []
        current_top_level_toc = None
        toc_raw = re.findall(r"(.+)[\s\.]+(\d+)\n", toc_text)
        toc_raw.append(("", len(pdf_html) - self.content_base_page_index))
        for idx, toc_raw_item in enumerate(toc_raw[:-1]):
            next_toc_raw_item = toc_raw[idx + 1]
            if next_toc_raw_item[1] == toc_raw_item[1]:
                if current_top_level_toc:
                    current_top_level_toc.page_number_range = list(
                        range(
                            current_top_level_toc.page_number_range[-1],
                            int(next_toc_raw_item[1]),
                        )
                    )
                result.append(
                    TableOfContentItem(
                        id=gen_uuid(),
                        title=toc_raw_item[0],
                        page_number_range=[int(toc_raw_item[1])],
                        level=1,
                    )
                )
                current_top_level_toc = result[-1]

                continue

            result.append(
                TableOfContentItem(
                    id=gen_uuid(),
                    title=toc_raw_item[0],
                    page_number_range=list(
                        range(int(toc_raw_item[1]), int(next_toc_raw_item[1]))
                    ),
                    level=2,
                    parent_id=current_top_level_toc.id
                    if current_top_level_toc
                    else None,
                )
            )

        return result

    def parse(self, item: PageItem):
        result = []

        pdf_html = any_to_html(item.file_path)
        logger.info(
            f"Converted PDF {item.file_path} to HTML"
        )  # use the name of the temporary file

        toc_text = ""
        for toc_page_number in self.toc_page_number_range:
            toc_text += html_to_text(
                pdf_html[self.toc_base_page_index + toc_page_number - 1]["html"].decode(
                    "utf-8"
                )
            )

        toc_items = self.parse_table_of_content(toc_text, pdf_html)
        for toc_item in toc_items:
            html = "\n\n".join(
                [
                    pdf_html[self.content_base_page_index + x - 1]["html"].decode(
                        "utf-8"
                    )
                    for x in toc_item.page_number_range
                ]
            )
            page_artifact = TextArtifact(
                page_id=item.id,
                page_uri=item.uri or item.file_path,
                page_depth=item.depth,
                page_type=item.type,
                id=toc_item.id,
                level=toc_item.level,
                parent_id=toc_item.parent_id,
                title=toc_item.title,
                html=html,
                text="\n\n".join(
                    [
                        self.get_page_text(
                            pdf_html[self.content_base_page_index + x - 1][
                                "html"
                            ].decode("utf-8"),
                            0,
                        )
                        for x in toc_item.page_number_range
                    ]
                ),
            )
            result.append(page_artifact)
        return result
