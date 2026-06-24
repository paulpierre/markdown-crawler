"""
Comprehensive test suite for markdown_crawler.
Covers URL validation, normalization, content extraction, link discovery,
excluded paths, file writing with UTF-8 encoding, heading styles,
user-agent injection, and crawl orchestration.
"""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest
from bs4 import BeautifulSoup

from markdown_crawler import (
    is_valid_url,
    normalize_url,
    crawl,
    get_target_content,
    get_target_links,
    worker,
    md_crawl,
    DEFAULT_BASE_DIR,
    DEFAULT_MAX_DEPTH,
    DEFAULT_NUM_THREADS,
    DEFAULT_DOMAIN_MATCH,
    DEFAULT_BASE_PATH_MATCH,
    DEFAULT_TARGET_CONTENT,
    DEFAULT_TARGET_LINKS,
    DEFAULT_HEADING_STYLE,
    DEFAULT_USER_AGENT,
    BANNER,
)
from markdown_crawler.cli import main as cli_main


# ──────────────────── HTML fixtures ────────────────────

SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Page</title><script>alert('hi');</script><style>body{}</style></head>
<body>
  <main>
    <article>
      <h1>Hello World</h1>
      <p>This is a test paragraph with some content that is long enough to be selected.</p>
      <p>Another paragraph here with more text to increase total length.</p>
      <a href="/page1">Page 1</a>
      <a href="/page2">Page 2</a>
      <a href="https://external.com/page3">External</a>
    </article>
  </main>
  <footer><a href="/about">About</a></footer>
</body>
</html>
"""

EMPTY_HTML = """
<!DOCTYPE html>
<html><head></head><body></body></html>
"""

UNICODE_HTML = """
<!DOCTYPE html>
<html><body><main><article>
<h1>Café résumé naïve</h1>
<p>日本語のテキスト emoji 🎉 — special chars: "smart quotes" &mdash; — ñ ç ü</p>
<a href="/café">Café link</a>
</article></main></body></html>
"""

NO_TARGET_HTML = """
<!DOCTYPE html>
<html><body>
<div>short</div>
<div>This is a longer div with more text content than the other one so it should be picked as main content.</div>
<div>mid</div>
</body></html>
"""

JS_CHECK_HTML = """
<!DOCTYPE html>
<html><body>
<noscript>Please enable JavaScript</noscript>
<main><article><h1>JS Required</h1><p>Content behind JS check</p></article></main>
</body></html>
"""

NESTED_LINKS_HTML = """
<!DOCTYPE html>
<html><body>
<main>
  <a href="/wiki/page1">P1</a>
  <a href="/wiki/page2">P2</a>
  <a href="/admin/login">Admin</a>
  <a href="/blog/post1">Blog</a>
</main>
</body></html>
"""


def make_soup(html):
    return BeautifulSoup(html, 'html.parser')


def make_response(html, content_type='text/html; charset=utf-8'):
    resp = MagicMock()
    resp.text = html
    resp.headers = {'Content-Type': content_type}
    return resp


# ──────────────────── is_valid_url ────────────────────

class TestIsValidUrl:
    def test_valid_http(self):
        assert is_valid_url('http://example.com') is True

    def test_valid_https(self):
        assert is_valid_url('https://example.com') is True

    def test_valid_with_path(self):
        assert is_valid_url('https://example.com/path/to/page') is True

    def test_invalid_no_scheme(self):
        assert is_valid_url('example.com') is False

    def test_invalid_no_netloc(self):
        assert is_valid_url('https://') is False

    def test_invalid_empty(self):
        assert is_valid_url('') is False

    def test_invalid_none(self):
        """None input should return False, not crash."""
        result = is_valid_url(None)
        assert result is False


# ──────────────────── normalize_url ────────────────────

class TestNormalizeUrl:
    def test_strips_trailing_slash(self):
        assert normalize_url('https://example.com/path/') == 'https://example.com/path'

    def test_strips_query_params(self):
        assert normalize_url('https://example.com/path?foo=bar') == 'https://example.com/path'

    def test_strips_fragment(self):
        assert normalize_url('https://example.com/path#section') == 'https://example.com/path'

    def test_strips_all(self):
        assert normalize_url('https://example.com/path/?a=1#frag') == 'https://example.com/path'

    def test_no_trailing_slash(self):
        assert normalize_url('https://example.com/path') == 'https://example.com/path'

    def test_root(self):
        assert normalize_url('https://example.com/') == 'https://example.com'


# ──────────────────── get_target_content ────────────────────

class TestGetTargetContent:
    def test_with_css_selector(self):
        soup = make_soup(SIMPLE_HTML)
        result = get_target_content(soup, target_content=['article'])
        assert 'Hello World' in result
        assert 'test paragraph' in result

    def test_with_div_selector(self):
        soup = make_soup(SIMPLE_HTML)
        result = get_target_content(soup, target_content=['main'])
        assert 'Hello World' in result

    def test_auto_content_selection(self):
        soup = make_soup(NO_TARGET_HTML)
        result = get_target_content(soup, target_content=None)
        assert 'longer div' in result

    def test_empty_html_returns_false(self):
        soup = make_soup(EMPTY_HTML)
        result = get_target_content(soup, target_content=None)
        assert result is False

    def test_target_content_no_match(self):
        soup = make_soup(SIMPLE_HTML)
        result = get_target_content(soup, target_content=['.nonexistent-class'])
        assert result is False

    def test_multiple_selectors(self):
        soup = make_soup(SIMPLE_HTML)
        result = get_target_content(soup, target_content=['h1', 'p'])
        assert 'Hello World' in result
        assert 'test paragraph' in result

    def test_unbound_local_error_fix(self):
        """Regression test for issue #11: UnboundLocalError when no DEFAULT_TARGET_CONTENT tags found."""
        html = """
        <html><body>
        <custom-tag>Some content but not in standard tags</custom-tag>
        </body></html>
        """
        soup = make_soup(html)
        # Before fix: this would raise UnboundLocalError
        result = get_target_content(soup, target_content=None)
        # Should return False, not crash
        assert result is False

    def test_unicode_content(self):
        soup = make_soup(UNICODE_HTML)
        result = get_target_content(soup, target_content=['article'])
        assert 'Café' in result
        assert '日本語' in result


# ──────────────────── get_target_links ────────────────────

class TestGetTargetLinks:
    def test_basic_link_extraction(self):
        """With is_base_path_match=True, links starting with base path are included."""
        soup = make_soup(SIMPLE_HTML)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            is_domain_match=True,
            is_base_path_match=True
        )
        assert len(links) >= 2
        assert any('/page1' in u for u in links)
        assert any('/page2' in u for u in links)

    def test_domain_match_filters_external(self):
        soup = make_soup(SIMPLE_HTML)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            is_domain_match=True,
            is_base_path_match=True
        )
        assert all('external.com' not in u for u in links)

    def test_base_path_match_filters(self):
        soup = make_soup(SIMPLE_HTML)
        links = get_target_links(
            soup, 'https://example.com/docs',
            target_links=['body'],
            is_domain_match=True,
            is_base_path_match=True
        )
        # /page1 and /page2 don't start with /docs, so won't be included
        assert all('/page' not in u for u in links)

    def test_valid_paths(self):
        soup = make_soup(NESTED_LINKS_HTML)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            valid_paths=['/wiki'],
            is_domain_match=False,
            is_base_path_match=False
        )
        assert any('/wiki/page1' in u for u in links)
        assert any('/wiki/page2' in u for u in links)
        assert not any('/admin' in u for u in links)
        assert not any('/blog' in u for u in links)

    def test_exclude_paths(self):
        """Test exclude_paths feature from PR #9."""
        soup = make_soup(NESTED_LINKS_HTML)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            exclude_paths=['/admin'],
            is_domain_match=False,
            is_base_path_match=False,
            valid_paths=['/wiki', '/admin', '/blog']
        )
        assert any('/wiki/page1' in u for u in links)
        assert any('/blog/post1' in u for u in links)
        assert not any('/admin' in u for u in links)

    def test_exclude_paths_multiple(self):
        soup = make_soup(NESTED_LINKS_HTML)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            exclude_paths=['/admin', '/blog'],
            is_domain_match=False,
            is_base_path_match=False,
            valid_paths=['/wiki', '/admin', '/blog']
        )
        assert any('/wiki/page1' in u for u in links)
        assert not any('/admin' in u for u in links)
        assert not any('/blog' in u for u in links)

    def test_no_links_returns_empty(self):
        soup = make_soup(EMPTY_HTML)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            is_domain_match=False,
            is_base_path_match=False
        )
        assert links == []

    def test_none_href_skipped(self):
        """Ensure <a> tags without href are skipped."""
        html = '<html><body><a>no href</a><a href="/real">real</a></body></html>'
        soup = make_soup(html)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            is_domain_match=False,
            is_base_path_match=True
        )
        assert len(links) == 1
        assert '/real' in links[0]

    def test_exclude_paths_none_no_filtering(self):
        """exclude_paths=None should not filter anything."""
        soup = make_soup(NESTED_LINKS_HTML)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            exclude_paths=None,
            is_domain_match=False,
            is_base_path_match=False,
            valid_paths=['/wiki', '/admin', '/blog']
        )
        assert any('/admin' in u for u in links)

    def test_domain_filter_excludes_external(self):
        """External links are filtered when is_domain_match=True."""
        soup = make_soup(SIMPLE_HTML)
        links = get_target_links(
            soup, 'https://example.com',
            target_links=['body'],
            is_domain_match=True,
            is_base_path_match=True
        )
        for u in links:
            assert 'external.com' not in u


# ──────────────────── crawl ────────────────────

class TestCrawl:
    @patch('markdown_crawler.requests.get')
    def test_crawl_writes_file(self, mock_get, tmp_path):
        mock_get.return_value = make_response(SIMPLE_HTML)
        file_path = str(tmp_path / 'test-page.md')
        already = set()

        result = crawl(
            'https://example.com/page',
            'https://example.com',
            already,
            file_path,
            target_links=['body'],
            is_domain_match=True,
            is_base_path_match=False
        )

        assert os.path.exists(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'Hello World' in content

    @patch('markdown_crawler.requests.get')
    def test_crawl_returns_child_urls(self, mock_get):
        mock_get.return_value = make_response(SIMPLE_HTML)
        result = crawl(
            'https://example.com',
            'https://example.com',
            set(),
            '/tmp/test_crawl_urls.md',
            target_links=['body'],
            is_domain_match=True,
            is_base_path_match=True
        )
        assert len(result) >= 2

    @patch('markdown_crawler.requests.get')
    def test_crawl_skips_already_crawled(self, mock_get):
        mock_get.return_value = make_response(SIMPLE_HTML)
        already = {'https://example.com/page'}
        result = crawl(
            'https://example.com/page',
            'https://example.com',
            already,
            '/tmp/test_skip.md'
        )
        assert result == []
        mock_get.assert_not_called()

    @patch('markdown_crawler.requests.get')
    def test_crawl_request_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.exceptions.RequestException('Connection failed')
        result = crawl(
            'https://example.com/page',
            'https://example.com',
            set(),
            '/tmp/test_err.md'
        )
        assert result == []

    @patch('markdown_crawler.requests.get')
    def test_crawl_non_html_content(self, mock_get):
        mock_get.return_value = make_response('binary data', content_type='application/octet-stream')
        result = crawl(
            'https://example.com/file',
            'https://example.com',
            set(),
            '/tmp/test_bin.md'
        )
        assert result == []

    @patch('markdown_crawler.requests.get')
    def test_crawl_utf8_encoding(self, mock_get, tmp_path):
        """Regression test for issue #7: UnicodeEncodeError on non-ASCII content."""
        mock_get.return_value = make_response(UNICODE_HTML)
        file_path = str(tmp_path / 'cafe-resume.md')
        crawl(
            'https://example.com/café',
            'https://example.com',
            set(),
            file_path,
            target_links=['body'],
            is_domain_match=True,
            is_base_path_match=False
        )
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert 'Café' in content or 'café' in content.lower()

    @patch('markdown_crawler.requests.get')
    def test_crawl_user_agent_header(self, mock_get):
        """Test that a User-Agent header is sent (issue #8: JS check bypass)."""
        mock_get.return_value = make_response(SIMPLE_HTML)
        crawl(
            'https://example.com/page',
            'https://example.com',
            set(),
            '/tmp/test_ua.md',
        )
        call_args = mock_get.call_args
        assert 'headers' in call_args.kwargs
        assert call_args.kwargs['headers']['User-Agent'] == DEFAULT_USER_AGENT

    @patch('markdown_crawler.requests.get')
    def test_crawl_heading_style_atx(self, mock_get, tmp_path):
        """Test heading_style parameter (issue #20: markdownify options)."""
        html = '<html><body><main><article><h1>Title</h1><p>Body</p></article></main></body></html>'
        mock_get.return_value = make_response(html)
        file_path = str(tmp_path / 'heading.md')
        crawl(
            'https://example.com/page',
            'https://example.com',
            set(),
            file_path,
            heading_style='ATX',
            is_domain_match=True,
            is_base_path_match=False
        )
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert '#' in content  # ATX uses # for headings

    @patch('markdown_crawler.requests.get')
    def test_crawl_heading_style_underline(self, mock_get, tmp_path):
        html = '<html><body><main><article><h1>Title</h1><p>Body</p></article></main></body></html>'
        mock_get.return_value = make_response(html)
        file_path = str(tmp_path / 'heading_underline.md')
        crawl(
            'https://example.com/page',
            'https://example.com',
            set(),
            file_path,
            heading_style='UNDERLINE',
            is_domain_match=True,
            is_base_path_match=False
        )
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert '===' in content or '---' in content or '#' in content

    @patch('markdown_crawler.requests.get')
    def test_crawl_empty_content_no_file(self, mock_get, tmp_path):
        mock_get.return_value = make_response(EMPTY_HTML)
        file_path = str(tmp_path / 'empty.md')
        crawl(
            'https://example.com/empty',
            'https://example.com',
            set(),
            file_path
        )
        assert not os.path.exists(file_path)

    @patch('markdown_crawler.requests.get')
    def test_crawl_exclude_paths(self, mock_get):
        mock_get.return_value = make_response(NESTED_LINKS_HTML)
        result = crawl(
            'https://example.com',
            'https://example.com',
            set(),
            '/tmp/test_exclude_crawl.md',
            target_links=['body'],
            exclude_paths=['/admin'],
            is_domain_match=False,
            is_base_path_match=False,
            valid_paths=['/wiki', '/admin', '/blog']
        )
        assert not any('/admin' in u for u in result)

    @patch('markdown_crawler.requests.get')
    def test_crawl_strips_script_style(self, mock_get, tmp_path):
        mock_get.return_value = make_response(SIMPLE_HTML)
        file_path = str(tmp_path / 'stripped.md')
        crawl(
            'https://example.com/page',
            'https://example.com',
            set(),
            file_path,
            is_domain_match=True,
            is_base_path_match=False
        )
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "alert('hi')" not in content
            assert 'body{}' not in content


# ──────────────────── worker ────────────────────

class TestWorker:
    @patch('markdown_crawler.requests.get')
    def test_worker_processes_queue(self, mock_get, tmp_path):
        mock_get.return_value = make_response(SIMPLE_HTML)
        import queue as q_mod
        test_queue = q_mod.Queue()
        test_queue.put((0, 'https://example.com/page'))
        already = set()
        worker(
            test_queue, 'https://example.com', 1,
            already, str(tmp_path),
            is_domain_match=True, is_base_path_match=False
        )
        assert 'https://example.com/page' in already

    @patch('markdown_crawler.requests.get')
    def test_worker_respects_max_depth(self, mock_get):
        mock_get.return_value = make_response(SIMPLE_HTML)
        import queue as q_mod
        test_queue = q_mod.Queue()
        test_queue.put((5, 'https://example.com/deep'))
        already = set()
        worker(
            test_queue, 'https://example.com', 1,
            already, '/tmp/test_worker_depth',
            is_domain_match=True, is_base_path_match=False
        )
        mock_get.assert_not_called()


# ──────────────────── md_crawl ────────────────────

class TestMdCrawl:
    @patch('markdown_crawler.requests.get')
    def test_md_crawl_creates_directory(self, mock_get, tmp_path):
        mock_get.return_value = make_response(SIMPLE_HTML)
        base_dir = str(tmp_path / 'crawl_test')
        md_crawl(
            'https://example.com/page',
            max_depth=0,
            num_threads=1,
            base_dir=base_dir,
            is_domain_match=True,
            is_base_path_match=False
        )
        assert os.path.exists(base_dir)

    def test_md_crawl_invalid_url(self):
        with pytest.raises(ValueError, match='Invalid base URL'):
            md_crawl('not-a-url', max_depth=0, num_threads=1)

    def test_md_crawl_empty_url(self):
        with pytest.raises(ValueError, match='Base URL is required'):
            md_crawl('', max_depth=0, num_threads=1)

    def test_md_crawl_domain_base_mismatch(self):
        with pytest.raises(ValueError, match='Domain match must be True'):
            md_crawl(
                'https://example.com',
                is_domain_match=False,
                is_base_path_match=True
            )

    @patch('markdown_crawler.requests.get')
    def test_md_crawl_string_args(self, mock_get, tmp_path):
        """Test that string arguments are properly split."""
        mock_get.return_value = make_response(SIMPLE_HTML)
        base_dir = str(tmp_path / 'string_args')
        md_crawl(
            'https://example.com/page',
            max_depth=0,
            num_threads=1,
            base_dir=base_dir,
            target_links='body,main',
            target_content='article,h1',
            valid_paths='/docs,/blog',
            exclude_paths='/admin,/login',
            is_domain_match=True,
            is_base_path_match=False
        )
        assert os.path.exists(base_dir)

    @patch('markdown_crawler.requests.get')
    def test_md_crawl_exclude_paths_string(self, mock_get, tmp_path):
        mock_get.return_value = make_response(NESTED_LINKS_HTML)
        base_dir = str(tmp_path / 'md_exclude_test')
        md_crawl(
            'https://example.com/page',
            max_depth=0,
            num_threads=1,
            base_dir=base_dir,
            exclude_paths='/admin,/login',
            is_domain_match=False,
            is_base_path_match=False
        )

    @patch('markdown_crawler.requests.get')
    def test_md_crawl_heading_style(self, mock_get, tmp_path):
        mock_get.return_value = make_response(SIMPLE_HTML)
        base_dir = str(tmp_path / 'heading_test')
        md_crawl(
            'https://example.com/page',
            max_depth=0,
            num_threads=1,
            base_dir=base_dir,
            heading_style='UNDERLINE',
            is_domain_match=True,
            is_base_path_match=False
        )


# ──────────────────── CLI ────────────────────

class TestCLI:
    def test_cli_help(self, capsys):
        with pytest.raises(SystemExit):
            sys.argv = ['markdown-crawler', '--help']
            cli_main()
        captured = capsys.readouterr()
        assert 'max-depth' in captured.out or 'usage' in captured.out.lower()

    @patch('markdown_crawler.cli.md_crawl')
    def test_cli_invokes_md_crawl(self, mock_md_crawl):
        sys.argv = [
            'markdown-crawler',
            '-d', '2',
            '-t', '3',
            '-b', '/tmp/cli_test',
            'https://example.com'
        ]
        cli_main()
        mock_md_crawl.assert_called_once()
        call_kwargs = mock_md_crawl.call_args.kwargs
        assert call_kwargs['max_depth'] == 2
        assert call_kwargs['num_threads'] == 3

    @patch('markdown_crawler.cli.md_crawl')
    def test_cli_exclude_paths(self, mock_md_crawl):
        sys.argv = [
            'markdown-crawler',
            '-x', '/admin,/login',
            '-b', '/tmp/cli_exclude',
            'https://example.com'
        ]
        cli_main()
        call_kwargs = mock_md_crawl.call_args.kwargs
        assert call_kwargs['exclude_paths'] == ['/admin', '/login']

    @patch('markdown_crawler.cli.md_crawl')
    def test_cli_heading_style(self, mock_md_crawl):
        sys.argv = [
            'markdown-crawler',
            '-s', 'UNDERLINE',
            '-b', '/tmp/cli_heading',
            'https://example.com'
        ]
        cli_main()
        call_kwargs = mock_md_crawl.call_args.kwargs
        assert call_kwargs['heading_style'] == 'UNDERLINE'


# ──────────────────── Constants & Exports ────────────────────

class TestConstants:
    def test_banner_exists(self):
        assert 'crawler' in BANNER.lower()
        assert 'paulpierre' in BANNER.lower()

    def test_defaults(self):
        assert DEFAULT_BASE_DIR == 'markdown'
        assert DEFAULT_MAX_DEPTH == 3
        assert DEFAULT_NUM_THREADS == 5
        assert DEFAULT_DOMAIN_MATCH is True
        assert DEFAULT_BASE_PATH_MATCH is True
        assert 'article' in DEFAULT_TARGET_CONTENT
        assert 'body' in DEFAULT_TARGET_LINKS

    def test_user_agent_exists(self):
        assert DEFAULT_USER_AGENT is not None
        assert 'Mozilla' in DEFAULT_USER_AGENT

    def test_heading_style_default(self):
        assert DEFAULT_HEADING_STYLE == 'ATX'
