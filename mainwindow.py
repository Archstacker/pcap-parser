import sys
import os
import sqlite3
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_mainwindow import Ui_MainWindow

def debugHere():
    from PyQt4.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        self.initDB("data.db")
        self.initConstant()
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.initSrcHost()
        self.initDstHost()
        self.initSignal()

    def initConstant(self):
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBold.setWeight(75)
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setWeight(175)
        self.srcClicked = []
        self.dstClicked = []
        self.sqlAllFromHost="""
                select * from {0}HOST
                order by {0}NUM
                """
        self.sqlNeedBoldIP="""
                SELECT {0}IP FROM {0}HOST
                WHERE {0}NUM IN
                (        SELECT DISTINCT {0}NUM FROM STREAM
                    WHERE {1}NUM IN
                        (SELECT {1}NUM FROM {1}HOST
                         WHERE {1}IP IN 
                          ({2})
                        )
                )
                ORDER BY {0}NUM
        """


    def initDB(self, dbName):
        self.conn=sqlite3.connect(dbName)
        self.cursor=self.conn.cursor()
        self.conn.row_factory = sqlite3.Row
        self.rawcursor=self.conn.cursor()

    def initSrcHost(self):
        self.srcHostModel = QStandardItemModel(self.srcHostList)
        sqlQuery = self.sqlAllFromHost.format('SRC')
        sqlResult = self.cursor.execute(sqlQuery).fetchall()
        self.srcHostModel.clear()
        for host in sqlResult:
            item = QStandardItem(host[1])
            item.setCheckable(True)
            item.setFont(self.fontNormal)
            self.srcHostModel.appendRow(item)
        self.srcHostList.setModel(self.srcHostModel)

    def initDstHost(self):
        self.dstHostModel = QStandardItemModel(self.dstHostList)
        sqlQuery = self.sqlAllFromHost.format('Dst')
        sqlResult = self.cursor.execute(sqlQuery).fetchall()
        self.dstHostModel.clear()
        for host in sqlResult:
            item = QStandardItem(host[1])
            item.setCheckable(True)
            item.setFont(self.fontNormal)
            self.dstHostModel.appendRow(item)
        self.dstHostList.setModel(self.dstHostModel)

    def srcHostClicked(self, item):
        selectedIP = str(item.text())
        if (selectedIP in self.srcClicked) ^ (not item.checkState()):
            return

        if item.checkState():
            self.srcClicked.append(selectedIP)
        else:
            self.srcClicked.pop(self.srcClicked.index(selectedIP))
        sqlQuery=self.sqlNeedBoldIP.format('DST','SRC','"%s"' % '","'.join(self.srcClicked))
        sqlResult = self.cursor.execute(sqlQuery).fetchall()
        i = 0
        while self.dstHostModel.item(i):
            if str(self.dstHostModel.item(i).text()) in str(sqlResult):
                self.dstHostModel.item(i).setFont(self.fontBold)
            else:
                self.dstHostModel.item(i).setFont(self.fontNormal)
            i = i + 1

    def dstHostClicked(self, item):
        print 'enter'
        selectedIP = str(item.text())
        if (selectedIP in self.dstClicked) ^ (not item.checkState()):
            return
        print 'here'

        if item.checkState():
            self.dstClicked.append(selectedIP)
        else:
            self.dstClicked.pop(self.dstClicked.index(selectedIP))
        sqlQuery=self.sqlNeedBoldIP.format('SRC','DST','"%s"' % '","'.join(self.dstClicked))
        sqlResult = self.cursor.execute(sqlQuery).fetchall()
        i = 0
        while self.srcHostModel.item(i):
            if str(self.srcHostModel.item(i).text()) in str(sqlResult):
                self.srcHostModel.item(i).setFont(self.fontBold)
            else:
                self.srcHostModel.item(i).setFont(self.fontNormal)
            i = i + 1

    def initSignal(self):
        self.srcHostModel.itemChanged.connect(self.srcHostClicked)
        self.dstHostModel.itemChanged.connect(self.dstHostClicked)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
