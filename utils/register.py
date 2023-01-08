from PyQt5.QtWidgets import *
from ui.RegisterUi import Ui_MainWindow
from PyQt5.QtCore import pyqtSignal


class MainRegistWindow(Ui_MainWindow, QMainWindow):
    SuccessReg = pyqtSignal()  # 定义一个注册成功信号

    def __init__(self, parent=None):
        super(Ui_MainWindow, self).__init__()
        self.setupUi(self)
        self.initUI()
        self.parent = parent

    def initUI(self):
        self.register_user.setFocus()  #鼠标焦点
        self.register_user.setPlaceholderText("请输入注册账户")
        self.register_passwd.setPlaceholderText("请输入密码")
        self.confrim_register_passwd.setPlaceholderText("请确认密码")
        self.register_passwd.setEchoMode(QLineEdit.Password)  #密码隐藏
        self.confrim_register_passwd.setEchoMode(QLineEdit.Password)

        self.btn_register.clicked.connect(self.emit_Confir_Button) #确认
        self.btn_go_login.clicked.connect(self.go_login)

    def go_login(self):
        self.SuccessReg.emit()

    def emit_Account(self):
        print("Account发生改变")

    def emit_Username(self):
        print("UserName发生改变")

    def emit_Password(self):
        print("PassWord发生改变")

    def emit_ConPassword(self):
        print("ConPassword发生改变")

    def emit_identity(self):  # 发射身份信号
        print(self.comboBox.currentText())

    def emit_Confir_Button(self):
        if self.register_user.text().strip() == '' or self.register_passwd.text().strip() == '' \
                or self.confrim_register_passwd.text().strip() == '':
            try:
                QMessageBox.information(self, "error", "输入有误，请重新输入")
            except Exception as str:
                print("输入错误 %s" % (str))
        elif len(self.register_passwd.text()) < 6:
            QMessageBox.information(self, "warning", "密码小于6位")
        elif self.register_passwd.text() != self.confrim_register_passwd.text():
            try:
                QMessageBox.information(self, "error", "两次密码输入不一致")
            except Exception as str:
                print("未知错误 %s" % (str))
        else:
            # sql = Oper_Mysql()
            # query = QSqlQuery()
            #
            #
            username = self.register_user.text()
            password = self.register_passwd.text()
            # 插入变量
            s = self.parent.win.conn.connect().execute(
                "insert into users(username, password) values('%s', '%s')" % (
                username, password))
            if s:
                QMessageBox.information(self, "QAQ", "注册成功")
            else:
                QMessageBox.information(self, "QAQ", "注册失败, 该账户已经存在")

            self.SuccessReg.emit()

    def emit_Cancel(self):
        self.SuccessReg.emit()
