from distutils.core import setup
setup(
    name='md_crawler',
    packages=['md_crawler'],
    version='0.1',
    license='MIT',
    description='A multithreaded 🕸️ web crawler that recursively crawls a website and creates a 🔽 markdown file for each page',
    author='Paul Pierre',
    author_email='hi@paulpierre.com',
    url='https://github.com/paulpierre/md_crawler',
    download_url='https://github.com/paulpierre/md_crawler/archive/v_01.tar.gz',
    keywords=['Markdown', 'Website', 'Crawler', 'LLM', 'RAG', 'scraper'],
    install_requires=[
        'beautifulsoup4',
        'requests'
    ],
    classifiers=[
        'Development Status :: 2 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Crawlers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    entry_points="""
        [console_scripts]
        md_crawler=md_crawler:main
    """
)
