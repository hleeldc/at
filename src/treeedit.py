from PyQt4 import QtGui
from PyQt4 import QtCore
from myaccel import AccelKeyHandler
from treeqt import TreeQtModel

__all__ = ['TreeEdit']
           
class TreeEditItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent, labels, treenode):
        QtGui.QTreeWidgetItem.__init__(self, parent, labels)
        self.setExpanded(True)
        self.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable)
        self.treenode = treenode
            
    def attach(self, node):
        return self.treenode.attach(node.treenode)
    def insertLeft(self, node):
        return self.treenode.insertLeft(node.treenode)
    def insertRight(self, node):
        return self.treenode.insertRight(node.treenode)
    def prune(self):
        return self.treenode.prune()
    def splice(self):
        return self.treenode.splice()

    # model -> gui
    def _attach(self,dst,src):
        p = src.gui.parent()
        if p:
            i = p.indexOfChild(src.gui)
            p.takeChild(i)
        else:
            p = src.gui.treeWidget()
            i = p.indexOfTopLevelItem(src.gui)
            p.takeTopLevelItem(i)
        dst.gui.addChild(src.gui)
        
    def _insertLeft(self,dst,src):
        p = dst.gui.parent()
        c = p.firstChild()
        p.insertItem(src.gui)
        if c != dst.gui:
            src.gui.moveItem(dst.gui)
            dst.gui.moveItem(src.gui)
        
    def _insertRight(self,dst,src):
        dst.gui.parent().insertItem(src.gui)
        src.gui.moveItem(dst.gui)
    
    def _prune(self,n):
        i = self.parent().indexOfChild(self)
        self.parent().takeChild(i)
        
    def _splice(self,n):
        p = self.parent()
        j = p.indexOfChild(self)
        for i in range(p.childCount()):
            c = self.takeChild(0)
            p.insertChild(i+j+1,c)
        p.takeChild(p.indexOfChild(self))

    def okRename(self, col):
        QListViewItem.okRename(self,col)
        f = self.listView().col2str[col]
        self.treenode.data[f] = self.text(col).ascii()
    
    def emitDataChanged(self):
        print "xxx"
        

class TreeEdit(QtGui.QTreeView,AccelKeyHandler):
    def __init__(self,parent=None):
        QtGui.QTreeView.__init__(self,parent)
        self.data = None
        self.col2str = None
        self.setRootIsDecorated(True)
        self.setSortingEnabled(False)
        self.clipBoard = None
        self.accelFilter = None
        self.keyBindingDescriptor = {
            "Ctrl+N":"new",
            "Ctrl+A":"attach",
            "Ctrl+I,Ctrl+L":"insertLeft",
            "Ctrl+I,Ctrl+R":"insertRight",
            "Ctrl+P":"prune",
            "Ctrl+S":"splice"
            }
        self.setKeyBindings(self.keyBindingDescriptor)
    
    def accel_new(self):
        if self.data is None: return
        self.clipBoard = self.data.__class__()

    def accel_attach(self):
        idx = self.currentIndex()
        node = self.model().getNode(idx)
        if node and self.clipBoard is not None and \
            node.attach(self.clipBoard):
            self.clipBoard.dfs(self.model().connectNodeSignals)
            self.clipBoard = None

    def accel_insertLeft(self):
        idx = self.currentIndex()
        node = self.model().getNode(idx)
        if node and self.clipBoard is not None and \
            node.insertLeft(self.clipBoard):
            self.clipboard.dfs(self.model().connectNodeSignals)
            self.clipBoard = None

    def accel_insertRight(self):
        idx = self.currentIndex()
        node = self.model().getNode(idx)
        if node and self.clipBoard is not None and \
            node.insertRight(self.clipBoard):
            self.clipBoard.dfs(self.model().connectNodeSignals)
            self.clipBoard = None

    def accel_prune(self):
        idx = self.currentIndex()
        node = self.model().getNode(idx)
        if node and node.prune():
            node.dfs(self.model().disconnectNodeSignals)
            self.clipBoard = node

    def accel_splice(self):
        idx = self.currentIndex()
        node = self.model().getNode(idx)
        if node and node.splice():
            self.model().disconnectNodeSignals(node)
            self.clipBoard = node
    
    def reset(self):
        QtGui.QTreeView.reset(self)
        self.expandAll()
        
    def setData(self, model, fields=[]):
        """
        @param model: An instance of TreeModel.
        """
        if model != model.root: return
        self.data = model
        qtmodel = TreeQtModel(model, self)
        self.col2str = {}
        for f,v in fields:
            i = qtmodel.getHeaderIndex(f)
            qtmodel.setHeaderData(i, QtCore.Qt.Horizontal, QtCore.QVariant(v))
            self.col2str[i] = f
        self.setModel(qtmodel)
        self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.expandAll()

    
if __name__ == "__main__":
    from PyQt4 import QtGui
    from PyQt4 import QtCore
    from treedyn import TreeModel

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
            hbox = QtGui.QGridLayout()
            lbl1 = QtGui.QLabel("Edit Panel",self)
            lbl2 = QtGui.QLabel("Clipboard",self)
            lbl1.setMargin(2)
            lbl1.setAlignment(QtCore.Qt.AlignCenter)
            lbl2.setAlignment(QtCore.Qt.AlignCenter)
            self.treeview = TreeEdit(self)
            self.clipboard = TreeEdit(self)
            hbox.addWidget(lbl1, 0,0)
            hbox.addWidget(lbl2, 0,1)
            hbox.addWidget(self.treeview, 1,0)
            hbox.addWidget(self.clipboard, 1,1)
            layout.addLayout(hbox)
            self.load()
            self.resize(400,450)

        def load(self):
            from nltk import tree
            s = "(S (NP (N I)) (VP1 (VP2 (V saw) (NP (ART the) (N man))) (PP (P with) (NP (ART a) (N telescope)))))"
            #s = "(S T)"
            t = tree.Tree(s)
            root = TreeModel.importNltkLiteTree(t)
            self.treeview.setData(root, [('label','Tree')])
            #self.treeview.setModel(TreeQtModel(root,self.treeview))
            #self.treeview.expandAll()
            #self.clipboard.setData(root, [('label','Tree')])
            #self.clipboard.expandAll()
            self.vp1 = root.children[1]
            self.pp = self.vp1.children[1]
            self.vp2 = self.vp1.children[0]
            self.stage = 0
            self.button2.setText('splice VP1')

        def change(self):
            if self.stage == 0:
                self.vp1.splice()
                self.clipboard.setData(self.vp1, [('label','Tree')])
                self.button2.setText('prune PP')
                self.stage = 1
            elif self.stage == 1:
                self.pp.prune()
                self.clipboard.setData(self.pp,[('label','Tree')])
                self.button2.setText('attach PP to VP2')
                self.stage = 2
            elif self.stage == 2:
                self.vp2.attach(self.pp)
                self.clipboard.reset()
                self.button2.setText('')
                self.stage = 3

    app = QtGui.QApplication([])
    w = Demo()
    w.show()
    app.exec_()
    
