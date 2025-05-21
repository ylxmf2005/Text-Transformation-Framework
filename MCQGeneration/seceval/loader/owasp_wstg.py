from pathlib import Path
from seceval.convert import html_to_text
from seceval.crawler import TypedContent
from seceval.loader.base.file import FileLoader
from seceval.loader.base import LoaderBase, LoaderType
from typing import List
import re


class OwaspWstgLoader(FileLoader):
    task_name = "owasp_wstg"
    # git clone --depth 1 https://github.com/OWASP/wstg.git
    dirname = "/nfs_ml/datasets/SecEval/WebSecurity/raw/wstg/document"

    filename_pattern = "*.md"
    recursive = True
    parser_profile = {}
