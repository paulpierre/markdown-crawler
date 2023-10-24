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

# Overview
This is a multithreaded web crawler that crawls a website and creates markdown files for each page.
It was primarily created for large language model document parsing to simplify chunking and processing of large documents for RAG use cases.
Markdown by nature is human readable and maintains document structure while keeping a small footprint.

### Features include
- 🧵 Threading support for faster crawling
- ⏬ Set the max depth of children you wish to crawl
- ✅ Validates URLs, HTML, filepaths
- 🍲 Uses BeautifulSoup to parse HTML
- 🪵 Verbose logging option
- 👩‍💻 Ready-to-go CLI interface

# Quick start

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

# Requirements
- Python 3.x
- BeautifulSoup4
- requests


# Usage

The following arguments are supported
```
usage: md_crawler.py [-h] [--max_depth MAX_DEPTH] [--num_threads NUM_THREADS]
                     [--base_path BASE_PATH] [--debug DEBUG]
                     base_url
```



# Thanks 👍
If you have an issues, please feel free to open an issue or submit a PR. You can reach me via DM on Twitter/X.

  - Follow me on [Twitter / X](https://x.com/paulpierre)
  - Give me a ⭐ on [Github](https://github.com/paulpierre)

# License
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

# html2text
`md_crawler` makes use of html2text by the late and legendary [Aaron Swartz](me@aaronsw.com). The original source code can be found [here](http://www.aaronsw.com/2002/html2text). A modification was implemented to make it compatible with Python 3.x. It is licensed under GNU General Public License (GPL).