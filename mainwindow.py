import sys
import os
import sqlite3
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_mainwindow import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        self.initDB("data.db")
        self.initConstant()
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.initSrcHost()
        self.initDstHost()

    def initConstant(self):
        self.boldFont = QFont()
        self.boldFont.setBold(True)
        self.boldFont.setWeight(75)
        self.normalFont = QFont()
        self.normalFont.setBold(False)
        self.normalFont.setWeight(175)


    def initDB(self, dbName):
        self.conn=sqlite3.connect(dbName)
        self.cursor=self.conn.cursor()
        self.conn.row_factory = sqlite3.Row
        self.rawcursor=self.conn.cursor()

    def initSrcHost(self):
        sqlQuery="""
                select * from SRCHOST
                order by SRCNUM
                """
        self.srcHostModel = QStandardItemModel(self.srcHostList)
        srcHostArr = self.cursor.execute(sqlQuery).fetchall()
        self.srcHostModel.clear()
        for host in srcHostArr:
            item = QStandardItem(host[1])
            item.setCheckable(True)
            item.setFont(self.normalFont)
            self.srcHostModel.appendRow(item)
        self.srcHostList.setModel(self.srcHostModel)

    def initDstHost(self):
        sqlQuery="""
                select * from DSTHOST
                order by DSTNUM
                """
        self.dstHostModel = QStandardItemModel(self.dstHostList)
        dstHostArr = self.cursor.execute(sqlQuery).fetchall()
        self.dstHostModel.clear()
        for host in dstHostArr:
            item = QStandardItem(host[1])
            item.setCheckable(True)
            item.setFont(self.normalFont)
            self.dstHostModel.appendRow(item)
        self.dstHostList.setModel(self.dstHostModel)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
