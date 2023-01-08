import json
import math
from copy import deepcopy

import scrapy

from xinhua_news.items import XinhuaNewsItem


class NewsSpider(scrapy.Spider):
    name = 'news'
    allowed_domains = ['news.cn']
    Q = None
    start_urls = ['http://www.news.cn/world/ds_8d5294ed513c4779af6242a3623aa27b.json']
    count = 0
    process = 0
    data_len = 0

    def parse(self, response):
        self.data_json = json.loads(response.text)
        # 循环打开数据链接
        self.data_len = len(self.data_json["datasource"])
        for count, i in enumerate(self.data_json["datasource"]):
            # item
            item = XinhuaNewsItem()
            item["contentId"] = i["contentId"]
            item["title"] = i["linkUrls"][0]["linkTitle"]
            item["date"] = i["publishTime"]
            item["url"] = i["publishUrl"]

            # 请求失败不会进入callback
            yield scrapy.Request(i["publishUrl"], callback=self.get_news_detial, encoding="utf-8",dont_filter=True ,
                                 meta={"item": deepcopy(item), "process": 0, "count": 0})

    def get_news_detial(self, response):
        self.count += 1

        item = response.meta["item"]
        if response.xpath("//div[@class='source']/text()").extract():
            response.meta["item"]["publish"] = response.xpath("//div[@class='source']/text()").extract()[0].replace("\n","").replace("来源：","").replace(
                "\r", "")
        elif response.xpath("//span[@class='aticle-src']/text()").extract():
            response.meta["item"]["publish"] = response.xpath("//span[@class='aticle-src']/text()").extract()[0].replace("\n","").replace("\r", "")
        else:
            response.meta["item"]["publish"] = None
        if response.xpath("//div[@id='detail']"):
            response.meta["item"]["content"] = response.xpath("//div[@id='detail']")[0].xpath('string(.)').extract()[0].replace("\n", "").replace("\r", "").strip()
        elif response.xpath("//span[@id='content']"):
            response.meta["item"]["content"] = response.xpath("//span[@id='content']")[0].xpath('string(.)').extract()[0].replace("\n", "").replace("\r", "").strip()
        else:
            response.meta["item"]["content"] = None
        if response.xpath('//span[@class="editor"]/text()'):
            response.meta["item"]["editor"] = response.xpath('//span[@class="editor"]/text()').extract()[0].replace("责任编辑:","").replace("\n","").replace("\r", "").replace("【", "").replace("】", "").strip()
        else:
            response.meta["item"]["editor"] = None
        # print(item)
        # response.meta["count"] = self.count
        response.meta["process"] = 100 * self.count / self.data_len
        # print(f"len:{self.data_len}")
        self.Q.put(response.meta)
        return item
