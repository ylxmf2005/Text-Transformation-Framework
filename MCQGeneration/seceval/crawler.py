from typing import List
import aiohttp
import asyncio
import logging
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.chrome.options import Options
import time
from selenium.common.exceptions import WebDriverException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Global retry count
MAX_RETRIES = 3

# PageType str class is not needed since we're going to return MIME types as strings


class TypedContent(BaseModel):
    mime_type: str
    content: bytes
    title: str = ""


async def http_get_page(session, url: str) -> TypedContent:
    for i in range(MAX_RETRIES):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get(
                        "Content-Type", "application/octet-stream"
                    )
                    bytes_content = await response.read()  # Read as bytes
                    return TypedContent(
                        mime_type=content_type, content=bytes_content, title=""
                    )
                else:
                    logger.warning(
                        f"Attempt {i + 1} of {url} failed with status {response.status}"
                    )
        except aiohttp.ClientError as e:
            logger.warning(f"Attempt {i + 1} of {url} failed with error {e}")
        await asyncio.sleep(i**2)  # Exponential backoff
    logger.error(f"Failed to retrieve {url} after {MAX_RETRIES} attempts")
    return TypedContent(mime_type="text/plain", content=b"")


async def worker(sem, task):
    async with sem:
        return await task


async def do_crawl_urls(urls: List[str], max_concurrency: int) -> List[TypedContent]:
    async with aiohttp.ClientSession() as session:
        tasks = []
        sem = asyncio.Semaphore(max_concurrency)

        for url in urls:
            tasks.append(http_get_page(session, url))
        results = await asyncio.gather(*(worker(sem, task) for task in tasks))

        return results


def browser_get_page(url) -> TypedContent:
    options = Options()
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")

    for i in range(MAX_RETRIES):
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            time.sleep(2)  # Wait for page to load, may need to be adjusted
            content_type = (
                driver.execute_script("return document.contentType") or "text/html"
            )
            html_content = driver.page_source.encode("utf-8")
            title = driver.title
            driver.quit()
            return TypedContent(
                mime_type=content_type, content=html_content, title=title
            )
        except WebDriverException as e:
            logger.warning(f"Attempt {i + 1} of {url} failed with error {e}")
            time.sleep(i**2)  # Exponential backoff

    logger.error(f"Failed to retrieve {url} after {MAX_RETRIES} attempts")
    return TypedContent(mime_type="text/plain", content=b"")


def browser_crawl_urls(
    urls: List[str], max_concurrency: int = 10
) -> List[TypedContent]:
    logger.info(f"Crawling {len(urls)} urls with browser")
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        result = list(executor.map(browser_get_page, urls))
    logger.info(f"Crawling with browser done")
    return result


def crawl_urls(urls: List[str], max_concurrency: int = 10) -> List[TypedContent]:
    logger.info(f"Crawling {len(urls)} urls asynchronously")
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        do_crawl_urls(urls, max_concurrency=max_concurrency)
    )
    logger.info(f"Asynchronous crawling done")
    return result
