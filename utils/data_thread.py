import time
from functools import partial

import jieba
import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, QUrl
from PyQt5.QtWidgets import QTableWidgetItem
from pyecharts.charts import Pie, Grid, Bar, Line, Page, WordCloud
import pyecharts.options as opts
from sqlalchemy import create_engine


class DataThread(QThread):
    """
    接收scrapy传来的数据
    """

    def __init__(self, gui):
        super(DataThread, self).__init__()
        self.gui = gui
        self.df = pd.DataFrame()
        self.count = 0
        self.spider_status = 1  # 0 不可编辑 1 可编辑状态
        self.start_status = 0
        try:
            self.df = pd.read_sql("select * from news", con=self.gui.conn)
            for key,val in self.df.iterrows():
                self.update_table(val)
            self.update_pie()
            self.word_analysis()
        except Exception as e:
            print(e)

    def run(self):
        while True:
            if self.start_status == 0:
                time.sleep(0.5)
                continue
            if not self.gui.Q.empty():
                self.data_dict = self.gui.Q.get()
                print(f"self.data_dict:{self.data_dict}")
                self.spider_status = 0
                df = pd.DataFrame.from_dict([self.data_dict["item"]])  # 数据
                df.dropna(inplace=True)
                if len(df) <= 0:
                    continue
                self.df = pd.concat([self.df, df])
                # print("进度：" + data_dict["process"])
                self.count += 1
                self.process = int(self.data_dict["process"])
                wrapper = partial(self.gui.crawl_len.setText, f'{self.count}条')
                QtCore.QTimer.singleShot(0, wrapper)
                wrapper1 = partial(self.gui.progress_bar.setValue, self.process)
                QtCore.QTimer.singleShot(0, wrapper1)
                # if self.count % 200 == 0 or self.process == 100:
                try:
                    print(f"self.process:{self.process}")
                    if self.process == 100:
                        self.spider_status = 1
                        self.word_analysis()
                        self.update_pie()
                        self.gui.search_data()
                        wrapper1 = partial(self.gui.btn_start.setText, "停止爬取")
                        QtCore.QTimer.singleShot(0, wrapper1)
                    self.update_table(self.data_dict["item"])
                except Exception as e:
                    print(f"datathread error : {e}")
                self.msleep(10)

    def update_table(self, item):
        self.gui.news_table_widget.insertRow(self.gui.news_table_widget.rowCount())
        self.gui.news_table_widget.setItem(self.gui.news_table_widget.rowCount()-1, 0, QTableWidgetItem(item["title"]))
        self.gui.news_table_widget.setItem(self.gui.news_table_widget.rowCount()-1, 1, QTableWidgetItem(str(item["date"])))
        self.gui.news_table_widget.setItem(self.gui.news_table_widget.rowCount()-1, 2, QTableWidgetItem(item["url"]))
        self.gui.news_table_widget.setItem(self.gui.news_table_widget.rowCount()-1, 3, QTableWidgetItem(item["publish"]))
        self.gui.news_table_widget.setItem(self.gui.news_table_widget.rowCount()-1, 4, QTableWidgetItem(item["editor"]))
        self.gui.news_table_widget.setItem(self.gui.news_table_widget.rowCount()-1, 5, QTableWidgetItem(item["content"]))
        self.gui.news_table_widget.setItem(self.gui.news_table_widget.rowCount()-1, 6, QTableWidgetItem(item["contentId"]))

    def update_pie(self):

        try:
            editor_counts = self.df['editor'].value_counts()
            cate = list(editor_counts.keys())[:20]
            data = list(editor_counts)[:20]
            pie = Pie(init_opts=opts.InitOpts("900px","400px"))
            pie.add("", [list(z) for z in zip(cate, data)]
                    # 数据标签展示
                    , label_opts=opts.LabelOpts(
                    position="outside",
                    formatter="{d}%", )
                    )
            #  设置其他配置项
            pie.set_global_opts(
                # 标题配置项
                title_opts=opts.TitleOpts(title="编辑人", pos_left='50%'),
                #  图例配置项
                legend_opts=opts.LegendOpts(
                    type_="scroll"
                    , pos_top="20%"
                    , pos_left="80%"
                    , orient="vertical"
                ),
            )
            pie.render("./img/editor_pie.html")

            wrapper2 = partial(self.gui.browser_map.load, QUrl(f'file://./img/editor_pie.html'))
            QtCore.QTimer.singleShot(0, wrapper2)
            # self.gui.browser_map.load(
            #     QUrl(f'file:///Users/chenzixin/Documents/Code/dan/spider_xinhua/img/editor_pie.html'))
        except Exception as e:
            print("error:")
            print(e)

    def get_word_items(self, df):
        word_count = {}
        for txt in df["title"].values:
            count = jieba.lcut(txt)
            for word in count:
                if len(word) < 2 or word in ['：', '—', '“', '”', ' ', '外交部', '发言人', '总统', '全球', '国际', '专访', '举行', '世界',
                                             '中方', '习近平']:
                    continue
                word_count[word] = word_count.get(word, 0) + 1

        word_items = list(word_count.items())
        word_items.sort(key=lambda x: x[1], reverse=True)
        return word_items

    def word_analysis(self):
        word_items = self.get_word_items(self.df)
        x = [i[0] for i in word_items[:10]]
        y = [i[1] for i in word_items[:10]]

        bar = (Bar()
               .add_xaxis(x)
               .add_yaxis("频次", y)
               .set_global_opts(title_opts=opts.TitleOpts(title="词频可视化分析",subtitle=""),
                                legend_opts=opts.LegendOpts(is_show=True)))

        line = (Line()
                .add_xaxis(x)
                .add_yaxis("频次", y)
                .set_global_opts(
                legend_opts=opts.LegendOpts(is_show=True)
            ))

        c1 = (
            WordCloud(init_opts=opts.InitOpts(width="1200px", height="300px"))
                .add(
                "",
                word_items[:40],
                word_size_range=[20, 100],
                textstyle_opts=opts.TextStyleOpts(font_family="cursive"),
            )
                .set_global_opts(title_opts=opts.TitleOpts(title="词云可视化展示"))
        )
        grid = Grid(init_opts=opts.InitOpts(width="1200px", height="350px"))
        grid.add(bar, opts.global_options.GridOpts(pos_left="55%"))
        grid.add(line, opts.global_options.GridOpts(pos_right="60%"))
        # grid.render("./img/word_analysis.html")
        # pie.render("./img/word_analysis.html")
        page = Page()
        page.add(grid)
        page.add(c1)
        page.render("./img/word_analysis.html")
        wrapper2 = partial(self.gui.word_pie_map.load,
                           QUrl(f'file://./img/word_analysis.html'))
        QtCore.QTimer.singleShot(0, wrapper2)


if __name__ == '__main__':
    DataThread("1")