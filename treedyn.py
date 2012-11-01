from PyQt4 import QtCore
from tree import TreeModel as PureTree

__all__ = ['TreeModel']

class TreeModel(PureTree, QtCore.QObject):
    def __init__(self, label=''):
        PureTree.__init__(self, label)
        QtCore.QObject.__init__(self)

    def setData(self, field, value):
        PureTree.setData(self, field, value)
        self.emit(QtCore.SIGNAL("setData"), self, field, value)
    
    def removeData(self, field):
        if PureTree.removeData(self, field):
            self.emit(QtCore.SIGNAL("removeData"), self, field)
            return True
        else:
            return False
        
    def attach(self,node):
        if PureTree.attach(self,node):
            self.emit(QtCore.SIGNAL("attach"), self, node)
            return True
        else:
            return False
        
    def insertLeft(self,node):
        if PureTree.insertLeft(self,node):
            self.emit(QtCore.SIGNAL("insertLeft"), self, node)
            return True
        else:
            return False
       
    def insertRight(self,node):
        if PureTree.insertRight(self,node):
            self.emit(QtCore.SIGNAL("insertRight"), self, node)
            return True
        else:
            return False
        
    def prune(self):
        if PureTree.prune(self):
            self.emit(QtCore.SIGNAL("prune"), self)
            return True
        else:
            return False
        
    def splice(self):
        if PureTree.splice(self):
            self.emit(QtCore.SIGNAL("splice"), self)
            return True
        else:
            return False
