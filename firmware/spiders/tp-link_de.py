from scrapy import Spider

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader
import re

import urllib.request, urllib.parse, urllib.error

class TPLinkDESpider(Spider):
    name = "tp-link_de"
    vendor = "TP-Link"
    test_mode = False
    test_mode_count = 0
    start_urls = ["https://www.tp-link.com/de/support/download/"]

    def parse(self, response):
        for product_group in response.css("div.item"):
            try:
                category = product_group.css("h2 span::text").get().strip()
            except:
                category = product_group.css("h2::text").get().strip()
            for product in product_group.css("a"):
                model = product.css("::text").get().strip()
                link = product.css("::attr(href)").get()

                if link[-1] == "/":
                    yield response.follow(link, meta={"category": category, "product":model}, callback=self.parse_product)
                else:
                    item = FirmwareLoader(item=FirmwareImage(), date_fmt=["%Y-%m-%d"])
                    item.add_value("vendor", self.vendor)
                    item.add_value("url", link)
                    item.add_value("product", model)
                    item.add_value("category", category)
                    yield item.load_item()

    def parse_product(self, response):
        self.logger.debug("Parsing %s..." % response.url)
        tmp = response.url.split('/')[-2]

        #The Version is here the Revision, so it must be changed to a Tag for FACT PUT
        #Also we need to find a way to parse the version from the binary in the zip file because TP-Link doesn't have the version numbers on their website
        #Problem is that the zip file isn't downloaded at this point in the scraping process
        version = "Rev 1"
        if tmp[0] != 'v':
            links=response.css("div.hardware-version dl.select-version li a::attr(href)").extract()
            if len(links):
                version = links[0].split('/')[-2]
                # Extract the numeric part from the version string
                numeric_part = re.findall(r'\d+', version)[0]
                # Construct the revised version string
                version = f"Rev{numeric_part}"
                del links[0]
                for link in links:
                    yield response.follow(link, meta=response.meta, callback=self.parse_product)
        elif tmp[0] == 'v':
            version = "Rev " + tmp[1:]
        firmwares=response.css("#content_Firmware > table")
        self.logger.debug("%s %s: %d binary firmware found." % (response.meta["product"], version, len(firmwares)))
        for firmware in firmwares:
            if self.test_mode and self.test_mode_count >= 15:
                break
            spans = firmware.css('tr.detail-info span')
            item = FirmwareLoader(
            item=FirmwareImage(), response=response, date_fmt=["%Y-%m-%d"])
            item.add_value("vendor", self.vendor)
            item.add_value("url", firmware.css("a::attr(href)").get())
            item.add_value("date", spans[1].css("::text").get().strip())
            item.add_value("language", spans[3].css("::text").get().strip())
            item.add_value("size", spans[5].css("::text").get().strip())
            item.add_value("description", "\n".join(firmware.css('td.more p').getall()))
            item.add_value("product", response.meta["product"])
            item.add_value("category", response.meta["category"])
            item.add_value("version", version)
            yield item.load_item()
            self.test_mode_count = self.test_mode_count + 1

        # gpl_source_codes=response.css("#content_GPL-Code a")
        # self.logger.debug("%s %s: %d gpl source code found." % (response.meta["product"], version, len(gpl_source_codes)))
        # for gpl in gpl_source_codes:
        #     item = FirmwareLoader(
        #     item=FirmwareImage(), response=response, date_fmt=["%d/%m/%Y"])
        #     item.add_value("vendor", self.vendor)
        #     item.add_value("url", gpl.css("a::attr(href)").get())
        #     item.add_value("product", response.meta["product"])
        #     item.add_value("category", response.meta["category"])
        #     item.add_value("version", version)
        #     yield item.load_item()
