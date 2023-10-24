from bs4 import BeautifulSoup
import urllib.parse
import threading
from md_crawler import html2text
import requests
import argparse
import logging
import queue
import time
import os
import re
from typing import (
    List,
    Optional,
    Union
)
__version__ = '0.1'
__author__ = 'Paul Pierre (github.com/paulpierre)'
__copyright__ = "(C) 2023 Paul Pierre. MIT License."
__contributors__ = ['Paul Pierre']

BANNER = """
                |                                     |             
 __ `__ \    _` |        __|   __|   _` | \ \  \   /  |   _ \   __| 
 |   |   |  (   |       (     |     (   |  \ \  \ /   |   __/  |    
_|  _|  _| \__._|      \___| _|    \__._|   \_/\_/   _| \___| _|    

-------------------------------------------------------------------------
A multithreaded 🕸️ web crawler that recursively crawls a website and
creates a 🔽 markdown file for each page by https://github.com/paulpierre
-------------------------------------------------------------------------
"""

logger = logging.getLogger(__name__)
DEFAULT_BASE_PATH = 'markdown'
DEFAULT_MAX_DEPTH = 3
DEFAULT_NUM_THREADS = 5
DEFAULT_TARGET_CONTENT = ['article', 'div', 'main', 'p']
DEFAULT_TARGET_LINKS = ['body']
DEFAULT_DOMAIN_MATCH = True
DEFAULT_BASE_PATH_MATCH = True

# --------------
# URL validation
# --------------
def is_valid_url(url: str) -> bool:
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        logger.debug(f'❌ Invalid URL {url}')
        return False


# ----------------
# Clean up the URL
# ----------------
def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), None, None, None))


# ------------------
# HTML parsing logic
# ------------------
def crawl(
    url: str,
    base_url: str,
    already_crawled: set,
    file_path: str,
    target_links: Union[str, List[str]] = DEFAULT_TARGET_LINKS,
    target_content: Union[str, List[str]] = None,
    valid_paths: Union[str, List[str]] = None,
    is_domain_match: Optional[bool] = DEFAULT_DOMAIN_MATCH,
    is_base_match: Optional[bool] = DEFAULT_BASE_PATH_MATCH
) -> List[str]:
    if url in already_crawled:
        return []
    try:
        logger.debug(f'Crawling: {url}')
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        logger.error(f'❌ Request error for {url}: {e}')
        return []
    if 'text/html' not in response.headers.get('Content-Type', ''):
        logger.error(f'❌ Content not text/html for {url}')
        return []
    already_crawled.add(url)

    # -------------------------------
    # Create BS4 instance for parsing
    # -------------------------------
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # --------------------------------------------
    # Write the markdown file if it does not exist
    # --------------------------------------------
    if not os.path.exists(file_path):
        h = html2text.HTML2Text()
        h.ignore_images = True
        h.ignore_links = True

        file_name = file_path.split("/")[-1]

        # ------------------
        # Get target content
        # ------------------
        content = get_target_content(soup, target_content,)
        
        # ---------------
        # Return if empty
        # --------------
        if not content:
            logger.error(f'❌ Empty content for {file_path}. Please check your targets, skipping. ')
            return []
        
        # --------------
        # Parse markdown
        # --------------
        md = h.handle(content)
        
        logger.info(f'Created 📝 {file_name}')
       
        # ------------------------------
        # Write markdown content to file
        # ------------------------------
        with open(file_path, 'w') as f:
            f.write(md)
    
    child_urls = get_target_links(
        soup,
        base_url,
        target_links,
        valid_paths=valid_paths,
        is_domain_match=is_domain_match,
        is_base_match=is_base_match    
    )

    logger.debug(f'Found {len(child_urls) if child_urls else 0} child URLs')
    return child_urls


def get_target_content(
    soup: BeautifulSoup,
    target_content: Union[List[str], None] = None
) -> str:
    
    content = ''

    # -------------------------------------
    # Get target content by target selector
    # -------------------------------------
    if target_content:
        for tag in soup.find_all(target_content):
            logger.debug(f'🔥 Target content: {target_content} {str(tag)}')
            # Get tag html
            content += f'{str(tag)}'

    # ---------------------------
    # Naive estimation of content
    # ---------------------------
    else:
        max_text_length = 0
        for tag in soup.find_all(DEFAULT_TARGET_CONTENT):
            text_length = len(tag.get_text())
            if text_length > max_text_length:
                max_text_length = text_length
                main_content = tag
    
        content = str(main_content)

    return content if len(content) > 0 else False


def get_target_links(
    soup: BeautifulSoup,
    base_url: str,
    target_links: List[str] = DEFAULT_TARGET_LINKS,
    valid_paths: Union[List[str], None] = None,
    is_domain_match: Optional[bool] = DEFAULT_DOMAIN_MATCH,
    is_base_match: Optional[bool] = DEFAULT_BASE_PATH_MATCH
)-> List[str]:

    child_urls = []

    # Get all urls from target_links
    for target in soup.find_all(target_links):
        # Get all the links in target
        for link in target.find_all('a'):
            child_urls.append(urllib.parse.urljoin(base_url, link.get('href')))

    
    result = []
    for u in child_urls:
        
        child_url = urllib.parse.urlparse(u)

        # ---------------------------------
        # Check if domain match is required
        # ---------------------------------
        if is_domain_match and child_url.netloc != urllib.parse.urlparse(base_url).netloc:
            continue

        if is_base_match and child_url.path.startswith(urllib.parse.urlparse(base_url).path):
            result.append(u)
            continue
        
        if valid_paths:
            for valid_path in valid_paths:
                if child_url.path.startswith(urllib.parse.urlparse(valid_path).path):
                    result.append(u)
                    break
        
    return result    


# ------------------
# Worker thread logic
# ------------------
def worker(
    q: object,
    base_url: str,
    max_depth: int,
    already_crawled: set,
    base_path: str,
    target_links: Union[List[str], None] = DEFAULT_TARGET_LINKS,
    target_content: Union[List[str], None] = None,
    valid_paths: Union[List[str], None] = None,
    is_domain_match: bool = None,
    is_base_match: bool = None
) -> None:
    while not q.empty():
        depth, url = q.get()
        if depth > max_depth:
            continue
        file_name = '-'.join(re.findall(r'\w+', urllib.parse.urlparse(url).path))
        file_name = 'index' if not file_name else file_name
        file_path = f'{base_path.rstrip("/") + "/"}{file_name}.md'

        child_urls = crawl(
            url,
            base_url,
            already_crawled,
            file_path,
            target_links,
            target_content,
            valid_paths,
            is_domain_match,
            is_base_match
        )
        child_urls = [normalize_url(u) for u in child_urls]
        for child_url in child_urls:
            q.put((depth + 1, child_url))
        time.sleep(1)


# -----------------
# Thread management
# -----------------
def md_crawl(
        base_url: str,
        max_depth: Optional[int] = DEFAULT_MAX_DEPTH,
        num_threads: Optional[int] = DEFAULT_NUM_THREADS,
        base_path: Optional[str] = DEFAULT_BASE_PATH,
        target_links: Union[str, List[str]] = DEFAULT_TARGET_LINKS,
        target_content: Union[str, List[str]] = None,
        valid_paths: Union[str, List[str]] = None,
        is_domain_match: Optional[bool] = None,
        is_base_match: Optional[bool] = None,
        is_debug: Optional[bool] = False
) -> None:
    if is_domain_match is False and is_base_match is True:
        raise ValueError('❌ Domain match must be True if base match is set to True')

    is_domain_match = DEFAULT_DOMAIN_MATCH if is_domain_match is None else is_domain_match
    is_base_match = DEFAULT_BASE_PATH_MATCH if is_base_match is None else is_base_match

    if not base_url:
        raise ValueError('❌ Base URL is required')
    
    if isinstance(target_links, str):
        target_links = target_links.split(',') if ',' in target_links else [target_links]
    
    if isinstance(target_content, str):
        target_content = target_content.split(',') if ',' in target_content else [target_content]

    if isinstance(valid_paths, str):
        valid_paths = valid_paths.split(',') if ',' in valid_paths else [valid_paths]
    
    if is_debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug('🐞 Debugging enabled')
    
    logger.info(f'{BANNER}\n\n🕸️ Crawling {base_url} at ⏬ depth {max_depth} with 🧵 {num_threads} threads')

    # Validate the base URL
    if not is_valid_url(base_url):
        raise ValueError('❌ Invalid base URL')

    # Create base_path if it doesn't exist
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    already_crawled = set()

    # Create a queue of URLs to crawl
    q = queue.Queue()

    # Add the base URL to the queue
    q.put((0, base_url))

    threads = []

    # Create a thread for each URL in the queue
    for i in range(num_threads):
        t = threading.Thread(
            target=worker,
            args=(
                q,
                base_url,
                max_depth,
                already_crawled,
                base_path,
                target_links,
                target_content,
                valid_paths,
                is_domain_match,
                is_base_match
            )
        )
        threads.append(t)
        t.start()
        logger.debug(f'Started thread {i+1} of {num_threads}')

    # Wait for all threads to finish
    for t in threads:
        t.join()

    logger.info('🏁 All threads have finished')


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.description = 'A multithreaded 🕸️ web crawler that recursively crawls a website and creates a 🔽 markdown file for each page'
    arg_parser.add_argument('--max_depth', '-d', required=False, default=3, type=int)
    arg_parser.add_argument('--num_threads', '-t', required=False, default=5, type=int)
    arg_parser.add_argument('--base_path', '-b', required=False, default='markdown', type=str)
    arg_parser.add_argument('--debug', '-v', required=False, type=bool, default=False)
    arg_parser.add_argument('--target-content', '-c', required=False, type=str, default=None)
    arg_parser.add_argument('--target-links', '-l', required=False, type=str, default=DEFAULT_TARGET_LINKS)
    arg_parser.add_argument('--valid-paths', '-p', required=False, type=str, default=None)
    arg_parser.add_argument('--domain_match', '-d', required=False, type=bool, default=True)
    arg_parser.add_argument('--base-match', '-m', required=False, type=bool, default=True)
    arg_parser.add_argument('base_url', type=str)

    # ----------------
    # Parse target arg
    # ----------------
    target_content = args.target_content.split(',') if args.target_content and ',' in args.target_content else None
    target_links = args.target_links.split(',') if args.target_links and ',' in args.target_links else [args.target_links]
    valid_paths = args.valid_paths.split(',') if args.valid_paths and ',' in args.valid_paths else None
    domain_match = args.domain_match
    base_match = args.base_match
    args = arg_parser.parse_args()
    base_url = args.base_url
    debug = args.debug

    md_crawl(
        base_url,
        max_depth=args.max_depth,
        num_threads=args.num_threads,
        base_path=args.base_path,
        target_content=target_content,
        target_links=target_links,
        valid_paths=valid_paths,
        is_domain_match=domain_match,
        is_base_match=base_match,
        is_debug=debug
    )


# --------------
# CLI entrypoint
# --------------
if __name__ == '__main__':
    main()