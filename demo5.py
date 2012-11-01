""" Test TransBox class
"""

from qt import *
from at import *

from transbox import *

class Demo5(QVBox):
    def __init__(self):
        QVBox.__init__(self)
        b = QPushButton("click me", self)
        b2 = QPushButton("set audio", self)
        b3 = QPushButton("change height", self)
        b.connect(b, SIGNAL("clicked()"), self._setdata)
        b2.connect(b2, SIGNAL("clicked()"), self._setaudio)
        b3.connect(b3, SIGNAL("clicked()"), self._changeheight)
        self.wave = Waveform(self)
        self.trans = TransBox(self.wave, self)


    def _setaudio(self):
        self.wave.addSndFile("long.sph")
        self.wave.placeWaveform("long.sph", 0, 0)

    def _setdata(self):
        data = Transcript.importTrs("x.trs")
        self.trans.setData(data)

    def _changeheight(self):
        self.trans.setHeight(40)
        
app = QApplication([])
w = Demo5()
app.setMainWidget(w)
w.show()
app.exec_loop()
