from PyQt4 import QtCore
from PyQt4 import QtGui
from at4 import TableModel, TableEdit

class Demo(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QVBoxLayout(self)
        self.b1 = QtGui.QPushButton('reset / load table',self)
        self.connect(self.b1,QtCore.SIGNAL("clicked()"),self.action)
        self.tab = TableEdit(self)
        self.stage = 0
        self.b2 = QtGui.QPushButton('print table on console',self)
        self.connect(self.b2,QtCore.SIGNAL("clicked()"),self.printTable)
        layout.addWidget(self.b1)
        layout.addWidget(self.tab)
        layout.addWidget(self.b2)

    def printTable(self):
        self.data.printTable()

    def action(self):
        if self.stage == 0:
            t = [[('start',float),('end',float),('ch',str),('transcript',str)],
                 [1.23,2.34,'A','hello'],
                 [2.45,2.67,'B','hi'],
                 [2.88,3.09,'A','how are you']]
            self.data = TableModel.importList(t)
            self.tab.setData(self.data)
            self.stage = 1
            self.b1.setText('add row')
        elif self.stage == 1:
            self.data.insertRow(len(self.data))
            self.stage = 2
            self.b1.setText('take row 4')
        elif self.stage == 2:
            self.tmprow = self.data.takeRow(3)
            self.stage = 3
            self.b1.setText('insert row at the top')
        elif self.stage == 3:
            self.data.insertRow(0,self.tmprow)
            self.stage = 4
            self.b1.setText('sort by start')
        elif self.stage == 4:
            self.data.sort()
            self.stage = 5
            self.b1.setText('add column at the begining')
        elif self.stage == 5:
            self.data.insertColumn(0)
            self.data.setHeader(0,('review',str))
            self.stage = 6
            self.b1.setText('take review column')
        elif self.stage == 6:
            self.tmpcol = self.data.takeColumn(0)
            self.stage = 7
            self.b1.setText('insert the column before ch column')
        elif self.stage == 7:
            self.data.insertColumn(2,self.tmpcol)
            self.stage = 8
            self.b1.setText('change start time of row 1 to 9.99')
        elif self.stage == 8:
            self.data[0][0] = 9.99
            self.stage = 0
            self.b1.setText('reset / load table')


app = QtGui.QApplication([])
w = Demo()
w.show()
app.exec_()
