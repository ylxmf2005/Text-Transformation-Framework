import trafilatura
import hashlib
import yaml
import subprocess
from bs4 import BeautifulSoup
import os
import re
import html2text
from tqdm import tqdm
from urllib.parse import urljoin
from lxml import etree

import logging

logger = logging.getLogger(__name__)


def html_to_md(html: str):
    # Create an html2text object
    h = html2text.HTML2Text()

    # Ignore converting links from HTML
    h.ignore_links = True
    h.ignore_images = True

    md = h.handle(html)
    return md


def xml_to_md(xml_string: str, heading_level: int = 1) -> str:
    """
    Convert all children of a given XML string to a single markdown string, considering their hierarchy.
    """
    xml_string = xml_string.strip()

    def get_local_tag(tag):
        return etree.QName(tag).localname

    def has_textual_content(node):
        """
        Check if the node or any of its descendants contain text.
        """
        if (node.text and not node.text.isspace()) or any(
            has_textual_content(child) for child in node.iterdescendants()
        ):
            return True
        return False

    def xml_node_to_md(node, level):
        markdown_parts = []
        h = html2text.HTML2Text()
        h.body_width = 0  # This will set the body width to unlimited which avoids unwanted line wraps

        # Get the local tag name without the namespace
        local_tag = get_local_tag(node.tag)

        # If the local_tag is a standard HTML tag, use html2text to convert it to Markdown.
        if local_tag.lower() in [
            "p",
            "div",
            "span",
            "b",
            "i",
            "strong",
            "em",
            "ul",
            "ol",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]:
            # Convert the entire node, including children, to a string and then to Markdown
            html_string = etree.tostring(node)
            markdown_parts.append(h.handle(html_string.decode("utf-8")))
        else:
            if has_textual_content(node):
                markdown_parts.append(f"{'#' * level} {local_tag}\n\n")
                if node.text and not node.text.isspace():
                    markdown_parts.append(node.text.strip() + "\n\n")

            for child in node.iterchildren():
                markdown_parts.append(xml_node_to_md(child, level + 1))

            if node.tail and not node.tail.isspace():
                markdown_parts.append(node.tail.strip() + "\n\n")

        return "".join(markdown_parts)

    # Parse the XML content
    root = etree.fromstring(xml_string, None)
    markdown_content = xml_node_to_md(root, heading_level)
    return markdown_content.strip()


def any_to_html(filepath: str) -> list:
    """
    @return [{'html': str, 'filename': str}]
    """
    output = subprocess.check_output(
        f"java -jar {os.path.dirname(__file__)}/tika-app-2.8.0.jar -h".split(" ")
        + [filepath],
        timeout=60,
    )
    soup = BeautifulSoup(output, "html.parser")
    body = soup.find("body")
    results = []
    if body == None:
        results.append(
            {
                "html": soup.encode_contents(),
            }
        )
        return results
    # detect pdf
    pages = body.findChildren("div", {"class": "page"}, recursive=False)  # type: ignore
    if len(pages) > 0:
        page_cnt = 1
        for page in pages:
            results.append({"html": page.encode_contents(), "filename": f"{page_cnt}"})
            page_cnt += 1
        return results

    # detect archives
    entries = body.findChildren("div", {"class": "package-entry"}, recursive=False)  # type: ignore
    if len(entries) > 0:
        for entry in entries:
            filename_elem = entry.find("h1", recursive=False)
            if filename_elem == None:
                continue
            filename = filename_elem.text
            filename_elem.decompose()
            children = entry.findChildren(recursive=False)
            if len(children) == 1:
                results.append(
                    {
                        "html": children[0].encode_contents(),
                        "filename": filename,
                    }
                )
            else:
                content = entry.encode_contents()
                results.append(
                    {
                        "html": content,
                        "filename": filename,
                    }
                )
        return results

    # default
    content = body.encode_contents()  # type: ignore
    results.append(
        {
            "html": body.encode_contents(),  # type: ignore
        }
    )
    return results


def html_to_main_text(html: str):
    return trafilatura.extract(html)


def html_to_text(raw_html):
    raw_html = raw_html.replace("<li>", "\n*")
    raw_html = raw_html.replace("</li>", "")
    raw_html = raw_html.replace("<ol>", "\n*")
    raw_html = raw_html.replace("</ol>", "")
    soup = BeautifulSoup(raw_html, "lxml")
    return soup.get_text()


def filter_text(text: str):
    newline_re = re.compile(r"\n{2,}")
    url_re = re.compile(
        r"([a-zA-Z0-9]{2,10}:\/\/)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b[-a-zA-Z0-9@:%_\+.~#?&//=]*"
    )
    text = url_re.sub("", text)
    text = newline_re.sub("\n\n", text)
    return text


def html_to_urls(html: str, base_url: str, current_url: str):
    soup = BeautifulSoup(html, "html.parser")
    url_attributes = ["href", "src", "action"]
    urls = []
    for attr in url_attributes:
        tags = soup.find_all(attrs={attr: True})
        for tag in tags:
            url = tag.get(attr)
            if url is not None:
                if url.startswith("/"):
                    url = urljoin(base_url, url)
                elif "://" not in url:
                    url = urljoin(current_url, url)
                urls.append(url)
    urls = list(set(urls))
    logger.info(f"Extracted {len(urls)} urls from {current_url}")
    return urls
