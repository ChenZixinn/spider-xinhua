# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class XinhuaNewsItem(scrapy.Item):
    # define the fields for your item here like:
    contentId = scrapy.Field()  # id
    title = scrapy.Field()  # 标题
    url = scrapy.Field()  # 链接
    content = scrapy.Field()  # 内容
    date = scrapy.Field()  # 日期
    publish = scrapy.Field()  # 出版社
    editor = scrapy.Field()  # 编辑人
