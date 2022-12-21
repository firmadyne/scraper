from scrapy import Spider
from scrapy.http import Request, FormRequest, HtmlResponse

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader

import urllib.request
import urllib.parse
import urllib.error
import re

class BelkinSpider(Spider):
    name = "belkin"
    allowed_domains = ["belkin.com", "belkin.force.com"]
    start_urls = ["https://www.belkin.com/us/support-search?text=router"]

    def parse(self, response):
        yield from response.follow_all(css="a.prodPageLink", callback=self.parse_product)

    #https://www.belkin.com/us/support-product?pid=01t80000003L8FDAA0
    def parse_product(self, response):
        product = response.css(
            "div.support-product-details-block h1::text").get()
        yield from response.follow_all(css="div.support-product-details-block a[title='Downloads / Firmware']", meta={"product": product}, callback=self.parse_product_firmware)

    #https://www.belkin.com/us/support-article?articleNum=105643
    #https://www.belkin.com/us/support-article?articleNum=4929
    def parse_product_firmware(self, response):
        version = ""
        build = ""
        url = ""
        size = ""
        description = ""

        divs = response.css("#support-article-downloads > div")
        model = response.css("h1::text").get().replace(" Downloads","")
        for div in divs:
            if div.css("h2"):
                version = div.xpath(".//h2/*/text()").get().replace("Versin ","")
            elif div.css("h3"):
                for el in div.xpath(".//*"):
                    tag = el.xpath("name()").get()
                    if tag == "h3":
                        res_type = el.xpath(".//text()").get()
                        self.logger.debug("%s: %s=%s" % (response.meta['product'], tag, res_type))

                    elif tag == "span" or tag == "div":
                        tmp=el.xpath(".//a/@href").get()
                        if tmp:
                            url = tmp
                        for text in el.xpath(".//text()").getall():
                            text=text.strip()
                            matches = re.match(r"Ver\. ([\d\.]+)",text)
                            if matches:
                                build=matches[1]
                            matches = re.match(r"(\d+) [KMG]B",text)

                            if matches:
                                size=matches[1]
                        self.logger.debug("%s: %s=%s" % (response.meta['product'], tag, url))

                    elif tag == "ul":
                        description = res_type + "\n" + "\n".join(el.xpath(".//li//text()").getall())
                        self.logger.debug("%s: %s=%s" % (response.meta['product'], tag, description))
                        item = FirmwareLoader(item=FirmwareImage(),
                                            response=response,
                                            date_fmt=["%b %d, %Y", "%B %d, %Y",
                                                        "%m/%d/%Y"])
                        item.add_value("version", version)
                        item.add_value("model", model)
                        item.add_value("build", build)
                        item.add_value("url", url)
                        item.add_value("size", size)
                        item.add_value("description", description)
                        item.add_value("product", response.meta["product"])
                        item.add_value("vendor", self.name)
                        build = ""
                        url = ""
                        size = ""
                        description = ""

                        yield item.load_item()
                    elif tag == "a":
                        url = el.xpath("@href").get()
                    elif tag == "br":
                        self.logger.debug("%s: %s=%s" % (response.meta['product'], tag, ""))
                    else:
                        self.logger.warn("%s: %s=%s" % (response.meta['product'], tag, el.xpath(".//text()").get()))