```
                |                                     |             
 __ `__ \    _` |        __|   __|   _` | \ \  \   /  |   _ \   __| 
 |   |   |  (   |       (     |     (   |  \ \  \ /   |   __/  |    
_|  _|  _| \__._|      \___| _|    \__._|   \_/\_/   _| \___| _|    

----------------------------
md_crawler.py by @paulpierre
----------------------------
A multithreaded 🕸️ web crawler that recursively crawls a website and creates a 🔽 markdown file for each page
https://github.com/paulpierre
https://x.com/paulpierre                                                           
```
<br><br>

# 📝 Overview
This is a multithreaded web crawler that crawls a website and creates markdown files for each page.
It was primarily created for large language model document parsing to simplify chunking and processing of large documents for RAG use cases.
Markdown by nature is human readable and maintains document structure while keeping a small footprint.

<br>

## Features include

> - 🧵 Threading support for faster crawling
> - ⏯️ Continue scraping where you left off
> - ⏬ Set the max depth of children you wish to crawl
> - ✅ Validates URLs, HTML, filepaths
> - ⚙️ Configure list of valid base paths or base domains
> - 🍲 Uses BeautifulSoup to parse HTML
> - 🪵 Verbose logging option
> - 👩‍💻 Ready-to-go CLI interface

<br><br>

# 🚀 Get started

If you wish to simply use it in the CLI, you can run the following command:
```
pip install md_crawler
md_crawler -n 5 -d 3 -b ./markdown https://platform.openai.com/docs/introduction
```

From the github repo once you have it checked out:
```
pip3 install -r requirements.txt
python3 md_crawler.py -n 5 -d 3 -b ./markdown https://en.wikipedia.org/wiki/Morty_Smith
```

Or use the library in your own code:
```
from md_crawler import md_crawl
url = 'https://en.wikipedia.org/wiki/Morty_Smith'
md_crawl(url, max_depth=3, num_threads=5, base_path='markdown')
```
<br><br>

# ⚠️  Requirements


- Python 3.x
- BeautifulSoup4
- requests

<br><br>
# 🔍 Usage

The following arguments are supported
```
usage: md_crawler [-h] [--max-depth MAX_DEPTH] [--num-threads NUM_THREADS] [--base-path BASE_PATH] [--debug DEBUG]
                  [--target-content TARGET_CONTENT] [--target-links TARGET_LINKS] [--valid-paths VALID_PATHS]
                  [--domain-match DOMAIN_MATCH] [--base-path-match BASE_PATH_MATCH]
                  base-url
```

<br><br>

# 📝 Example
Take a look at [example.py](https://github.com/paulpierre/md_crawler/blob/main/example.py) for an example
implementation of the library. In this configuration we set:
- `max_depth` to 3. We will crawl the base URL and 3 levels of children
- `num_threads` to 5. We will use 5 parallel(ish) threads to crawl the website
- `base_dir` to `markdown`. We will save the markdown files in the `markdown` directory
- `valid_paths` an array of valid relative URL paths. We will only crawl pages that are in this list and base path
- `is_domain_match` to `False`. We will only crawl pages that are in the same domain as the base URL
- `is_base_match` to `False`. We will include all URLs in the same domain, even if they don't begin with the base url
- `is_debug` to True. We will print out verbose logging
<br><br>

And when we run it we can view the progress
<br>
> ![cli](https://github.com/paulpierre/md_crawler/blob/main/img/ss_crawler.png?raw=true)

We can see the progress of our files in the `markdown` directory locally
> ![md](https://github.com/paulpierre/md_crawler/blob/main/img/ss_dir.png?raw=true)

And we can see the contents of the HTML converted to markdown
> ![md](https://github.com/paulpierre/md_crawler/blob/main/img/ss_markdown.png?raw=true)

<br><br>
# ❤️ Thanks 
If you have an issues, please feel free to open an issue or submit a PR. You can reach me via DM on Twitter/X.

  - Follow me on [Twitter / X](https://x.com/paulpierre)
  - Give me a ⭐ on [Github](https://github.com/paulpierre)


<br><br>
# ⚖️ License
MIT License
Copyright (c) 2023 Paul Pierre
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

<br><br>

###  html2text credits
`md_crawler` makes use of html2text by the late and legendary [Aaron Swartz](me@aaronsw.com). The original source code can be found [here](http://www.aaronsw.com/2002/html2text). A modification was implemented to make it compatible with Python 3.x. It is licensed under GNU General Public License (GPL).