from scrapy import Spider
from scrapy.http import Request
from selenium import webdriver

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader


class DLinkDESpider(Spider):
    name = "d-link_de"
    vendor = "D-Link"
    pagecount = None

    # Set the start url to page one
    ajax_url = "https://eu.dlink.com/de/de/support/all-products?mode=ajax&target=products&page="
    start_urls = [ajax_url + "1"]

    def parse(self, response):
        if not self.pagecount:
            pagecount = response.css('div.grid__col.grid__col--12.pagecount div.product-item::attr(data-pagecount-total)').get()
            try:
                pagecount = int(pagecount)
            except ValueError:
                pass
            self.logger.debug("Total Pagecount : " + str(pagecount))
        current_page = response.css('div.grid__col.grid__col--12.pagecount div.product-item::attr(data-pagecount-current)').get()
        try:
            current_page = int(current_page)
        except ValueError:
            pass
        self.logger.debug("Current page : " + str(current_page))
        #Get the product page links from the current page and push them to parse_product method
        for product in response.css('.product-item__details-container'):
            model = product.css('div.product-item__number::text').get()
            link = product.css('a::attr(href)').get()
            #TODO find a useful way to parse the category
            category = "misc"
            yield response.follow(link, meta={"category": category, "product": model}, callback=self.parse_product)
        if current_page <= pagecount:
            current_page = current_page + 1
            yield Request("{0}{1}".format(self.ajax_url, str(current_page)))

    def parse_product(self, response):
        self.logger.debug("Parsing %s..." % response.url)
        #TODO check for revision element in response and redirect accordingly