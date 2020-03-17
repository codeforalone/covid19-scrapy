#!/bin/bash

python3 -B scrapy_news.py
python3 -B scrapy_sources.py
python3 -B convert_data.py