from markdown_crawler import md_crawl
url = 'https://rickandmorty.fandom.com/wiki/Evil_Morty'
print(f'🕸️ Starting crawl of {url}')
md_crawl(
    url,
    max_depth=3,
    num_threads=5,
    base_dir='markdown',
    valid_paths=['/wiki'],
    target_content=['div#content'],
    is_domain_match=True,
    is_base_path_match=False,
    is_debug=True
)