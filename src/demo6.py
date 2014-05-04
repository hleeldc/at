from at4 import TreeEdit, TreeModel
from PyQt4 import QtGui
import sys

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    s = "(S (NP (N I)) (VP1 (VP2 (V saw) (NP (ART the) (N man))) " \
        "(PP (P with) (NP (ART a) (N telescope)))))"
    root = TreeModel.importTreebank([s]).next()
    w = TreeEdit()
    w.setData(root)
    w.show()
    app.exec_()
