import at4
from PyQt4 import QtGui
from PyQt4 import QtCore

class MyApp(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QGridLayout(self)
        self.button1 = QtGui.QPushButton("Update table from tree")
        self.button2 = QtGui.QPushButton("Update tree from table")
        self.gTable = at4.TableEdit(self)
        self.gTree = at4.TreeEdit(self)
        layout.addWidget(self.button1,0,0)
        layout.addWidget(self.button2,0,1)
        layout.addWidget(self.gTable,1,0)
        layout.addWidget(self.gTree,1,1)

        s = "(S (NP (N I)) (VP (VP (V saw) " \
            "(NP (DT the) (N man))) (PP (P with) " \
            "(NP (DT a) (N telescope)))))"

        self.tree = at4.TreeModel.importTreebank([s]).next()
        self.table = self.tree.exportLPathTable(at4.TableModel)

        self.gTree.setData(self.tree,[('label','Tree')])
        self.gTree.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.gTable.setData(self.table)

        self.connect(self.button1,QtCore.SIGNAL("clicked()"),self.updateTable)
        self.connect(self.button2,QtCore.SIGNAL("clicked()"),self.updateTree)

    def updateTable(self):
        self.table = self.tree.exportLPathTable(at4.TableModel)
        self.gTable.setData(self.table)
        
    def updateTree(self):
        self.tree = at4.TreeModel.importLPathTable(self.table)
        self.gTree.setData(self.tree,[('label','Tree')])
        self.gTree.expandAll()

if __name__ == "__main__":
    app = QtGui.QApplication([])
    w = MyApp()
    w.show()
    app.exec_()
