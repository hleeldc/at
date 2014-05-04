from PyQt4 import QtGui
from PyQt4 import QtCore

class TableEdit(QtGui.QTableWidget):
    def __init__(self, parent=None):
        QtGui.QTableWidget.__init__(self, parent)
        self.data = None

    def setData(self, data):
        self.clear()
        self.setColumnCount(len(data.header))
        self.setHorizontalHeaderLabels([h for h,t in data.header])
        self.setRowCount(len(data))
        for i,row in enumerate(data):
            for j,v in enumerate(row):
                if v is not None:
                    if type(v)==str or type(v)==unicode:
                        self.setItem(i,j,QtGui.QTableWidgetItem(v))
                    else:
                        self.setItem(i,j,QtGui.QTableWidgetItem(str(v)))
        resizemode = QtGui.QHeaderView.ResizeToContents
        self.horizontalHeader().setResizeMode(resizemode)
        if data != self.data:
            for sig in ('setHeader',
                        'cellChanged',
                        'insertRow',
                        'insertColumn',
                        'takeRow',
                        'takeColumn',
                        'sort'):
                self.connect(data.emitter,QtCore.SIGNAL(sig),eval("self._%s"%sig))
            self.connect(self,
                         QtCore.SIGNAL("cellChanged(int,int)"),
                         self.__cellChanged)
            self.data = data
            
    # incoming; model-to-gui
    def _setHeader(self, col, header):
        self.setHorizontalHeaderItem(col, QtGui.QTableWidgetItem(header[0]))
        #self.horizontalHeaderItem(col).setText(header[0])
        
    def _cellChanged(self, i, j, val):
        if val is None:
            val = ''
        self.disconnect(self,QtCore.SIGNAL("valueChanged(int,int)"),self.__cellChanged)
        self.setItem(i,j,QtGui.QTableWidgetItem(unicode(val)))
        self.connect(self,QtCore.SIGNAL("valueChanged(int,int)"),self.__cellChanged)

    def _insertRow(self, i, row):
        self.insertRow(i)
        if row is not None:
            for j,c in enumerate(row):
                if c is not None:
                    self.setItem(i,j,QtGui.QTableWidgetItem(c))
                    
    def _insertColumn(self, j, col):
        self.insertColumn(j)
        if col is not None:
            self.setHorizontalHeaderItem(j, QtGui.QTableWidgetItem(col[0][0]))
            for i,c in enumerate(col[1:]):
                if c is not None:
                    self.setItem(i,j,QtGui.QTableWidgetItem(c))
                    
    def _takeRow(self, i, r):
        self.removeRow(i)
    def _takeColumn(self, j):
        self.removeColumn(j)
    def _sort(self):
        self.setData(self.data)

    # outgoing; gui-to-model
    def __cellChanged(self, row, col):
        self.disconnect(self,QtCore.SIGNAL("cellChanged(int,int)"),self.__cellChanged)
        self.disconnect(self.data.emitter,QtCore.SIGNAL("cellChanged"),self._cellChanged)
        self.data[row][col] = self.item(row,col).text()
        self.connect(self,QtCore.SIGNAL("cellChanged(int,int)"),self.__cellChanged)
        self.connect(self.data.emitter,QtCore.SIGNAL("cellChanged"),self._cellChanged)
        
if __name__ == '__main__':
    from PyQt4 import QtGui, QtCore
    from table_qt import TableModel

    class Demo(QtGui.QWidget):
        def __init__(self):
            QtGui.QWidget.__init__(self)
            self.b1 = QtGui.QPushButton('reset / load table',self)
            self.connect(self.b1,QtCore.SIGNAL("clicked()"),self.action)
            self.tab = TableEdit(self)
            self.stage = 0
            self.b2 = QtGui.QPushButton('print table on console',self)
            layout = QtGui.QVBoxLayout(self)
            layout.addWidget(self.b1)
            layout.addWidget(self.tab)
            layout.addWidget(self.b2)
            self.connect(self.b2,QtCore.SIGNAL("clicked()"),self.printTable)

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
