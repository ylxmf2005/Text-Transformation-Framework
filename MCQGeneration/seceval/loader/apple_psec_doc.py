from pathlib import Path
from seceval.convert import html_to_text
from seceval.crawler import TypedContent
from seceval.loader.base.file import FileLoader
from seceval.loader.base import LoaderBase, LoaderType
from typing import List
import re


def get_page_text(html: str, depth: int = 0) -> str:
    text = html_to_text(html)
    text = re.sub(r"\n?\d+Apple Platform Security\n*", "", text)
    return text


class ApplePSecDocLoader(FileLoader):
    task_name = "apple_platform_security"
    # wget https://help.apple.com/pdf/security/en_GB/apple-platform-security-guide-b.pdf
    dirname = "/nfs_ml/datasets/SecEval/SystemSecurity/raw"
    filename_pattern = "apple-platform-security-guide-b.pdf"
    parser_profile = {
        "toc_page_number_range": [2, 3, 4],
        "content_base_page_index": 0,
        "toc_base_page_index": 0,
        "get_page_text": get_page_text,
    }
