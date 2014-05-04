from PyQt4 import QtCore
import treedyn

__all__ = ["TreeQtModel"]

class TreeQtModel(QtCore.QAbstractItemModel):
    def __init__(self, treemodel, parent=None):
        """
        @param treemodel: Dynamic tree model.
        """
        QtCore.QAbstractItemModel.__init__(self, parent)
        self.root = treemodel
        self.fields = ['label']
        self.headers = ['label']
        self.root.dfs(self.updateFieldsWithNode)
        self.root.dfs(self.connectNodeSignals)
            
    def _reset(self, *args):
        self.reset()
    
    def updateFieldsWithNode(self, node):
        for k in node.getFields():
            if k not in self.fields:
                self.fields.append(k)
                self.headers.append(k)
    
    def connectNodeSignals(self, node):
        for sig in ("attach","insertLeft","insertRight","prune","splice"):
            self.connect(node, QtCore.SIGNAL(sig), self._reset)
    
    def disconnectNodeSignals(self, node):
        for sig in ("attach","insertLeft","insertRight","prune","splice"):
            self.disconnect(node, QtCore.SIGNAL(sig), self._reset)
            
    def getHeaderIndex(self, field):
        try:
            return self.fields.index(field)
        except ValueError:
            return 0
    
    def getTreeModel(self):
        return self.root
    
    def index(self, row, column, parent=None):
        if self.root.root != self.root:
            return QtCore.QModelIndex()
        if parent is None or not parent.isValid():
            return self.createIndex(0, column, self.root)
        else:
            parent_node = parent.internalPointer()
            try:
                node = parent_node.children[row]
                return self.createIndex(row, column, node)
            except IndexError:
                return QtCore.QModelIndex()
    
    def parent(self, index):
        if self.root.root != self.root:
            return QtCore.QModelIndex()
        if not index.isValid():
            return QtCore.QModelIndex()
        node = index.internalPointer()
        parent_node = node.parent
        if parent_node is None or parent_node == node:
            return QtCore.QModelIndex()
        row = 0
        ls = parent_node.leftSibling
        while ls:
            row += 1
            ls = ls.leftSibling
        return self.createIndex(row, 0, parent_node)
    
    def rowCount(self, parentIndex=None):
        if self.root.root != self.root:
            return 0
        if parentIndex is None or not parentIndex.isValid():
            return 1
        else:
            parent_node = parentIndex.internalPointer()
            return len(parent_node.children) 
    
    def columnCount(self, parentIndex=None):
        if self.root.root != self.root:
            return 0
        return len(self.fields)
    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if self.root.root != self.root:
            return QtCore.QVariant()
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        node = index.internalPointer()
        try:
            field = self.fields[index.column()]
        except IndexError:
            field = self.fields[0]
        return QtCore.QVariant(unicode(node.getData(field)))
    
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if self.root.root != self.root:
            return False
        if index.isValid() or role != QtCore.Qt.EditRole:
            v = unicode(value.toString())
            node = index.internalPointer()
            try:
                field = self.fields[index.column()]
            except IndexError:
                field = self.fields[0]
            node.setData(field, v)
            self.emit(QtCore.SIGNAL("dataChanged"),index,index)
            return True
        else:
            return False
    
    def flags(self, index):
        return QtCore.QAbstractItemModel.flags(self,index) | QtCore.Qt.ItemIsEditable
    
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if self.root.root != self.root:
            return QtCore.QVariant()
        if orientation != QtCore.Qt.Horizontal or role!=QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        elif section >= 0 and section < len(self.headers):
            return QtCore.QVariant(self.headers[section])
        else:
            return QtCore.QVariant()
    
    def setHeaderData(self, section, orientation, value, role=QtCore.Qt.EditRole):
        if self.root.root != self.root:
            return False
        if orientation != QtCore.Qt.Horizontal or role!=QtCore.Qt.EditRole:
            return False
        elif section >= 0 and section < len(self.fields):
            self.headers[section] = unicode(value.toString())
            self.emit(QtCore.SIGNAL("headerDataChanged"),
                      orientation, section, section)
            return True
        else:
            return False
        
    def insertRows(self, row, count, parent=None):
        if self.root.root != self.root:
            return False
        if parent is None or not parent.isValid() or count <= 0:
            return False
        parent_node = parent.internalPointer()
        if len(parent_node.children) >= row:
            idx = len(parent_node.children) 
            method = parent_node.attach
        else:
            idx = max(row, 0)
            method = parent_node.children[idx].insertLeft
        self.beginInsertRows(parent, idx, idx+count-1)
        for i in range(count):
            method(treedyn.TreeModel())
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=None):
        if self.root.root != self.root:
            return False
        if parent is None or not parent.isValid() or row+count < 0:
            return False
        parent_node = parent.internalPointer()
        if row >= len(parent_node.children):
            return False
        first = max(0, row)
        last = min(len(parent_node.children), row+count) - 1 
        self.beginRemoveRows(parent, first, last)
        for i in range(last-first+1):
            parent_node.children[first].prune()
        self.endRemoveRows()
            
    def getNode(self, index):
        if index.isValid():
            return index.internalPointer()
                
if __name__ == "__main__":
    from PyQt4 import QtGui
    from nltk import tree

    class MyWidget(QtGui.QWidget):
        def __init__(self):
            QtGui.QWidget.__init__(self)
            self.treeview = QtGui.QTreeView(self)
            self.treemodel = self.buildModel(self.treeview)
            self.treeview.setModel(self.treemodel) 
            self.treeview.expandAll()
            self.treeview.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
            self.button = QtGui.QPushButton("dump", self)
            layout = QtGui.QVBoxLayout(self)
            layout.addWidget(self.treeview)
            layout.addWidget(self.button)
            self.connect(self.button,QtCore.SIGNAL("clicked()"),self.dump)
            
        def buildModel(self, view):
            s = "(S (NP (N I)) (VP (VP (V saw) (NP (DT the) (N man))) (PP (P with) (NP (DT a) (N telescope)))))"
            t = tree.Tree(s)
            treemodel = treedyn.TreeModel.importNltkLiteTree(t)
            return TreeQtModel(treemodel, view)
     
        def dump(self):
            print self.treemodel.root.treebankString('label')
            
    app = QtGui.QApplication([])
    w = MyWidget()
    w.show()
    app.exec_()
     