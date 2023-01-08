from PyQt5.QtWidgets import *
from sqlalchemy import text

from ui.LoginUi import Ui_MainWindow  # 导入login文件
from utils.register import MainRegistWindow  # 导入注册文件
import sys
from utils.main import MainWin

global UserName
UserP = {}  # 定义一个存储密码账号的元组


class MainLoginWindow(Ui_MainWindow, QMainWindow):
    def __init__(self, parent=None):
        super(Ui_MainWindow, self).__init__()
        self.re = MainRegistWindow(self)  # 这边一定要加self
        self.setupUi(self)
        self.initUi()
        self.win = MainWin()

    def initUi(self):
        self.login_user.setFocus()
        self.login_user.setPlaceholderText("请输入账号")
        self.login_passwd.setPlaceholderText("请输入密码")
        self.login_passwd.setEchoMode(QLineEdit.Password)  # 密码隐藏

        self.btn_go_register.clicked.connect(self.regist_button)  # 跳转到注册页面
        self.re.SuccessReg.connect(self.Success_Regist)  # 注册或者取消跳转回来
        self.btn_login.clicked.connect(self.login_button)  # 登录

    # 注册
    def regist_button(self):
        # 载入数据库
        # self.sql = Oper_Mysql()
        # self.sql.ZSGC_Mysql()
        self.re.show()
        w.close()

    # 登录
    def login_button(self):
        login_user = self.login_user.text()
        login_passwd = self.login_passwd.text()
        # print(type(Login_User))
        # print(type(Login_Passwd))


        if login_user == 0 or login_passwd.strip() == '':
            QMessageBox.information(self, "error", "输入错误")
        else:
            select_params_dict = {
                'username': login_user,
                "password": login_passwd
            }

            ## use sqlalchemy bindparams to prevent sql injection
            pre_sql = 'select username, password from users where username = :username and password = :password'
            bind_sql = text(pre_sql)
            resproxy = self.win.conn.connect().execute(bind_sql, select_params_dict)
            row = resproxy.first()
            print(f"row:{row}")

            if row:  # 密码和账号都对的情况下
                mess = QMessageBox()
                mess.setWindowTitle("Success")
                mess.setText("登录成功")
                mess.setStandardButtons(QMessageBox.Ok)
                mess.button(QMessageBox.Ok).animateClick(1000)  # 弹框定时关闭
                mess.exec_()
                print("登录成功")
                """跳转到主界面"""
                self.win.show()
                w.close()
                return True
            else:
                QMessageBox.information(self, "error!", "密码输入错误", QMessageBox.Ok)
                return False

    # 退出
    def logout_button(self):
        # 警告对话框
        messageBox = QMessageBox(QMessageBox.Warning, "警告", "是否退出系统！")
        Qyes = messageBox.addButton(self.tr("确认"), QMessageBox.YesRole)
        Qno = messageBox.addButton(self.tr("取消"), QMessageBox.NoRole)
        messageBox.setDefaultButton(Qno)  # 默认焦点
        messageBox.exec_()  # 保持
        if messageBox.clickedButton() == Qyes:
            w.close()
        else:
            return

    # 成功注册
    def Success_Regist(self):
        w.show()
        self.re.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainLoginWindow()
    w.show()
    sys.exit(app.exec())

