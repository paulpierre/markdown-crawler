# Changelog

All notable changes to `markdown-crawler` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.5] - 2026-06-26

### Fixed
- **#11** — `UnboundLocalError` in `get_target_content` when no tags are found. `main_content` is now initialized to `None` and checked before `str()` conversion.
- **#7** — `UnicodeEncodeError` on non-ASCII content. All file writes now use `encoding='utf-8'`.
- **#10** — `target_content` CSS selector handling. Null `href` links are now skipped in `get_target_links`.
- **#8** — JavaScript check bypass. A browser-like `User-Agent` header is now sent on all `requests.get` calls.

### Added
- **#9** — `exclude_paths` parameter for URL filtering. Available in `crawl()`, `get_target_links()`, `worker()`, `md_crawl()`, and the CLI (`-x` / `--exclude-paths`).
- **#20** — Configurable `heading_style` for markdownify (`ATX`, `ATX_CLOSED`, `UNDERLINE`, `SETEXT`). CLI flag: `-s` / `--heading-style`.
- **#17** — Proper `dependencies` in `pyproject.toml` (`beautifulsoup4`, `markdownify`, `requests`) enabling `uvx` support out of the box.
- Comprehensive test suite — 60 tests with 95% coverage across `__init__.py` (96%) and `cli.py` (88%).
- `dev` optional dependencies (`pytest`, `pytest-cov`) for contributors.

### Changed
- Minimum Python version bumped to 3.8.
- `pyproject.toml` now uses `[project.scripts]` instead of `[tool.poetry.scripts]`.

## [0.0.4] - 2024-01-15

### Changed
- Fixed CLI bug with argument parsing.
- Fixed CLI flags.
- Changed package name to `markdown-crawler`.
- Migrated to Poetry for dependency management.

## [0.0.3] - 2023-12-20

### Added
- Initial PyPI release.
- Multithreaded web crawler with configurable depth, threads, and target selectors.
- CLI interface via `markdown-crawler` command.
- BeautifulSoup HTML parsing with markdownify conversion.
- Support for `valid_paths`, `target_content`, `target_links`, domain matching, and base path matching.
