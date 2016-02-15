Introduction
============

This is a firmware scraper that aims to download firmware images and associated
metadata from supported device vendor websites.

Dependencies
============
* [psycopg2](http://initd.org/psycopg/)
* [scrapy](http://scrapy.org/)

Usage
=====

Configure the `scrapy/settings.py` file, including whether metadata about
downloaded firmware should be inserted into a SQL server.

To run a specific scraper, e.g. `dlink`:

`scrapy crawl dlink`

To run all scrapers with maximum 4 in parallel, using [GNU Parallel](https://www.gnu.org/software/parallel/):

```parallel -j 4 scrapy crawl ::: `for i in ./scraper/spiders/*.py; do basename ${i%.*}; done` ```
