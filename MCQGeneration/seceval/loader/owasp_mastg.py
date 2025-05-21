from pathlib import Path
from seceval.convert import html_to_text
from seceval.crawler import TypedContent
from seceval.loader.base.file import FileLoader
from seceval.loader.base import LoaderBase, LoaderType
from typing import List
import re


class OwaspMastgLoader(FileLoader):
    task_name = "owasp_mastg"
    # git clone --depth 1 https://github.com/OWASP/owasp-mastg.git
    dirname = "/nfs_ml/datasets/SecEval/WebSecurity/raw/owasp-mastg/Document"

    filename_pattern = "0x*.md"
    parser_profile = {}
