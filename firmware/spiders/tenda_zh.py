#coding:utf-8
from scrapy import Spider
from scrapy.http import Request

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader

import json
import urllib.request, urllib.parse, urllib.error

class TendaZHSpider(Spider):
    name = "tenda_zh"
    vendor = "tenda"
    allowed_domains = ["tenda.com.cn"]
    start_urls = ["https://www.tenda.com.cn/service/download-cata-11.html"]

    def parse(self, response):
        for a in response.xpath("//ul[@class='hotlist  flex']/li/a"):
            product_url = "https:" + a.xpath("./@href").extract()[0]
            version = ""
            v = a.xpath("./span[@class='editons']/text()").extract()
            if len(v) != 0:
                version = v[0]
            product = ""
            p = a.xpath("./@title").extract()
            if len(p) != 0:
                product = p[0]

            yield Request(
                url = product_url,
                headers = {"Referer": response.url},
                meta = {
                    "product": product,
                    "version": version,
                },
                callback = self.parse_product)

    def parse_product(self, response):
        url = "https:" + response.xpath("//div[@class='onebtn']//a/@href").extract()[0]
        item = FirmwareLoader(
            item = FirmwareImage(), response = response)
        item.add_value(
            "version", response.meta['version'])
        item.add_value("url", url)
        item.add_value("product", response.meta['product'])
        item.add_value("vendor", self.vendor)
        yield item.load_item()
