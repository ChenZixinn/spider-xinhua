import sys
from functools import partial

import pandas as pd
import pymysql
from PyQt5 import QtWidgets, QtCore, Qt
from PyQt5.QtChart import QChartView, QChart, QPieSlice, QPieSeries
from PyQt5.QtCore import QUrl, QDate
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QTableWidgetItem
from pyecharts.charts import Pie, Bar, Grid
import pyecharts.options as opts
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from multiprocessing import Process, Manager

from sqlalchemy import NVARCHAR, VARCHAR, TEXT, DATETIME, create_engine

from utils.data_thread import DataThread
from ui.MainUi import Ui_MainWindow
from utils.Common import DB_STRING, IMG_PATH


def crawl(Q):
    process = CrawlerProcess(get_project_settings())

    # 'followall' is the name of one of the spiders of the project.
    process.crawl('news', Q=Q)
    process.start()  # the script will block here until the crawling is finished


class MainWin(Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui_MainWindow, self).__init__()
        self.browser_map = None
        self.setupUi(self)
        self.initUi()
        self.p = None

        pymysql.install_as_MySQLdb()
        # DB_STRING = 'mysql+mysqldb://账号:密码@127.0.0.1/数据库名?charset=utf8'
        self.conn = create_engine(DB_STRING)
        self.dtype_dict = {
            "contentId": NVARCHAR(length=255),  # id
            "title": VARCHAR(length=255),  # 标题
            "url": NVARCHAR(length=255),  # 链接
            "content": TEXT,  # 内容
            "date": DATETIME,  # 日期
            "publish": NVARCHAR(length=32),  # 出版社
            "editor": VARCHAR(length=32),  # 编辑人
        }


        # 事件绑定
        self.btn_start.clicked.connect(self.start_crawl)

        self.Q = Manager().Queue()
        self.data_thread = DataThread(self)
        self.progress_bar.setValue(1)

        self.btn_create.clicked.connect(self.table_create)
        self.btn_delete.clicked.connect(self.table_delete)
        self.btn_save.clicked.connect(self.table_save)
        self.btn_search_data.clicked.connect(self.search_data)

        self.search_data()

    def search_data(self):
        try:
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")

            sql = f"select * from news where `date` > '{start_date}' and `date` < '{end_date}'"
            df = pd.read_sql(sql, con=self.conn)
            if df.empty:
                return
            word_items = self.data_thread.get_word_items(df)
            x = [i[0] for i in word_items[:15]]
            y = [i[1] for i in word_items[:15]]
            pie = (
                Pie()
                    .add(
                    "",
                    word_items[:15],
                    center=["35%", "50%"],
                )
                    .set_global_opts(
                    legend_opts=opts.LegendOpts(pos_left="15%"),
                )
                    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
            )

            bar = (Bar()
                   .add_xaxis(x)
                   .add_yaxis("关键词", y)
                   .set_global_opts(title_opts=opts.TitleOpts(title="词频可视化分析",subtitle=""),
                                    legend_opts=opts.LegendOpts(is_show=False)))

            grid = Grid(init_opts=opts.InitOpts(width="1200px", height="500px"))
            grid.add(bar, opts.global_options.GridOpts(pos_left="65%"))
            grid.add(pie, opts.global_options.GridOpts(pos_right="60%"))
            grid.render("./img/search_data.html")
            # page = Page()
            # page.add(pie)
            # page.add(bar)
            # page.render("./img/search_data.html")
            wrapper1 = partial(self.search_data_map.load, QUrl(f'file://{IMG_PATH}search_data.html'))
            QtCore.QTimer.singleShot(0, wrapper1)

        except Exception as e:
            print(e)

    def table_delete(self):
        while self.news_table_widget.selectedIndexes():
            rowIdx = self.news_table_widget.selectedIndexes()[0]
            self.news_table_widget.removeRow(rowIdx.row())

    def table_save(self):
        if self.data_thread.spider_status == 1:
            num_rows = self.news_table_widget.rowCount()
            num_cols = self.news_table_widget.columnCount()
            if num_rows <= 0:
                return
            tmp_df = pd.DataFrame(
                columns=['title', 'date', "url", "publish", "editor", "content", "contentId"], index=range(num_rows))
            print(f"num_rows:{num_rows}")
            print(f"num_cols:{num_cols}")
            for i in range(num_rows):
                for j in range(num_cols):
                    print(self.news_table_widget.item(i, j).text())
                    tmp_df.iloc[i, j] = self.news_table_widget.item(i, j).text()
            tmp_df.dropna(axis=0, how='any', inplace=True)
            tmp_df.to_sql('news', con=self.conn, chunksize=10000, if_exists="replace", index=False,
                           dtype=self.dtype_dict)

    def table_create(self):
        if self.data_thread.spider_status == 1:
            print(self.news_table_widget.rowCount())
            self.news_table_widget.insertRow(self.news_table_widget.rowCount())
            self.news_table_widget.setItem(self.news_table_widget.rowCount()-1, 0, QTableWidgetItem(" "))
            self.news_table_widget.setItem(self.news_table_widget.rowCount()-1, 1, QTableWidgetItem(" "))
            self.news_table_widget.setItem(self.news_table_widget.rowCount()-1, 2, QTableWidgetItem(" "))
            self.news_table_widget.setItem(self.news_table_widget.rowCount()-1, 3, QTableWidgetItem(" "))
            self.news_table_widget.setItem(self.news_table_widget.rowCount()-1, 4, QTableWidgetItem(" "))
            self.news_table_widget.setItem(self.news_table_widget.rowCount()-1, 5, QTableWidgetItem(" "))
            self.news_table_widget.setItem(self.news_table_widget.rowCount()-1, 6, QTableWidgetItem(" "))
            self.news_table_widget.scrollTo(self.news_table_widget.model().index(self.news_table_widget.rowCount(), 0))

    def initUi(self):
        # 显示插件
        self.browser_map = QWebEngineView()
        self.word_pie_map = QWebEngineView()
        self.search_data_map = QWebEngineView()
        self.news_table_widget.setColumnWidth(0, 200)
        self.news_table_widget.setColumnWidth(1, 200)
        self.news_table_widget.setColumnWidth(2, 400)
        self.news_table_widget.setColumnWidth(3, 100)
        self.news_table_widget.setColumnWidth(4, 100)
        self.news_table_widget.setColumnWidth(5, 300)
        self.news_table_widget.setColumnWidth(6, 100)

        self.start_date.setDate(QDate.currentDate().addDays(-15))
        self.end_date.setDate(QDate.currentDate())

        cate = ["编辑人"]
        data = [1]
        pie = Pie()
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
        self.browser_map.load(QUrl(f'file://{IMG_PATH}editor_pie.html'))

        ###

        series = QPieSeries()


        # adding slice

        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.addSeries(series)
        self.chart.createDefaultAxes()
        # self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setTitle("编辑人")

        # self.chart.legend().setVisible(True)
        # self.chart.legend().setAlignment(Qt.Qt.AlignRight)

        chartview = QChartView(self.chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        self.chart.removeAllSeries()

        # self.setCentralWidget(chartview)

        ###

        # 加载外部的web界面
        self.layout_word_pie.addWidget(self.word_pie_map)
        # self.layout_editor_pie.addWidget(self.browser_map)
        self.layout_editor_pie.addWidget(chartview)
        self.layout_search.addWidget(self.search_data_map)
        # self.news_table_widget.setHorizontalHeaderLabels(["新闻标题", "日期", "url", "出处", "编辑人"])
        # self.news_table_widget.horizontalHeader().setVisible(True)

    def start_crawl(self):
        if self.btn_start.text() == '开始爬取':
            self.btn_start.setText('停止爬取')
            if not self.p:
                self.p = Process(target=crawl, args=(self.Q,))
                self.p.start()
                self.data_thread.start()
                self.data_thread.start_status = 1
                self.news_table_widget.setRowCount(0)
                self.news_table_widget.clearContents()
            else:
                self.data_thread.start_status = 1
        else:
            self.btn_start.setText('开始爬取')
            self.data_thread.start_status = 0
            # self.p.terminate()
            # self.log_thread.count = 0
            # self.log_thread.terminate()



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWin()
    ui.show()
    sys.exit(app.exec_())

