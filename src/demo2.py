from PyQt4 import QtCore, QtGui
from at4 import TreeModel, TreeEdit

class Demo(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QVBoxLayout(self)
        
        self.button = QtGui.QPushButton('Reset',self)
        self.connect(self.button,QtCore.SIGNAL("clicked()"),self.load)
        self.button2 = QtGui.QPushButton(self)
        self.connect(self.button2,QtCore.SIGNAL("clicked()"),self.change)
        layout.addWidget(self.button)
        layout.addWidget(self.button2)
        
        grid = QtGui.QGridLayout()
        lbl1 = QtGui.QLabel("Edit Panel")
        lbl2 = QtGui.QLabel("Clipboard")
        lbl1.setMargin(2)
        lbl1.setAlignment(QtCore.Qt.AlignHCenter)
        lbl2.setAlignment(QtCore.Qt.AlignHCenter)
        self.treeview = TreeEdit()
        self.clipboard = TreeEdit()
        grid.addWidget(lbl1, 0, 0)
        grid.addWidget(lbl2, 0, 1)
        grid.addWidget(self.treeview, 1, 0)
        grid.addWidget(self.clipboard, 1, 1)
        
        layout.addLayout(grid)
        
        self.root = None
        self.load()
        self.resize(400,450)

    def load(self):
        s = "(S (NP (N I)) (VP1 (VP2 (V saw) " \
            "(NP (ART the) (N man))) (PP (P with) " \
            "(NP (ART a) (N telescope)))))"
        self.root = TreeModel.importTreebank([s]).next()
        self.treeview.setData(self.root,[('label','Tree')])
        self.vp1 = self.root.children[1]
        self.pp = self.vp1.children[1]
        self.vp2 = self.vp1.children[0]
        self.stage = 0
        self.button2.setText('splice VP1')

    def change(self):
        if self.stage == 0:
            self.vp1.splice()
            self.clipboard.setData(self.vp1,[('label','Tree')])
            self.button2.setText('prune PP')
            self.stage = 1
        elif self.stage == 1:
            self.pp.prune()
            self.clipboard.setData(self.pp,[('label','Tree')])
            self.button2.setText('attach PP to VP2')
            self.stage = 2
        elif self.stage == 2:
            self.vp2.attach(self.pp)
            self.clipboard.setData(self.vp2,[('label','Tree')])
            self.button2.setText('')
            self.stage = 3

app = QtGui.QApplication([])
w = Demo()
w.show()
app.exec_()

