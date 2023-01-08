# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pandas as pd
from pymysql.constants.FIELD_TYPE import CHAR
from sqlalchemy import create_engine
import pymysql
from sqlalchemy.types import NVARCHAR, DATETIME, TEXT,VARCHAR
from utils.Common import DB_STRING

class XinhuaNewsPipeline:
    df = pd.DataFrame()
    pymysql.install_as_MySQLdb()
    # DB_STRING = 'mysql+mysqldb://root:cat010320..@127.0.0.1/xinhua_news?charset=utf8'
    engine = None
    dtype_dict = {
        "contentId": NVARCHAR(length=255),  # id
        "title": VARCHAR(length=255),  # 标题
        "url": NVARCHAR(length=255),  # 链接
        "content": TEXT,  # 内容
        "date": DATETIME,  # 日期
        "publish": NVARCHAR(length=32),  # 出版社
        "editor": VARCHAR(length=32),  # 编辑人
    }

    def process_item(self, item, spider):
        data = pd.DataFrame.from_dict([item])
        self.df = pd.concat([self.df, data])
        # print(data)
        return item

    def open_spider(self, spider):
        # 开启爬虫时先填写好列名
        self.engine = create_engine(DB_STRING)
        # self.data

    def close_spider(self, spider):
        # 关闭时保存
        print("close")
        try:
            self.df.dropna(axis=0, how='any', inplace=True)
            self.df.to_sql('news', con=self.engine, chunksize=10000, if_exists="replace", index=False,
                           dtype=self.dtype_dict)
        except Exception as e:
            print(f"pipline error:{e}")