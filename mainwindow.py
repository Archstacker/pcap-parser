#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3
import hexdump
import tempfile
import subprocess
import shutil
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_mainwindow import Ui_MainWindow
from mytablemodel import MyTableModel
import createdb

def debugHere():
    from PyQt4.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.initConstant()
        self.initSignal()

    def pcapImport(self):
        pcapPath = QFileDialog.getOpenFileName(self,
                "Open Pcap",".",
                "Pcap File (*.pcap)");
        self.dbPath = createdb.createDB(pcapPath)
        self.initDB(str(self.dbPath))
        self.srcClicked = []
        self.dstClicked = []
        self.streamTableID = []
        self.initSrcHost()
        self.initDstHost()
        self.updateStream()

    def DBOpen(self):
        path = QFileDialog.getOpenFileName(self,
                "Open Database",".",
                "Sqlite Database (*.db)");
        self.initDB(str(path))
        self.srcClicked = []
        self.dstClicked = []
        self.streamTableID = []
        self.initSrcHost()
        self.initDstHost()
        self.updateStream()

    def initConstant(self):
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBold.setWeight(75)
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setWeight(175)
        self.streamTableHeader = [u'请求信息',u'返回信息', u'文件类型']
        self.headerTableHeader = ['Header', 'Data']
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
        self.sqlStreamIDBetween="""
            SELECT ID FROM STREAM
                WHERE SRCNUM IN
                    (SELECT SRCNUM FROM SRCHOST
                    WHERE SRCIP IN({0}))
                AND DSTNUM IN
                    (SELECT DSTNUM FROM DSTHOST
                    WHERE DSTIP IN({1}))
            ORDER BY SRCNUM
        """
        self.sqlStreamIDSingle="""
            SELECT ID FROM STREAM
                WHERE {0}NUM IN
                    (SELECT {0}NUM FROM {0}HOST
                    WHERE {0}IP IN({1}))
        """
        self.sqlStreamBetween="""
            SELECT SRCDESCRIPTION,DSTDESCRIPTION,FILETYPE FROM STREAM
            WHERE ID IN({})
        """
        self.sqlStreamIDAll="""
            SELECT ID FROM STREAM
        """
        self.sqlStreamInfo="""
                SELECT * FROM STREAM
                WHERE ID={}
        """
        self.sqlHTTPHeader="""
                SELECT COLUMNATTR FROM {0}HEADER 
                WHERE COLUMNID={1}
        """
        self.sqlGetNumByIP="""
                SELECT {0}NUM FROM {0}HOST
                WHERE {0}IP = ?
        """
        self.sqlDeleteIP="""
                DELETE FROM {0}HOST 
                WHERE {0}NUM = ?
        """
        self.sqlDeleteStreamByIP="""
                DELETE FROM STREAM
                WHERE {0}NUM = ?
        """
        self.sqlDeleteHost="""
                DELETE FROM {0}HOST
                WHERE {0}NUM NOT IN
                (SELECT DISTINCT {0}NUM 
                FROM STREAM)
        """
        self.sqlGetItemData="""
                SELECT DSTBODY FROM STREAM
                WHERE ID = ?
        """

    def initDB(self, dbName):
        try:
            self.conn.close()
        except:
            pass
        self.conn=sqlite3.connect(dbName)
        self.cursor=self.conn.cursor()
        self.conn.row_factory = sqlite3.Row
        self.rawcursor=self.conn.cursor()

    def initSignal(self):
        self.actionImport.triggered.connect(self.pcapImport)
        self.actionDBOpen.triggered.connect(self.DBOpen)
        self.actionFileSave.triggered.connect(self.fileSave)
        self.actionFileSaveAs.triggered.connect(self.fileSaveAs)
        self.actionPreview.triggered.connect(self.itemPreview)
        self.srcHostList.connect(self.srcHostList, SIGNAL('customContextMenuRequested(const QPoint &)'), self.srcHostRightClicked)
        self.dstHostList.connect(self.dstHostList, SIGNAL('customContextMenuRequested(const QPoint &)'), self.dstHostRightClicked)
        self.streamTable.clicked.connect(self.streamClicked)

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
        self.srcHostModel.itemChanged.connect(self.srcHostClicked)
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
        self.dstHostModel.itemChanged.connect(self.dstHostClicked)
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
        self.updateStream()

    def dstHostClicked(self, item):
        selectedIP = str(item.text())
        if (selectedIP in self.dstClicked) ^ (not item.checkState()):
            return

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
        self.updateStream()

    def updateStream(self):
        if(self.streamHeaders.itemAt(0) != None):
            self.streamHeaders.itemAt(0).widget().setParent(None)
            self.streamHeaders.itemAt(0).widget().setParent(None)
        if len(self.srcClicked)==0 and len(self.dstClicked)==0 :
            sqlQuery = self.sqlStreamIDAll
        elif len(self.srcClicked)!=0 and len(self.dstClicked)==0 :
            sqlQuery = self.sqlStreamIDSingle.format("SRC", '"%s"' % '","'.join(self.srcClicked))
        elif len(self.dstClicked)!=0 and len(self.srcClicked)==0 :
            sqlQuery = self.sqlStreamIDSingle.format("DST", '"%s"' % '","'.join(self.dstClicked))
        else:
            sqlQuery = self.sqlStreamIDBetween.format('"%s"' % '","'.join(self.srcClicked) ,
                                                    '"%s"' % '","'.join(self.dstClicked) )
        sqlResult = self.cursor.execute(sqlQuery).fetchall()
        self.streamTableID = [str(i[0]) for i in sqlResult]
        sqlQuery = self.sqlStreamBetween.format('"%s"' % '","'.join(self.streamTableID))
        sqlResult = self.cursor.execute(sqlQuery).fetchall()
        tableModel = MyTableModel(self, sqlResult, self.streamTableHeader)
        self.streamTable.setModel(tableModel)

    def streamClicked(self, qModelIndex):
        rowNum = qModelIndex.row()
        sqlQuery = self.sqlStreamInfo.format(self.streamTableID[rowNum])
        sqlResult = self.rawcursor.execute(sqlQuery).fetchone()
        if(sqlResult['SRCDATA'] is None):
            srcDetailTable = QTableView()
            srcHeaders = []
            for col in sqlResult.keys():
                if col.startswith('SRCHEADER') and sqlResult[col] is not None:
                    singleHeader = self.cursor.execute(self.sqlHTTPHeader.format("SRC",col[9:])).fetchone()[0]
                    srcHeaders.append([singleHeader, sqlResult[col]])
            srcHeaders.append(['Data',sqlResult['SRCBODY']])
            srcTableModel = MyTableModel(self, srcHeaders, self.headerTableHeader)
            srcDetailTable.setModel(srcTableModel)
        else:
            srcDetailTable = QPlainTextEdit()
            srcDetailTable.setLineWrapMode(QPlainTextEdit.NoWrap)
            srcDetailTable.setReadOnly(True)
            srcDetailTable.insertPlainText(hexdump.hexdump(sqlResult['SRCDATA'],result='return'))
        if(sqlResult['DSTDATA'] is None):
            dstDetailTable = QTableView()
            dstHeaders = []
            for col in sqlResult.keys():
                if col.startswith('DSTHEADER') and sqlResult[col] is not None:
                    singleHeader = self.cursor.execute(self.sqlHTTPHeader.format("DST",col[9:])).fetchone()[0]
                    dstHeaders.append([singleHeader, sqlResult[col]])
            dstHeaders.append(['Data',sqlResult['DSTBODY']])
            dstTableModel = MyTableModel(self, dstHeaders, self.headerTableHeader)
            dstDetailTable.setModel(dstTableModel)
        else:
            dstDetailTable = QPlainTextEdit()
            dstDetailTable.setLineWrapMode(QPlainTextEdit.NoWrap)
            dstDetailTable.setReadOnly(True)
            dstDetailTable.insertPlainText(hexdump.hexdump(sqlResult['DSTDATA'],result='return'))
        if(self.streamHeaders.count() == 0):
            self.streamHeaders.addWidget(srcDetailTable)
            self.streamHeaders.addWidget(dstDetailTable)
        else:
            self.streamHeaders.addWidget(srcDetailTable)
            self.streamHeaders.addWidget(dstDetailTable)
            self.streamHeaders.itemAt(0).widget().setParent(None)
            self.streamHeaders.itemAt(0).widget().setParent(None)

    def srcHostRightClicked(self, point):
        self.srcHostListMenu = QMenu()
        menuItem = self.srcHostListMenu.addAction("Delete")
        self.connect(menuItem, SIGNAL("triggered()"), self.srcHostItemClicked) 
        self.srcHostListMenu.move(QCursor.pos())
        self.srcHostListMenu.show()

    def dstHostRightClicked(self, point):
        self.dstHostListMenu = QMenu()
        menuItem = self.dstHostListMenu.addAction("Delete")
        self.connect(menuItem, SIGNAL("triggered()"), self.dstHostItemClicked) 
        self.dstHostListMenu.move(QCursor.pos())
        self.dstHostListMenu.show()

    def srcHostItemClicked(self):
        toDeleteItem = self.srcHostModel.item(self.srcHostList.currentIndex().row())
        toDeleteIP = toDeleteItem.text()
        if toDeleteItem.checkState() == Qt.Checked:
            self.srcClicked.pop(self.srcClicked.index(toDeleteIP))
        sqlQuery = self.sqlGetNumByIP.format("SRC")
        num = self.cursor.execute(sqlQuery, [str(toDeleteIP)]).fetchone()[0]
        sqlQuery = self.sqlDeleteIP.format("SRC")
        self.cursor.execute(sqlQuery, [num])
        sqlQuery = self.sqlDeleteStreamByIP.format("SRC")
        self.cursor.execute(sqlQuery, [num])
        sqlQuery = self.sqlDeleteHost.format("DST")
        self.cursor.execute(sqlQuery)
        self.updateHosts()

    def dstHostItemClicked(self):
        toDeleteItem = self.dstHostModel.item(self.dstHostList.currentIndex().row())
        toDeleteIP = toDeleteItem.text()
        if toDeleteItem.checkState() == Qt.Checked:
            self.dstClicked.pop(self.dstClicked.index(toDeleteIP))
        sqlQuery = self.sqlGetNumByIP.format("DST")
        num = self.cursor.execute(sqlQuery, [str(toDeleteIP)]).fetchone()[0]
        sqlQuery = self.sqlDeleteIP.format("DST")
        self.cursor.execute(sqlQuery, [num])
        sqlQuery = self.sqlDeleteStreamByIP.format("DST")
        self.cursor.execute(sqlQuery, [num])
        sqlQuery = self.sqlDeleteHost.format("SRC")
        self.cursor.execute(sqlQuery)
        self.updateHosts()

    def updateHosts(self):
        self.initSrcHost()
        self.initDstHost()
        toClickedList = self.srcClicked
        self.srcClicked = []
        for i in toClickedList:
            toClickedItem = self.srcHostList.model().findItems(i)[0]
            toClickedItem.setCheckState(Qt.Checked)
            self.srcHostClicked(toClickedItem)
        toClickedList = self.dstClicked
        self.dstClicked = []
        for i in toClickedList:
            toClickedItem = self.dstHostList.model().findItems(i)[0]
            toClickedItem.setCheckState(Qt.Checked)
            self.dstHostClicked(toClickedItem)

    def fileSave(self):
        self.conn.commit()

    def fileSaveAs(self):
        self.conn.commit()
        dbPathNew = QFileDialog.getSaveFileName(self,
                "Save As",".",
                "Sqlite Database (*.db)");
        shutil.copy2(self.dbPath,dbPathNew)

    def itemPreview(self):
        currentID = self.streamTableID[self.streamTable.currentIndex().row()]
        sqlResult = self.cursor.execute(self.sqlGetItemData,[currentID]).fetchone()[0]
        tmp = tempfile.mktemp()
        f = open(tmp,"w")
        f.write(sqlResult)
        f.close()
        subprocess.call(["xdg-open", tmp])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
