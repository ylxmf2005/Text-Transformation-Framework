from pathlib import Path
from seceval.convert import html_to_text
from seceval.crawler import TypedContent
from seceval.loader.base.file import FileLoader
from seceval.loader.base import LoaderBase, LoaderType
from typing import List
import re


class WinSecDocLoader(FileLoader):
    task_name = "windows_security"
    # git clone --depth 1 https://github.com/MicrosoftDocs/windows-itpro-docs.git
    dirname = "/nfs_ml/datasets/SecEval/SystemSecurity/raw/windows-itpro-docs/windows/security"

    recursive = True
    filename_pattern = "*.md"
    parser_profile = {}
