from seceval.crawler import TypedContent
from seceval.loader.base.web import WebLoader
from seceval.entity import PageItem
from typing import List
import re


class MIT6858Loader(WebLoader):
    task_name: str = "mit6.858"
    base_url: str = "https://css.csail.mit.edu/"
    start_urls: List[str] = ["https://css.csail.mit.edu/6.858/2022/"]
    max_depth: int = 2
    use_browser: bool = False

    def filter_url(self, url: str, parent_url: str, depth: int):
        return re.search(r"/6.858/2022/lec/.*", url) and url.endswith(".txt")

    def filter_item(self, item: PageItem, depth: int = 0):
        return depth != 1
