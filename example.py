from md_crawler import md_crawl
url = 'https://rickandmorty.fandom.com/wiki/Evil_Morty'
print(f'🕸️ Starting crawl of {url}')
md_crawl(
    url,
    max_depth=4,
    num_threads=5,
    base_path='markdown',
    valid_paths=['/wiki'],
    is_domain_match=True,
    is_base_match=False,
    is_debug=True
)