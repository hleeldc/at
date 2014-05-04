from PyQt4 import QtCore
from PyQt4 import QtGui
import speakercode

__all__ = ["TranscriptEditSideBarCanvas","TranscriptEditSideBarBox"]

class TranscriptEditSideBarBox(QtGui.QGraphicsRectItem):
    def __init__(self,seg,field,format,x,y,w,h,canvas):
        """
        @param seg: Segment (a row of the transcript model)
        @param field: The field to be displayed
        @param format: Display format, e.g. "%s"
        @param x: X-coordinate
        @param y: Y-coordinate
        @param w: Width
        @param h: Height
        @param canvas: The canvas on with this box will be drawn.
        """
        QtGui.QGraphicsRectItem.__init__(self, x, y, w, h)
        canvas.addItem(self)
        self.seg = seg  # a row of the table model
        self.field = field
        self.format = format

    def paint(self, p, option=None, widget=None):
        """
        Called by Qt when this box is drawn.
        
        @param p: An instance of QPainter
        """
        QtGui.QGraphicsRectItem.paint(self, p, option, widget)
        label = self.format % self.seg[self.field]
        if label is not None:
            p.font().setPixelSize(8)
            p.drawText(self.rect().adjusted(2,0,-2,0),
                       QtCore.Qt.TextSingleLine,
                       label)

class TranscriptEditSideBarCanvas(QtGui.QGraphicsView):
    def __init__(self, te, field, format,
                 colorMap=lambda x:Qt.white, parent=None):
        """
        @param te: TranscriptEdit
        @param field: Field to be displayed
        @param format: Field display format
        @param colorMap: speaker color map
        """
        QtGui.QGraphicsView.__init__(self, parent)
        self._canvas = QtGui.QGraphicsScene()
        self._te = te
        self._boxes = {}
        self._colorMap = colorMap
        self._field = field
        self._format = format
        self._data = None
        
        self.setScene(self._canvas)
        self.setFrameShape(QtGui.QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._canvas.setBackgroundBrush(QtCore.Qt.lightGray)

        self._te.sideBarLayoutChanged.connect(self.repaint)

    def resizeEvent(self, e):
        s0 = e.oldSize()
        s1 = e.size()
        self._canvas.setSceneRect(0, 0, s1.width(), s1.height())

    def setData(self, data):
        self._data = data
        self.repaint(self._te.getSideBarLayout())
        self.connect(data.emitter,QtCore.SIGNAL("cellChanged"),self._cellChanged)
            
    def repaint(self, layout):
        self._boxes = {}
        for item in self._canvas.items():
            self._canvas.removeItem(item)
            del item

        w = self.width()
        for para,seg,y,h in layout:
            item = TranscriptEditSideBarBox(
                seg, self._field, self._format, 0, y, w, h, self._canvas)
            self._boxes[para] = item
            color = QtGui.QColor(self._colorMap(seg[self._field]))
            item.setBrush(QtGui.QBrush(color))
            item.show()
        self._canvas.update()

    # model-to-self
    def _cellChanged(self, i, c, v, w):
        """
        @param i: row index
        @param c: column index
        @param v: cell value
        @param w: old value
        """
        h = self._data.getColumnName(c)
        if h == self._field:
            p = self._te.getParagraphIndex(i)
            if p is not None and p in self._boxes:
                item = self._boxes[p]
                seg = self._data[i]
                color = QtGui.QColor(self._colorMap(v))
                item.setBrush(QtGui.QBrush(color))
                item.update()
                self._canvas.update()
                
