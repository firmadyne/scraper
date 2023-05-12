from scrapy import Spider
from scrapy.http import Request
from selenium import webdriver

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader

class EdimaxDESpider(Spider):
    name = "edimax_de"
    vendor = "Edimax"

    start_urls = ["https://www.edimax.com/edimax/download/download/data/edimax/de/download/"]

    def parse(self, response):
        pass
