from PyQt4 import QtCore
from PyQt4 import QtGui
from myaccel import AccelKeyHandler
import speakercode
import bisect
import time

__all__ = ["TranscriptEdit"]

class TranscriptEdit(QtGui.QTextEdit):

    sideBarLayoutChanged = QtCore.pyqtSignal(list)
    
    def __init__(self, parent=None):
        QtGui.QTextEdit.__init__(self, parent)
        #self.setTextFormat(Qt.PlainText)
        self.clipboard = QtGui.QApplication.clipboard()
        self.currentParagraph = None
        self.currentParagraphHeight = None
        #self.defaultKeyBindings = {
        #    "Ctrl+V":"paste"
        #    }
        #self.setKeyBindings(self.defaultKeyBindings)
        #act = QtGui.QAction(self)
        #act.setShortcut(QtGui.QKeySequence.fromString('Ctrl+v'))
        #act.triggered.connect(self.accel_paste)
        #self.addAction(act)
        
        # disable some of the default shortcuts including Ctrl+Insert
        class IgnoreDefaultShortcuts(QtCore.QObject):
            def eventFilter(self, watched, event):
                return event.type() == QtCore.QEvent.ShortcutOverride
        self.eventFilter1 = IgnoreDefaultShortcuts()
        self.installEventFilter(self.eventFilter1)
        
        self.data = None
        self.rownums = []
        self.sideBarLayout = []
        self.sb = self.verticalScrollBar()
        self.sb2 = None # another vertical scroll bar

        self.brushNormal = QtCore.Qt.white
        self.brushSelected = QtCore.Qt.green
        
        # There is a call circle:
        #   data.select -> _select -> (cursor position is changed)
        #     -> _cursorPositionChanged -> data.select
        # To cut the circle, _cursorPositionChanged sets
        # cursorPosAlreadySet to True.  Then, _select doesn't change the
        # cursor position and sets cursorPosAlreadySet to False if
        # it is True.
        self.cursorPosAlreadySet = False

        # to avoid errors that occur in _display
        # (_display tries to disconnect these signals at the beginning)
        self.connect(self, QtCore.SIGNAL("textChanged()"),self._textChanged)
        self.connect(self, QtCore.SIGNAL("cursorPositionChanged()"),self._cursorPositionChanged)
        self.connect(self.sb, QtCore.SIGNAL("valueChanged(int)"), self._generateSideBarLayout)

    def _display(self, data):
        # these signals have to be disconnected to avoid any side effects
        # caused when changing the text
        self.disconnect(self, QtCore.SIGNAL("textChanged()"),self._textChanged)
        self.disconnect(self, QtCore.SIGNAL("cursorPositionChanged()"),self._cursorPositionChanged)
        self.clear()
        self.rownums = []
##         i = 0
##         for row in data:
##             if self.displayFilter(row):
##                 self.rownums.append(row.num)
##                 self.insertParagraph(row['transcript'],i)
##                 i += 1
        txt = ""
        for row in data:
            if self.displayFilter(row):
                self.rownums.append(row.num)
                txt += row['transcript'] + "\n"
        if txt:
            self.setText(txt[:-1])
        #for i in range(len(self.rownums),self.document().blockCount()):
        #    self.removeParagraph(i)
        if self.rownums:
            data.select(self.rownums[0])
            if self.styler:
                for p,r in enumerate(self.rownums):
                    self.setSelection(p,0,p,self.paragraphLength(p))
                    L = self.styler(data[r])
                    if L:
                        for f,args in L:
                            apply(f,args)
                self.removeSelection()
        self.moveCursor(QtGui.QTextCursor.Start)
        self.currentParagraph = 0
        self.connect(self,QtCore.SIGNAL("textChanged()"),self._textChanged)
        self.connect(self,QtCore.SIGNAL("cursorPositionChanged()"),self._cursorPositionChanged)
        #self.emit(QtCore.SIGNAL("textChanged()"))
        
    def setData(self, data, displayFilter=lambda x:True, styler=None):
        self.data = None
        self.displayFilter = displayFilter
        self.styler = styler
        self._display(data)
        self.data = data
        self.connect(data.emitter, QtCore.SIGNAL("cellChanged"), self._cellChanged)
        self.connect(data.emitter, QtCore.SIGNAL("insertRow"), self._insertRow)
        self.connect(data.emitter, QtCore.SIGNAL("takeRow"), self._takeRow)
        self.connect(data.emitter, QtCore.SIGNAL("select"), self._select)
        self._updateScrollBar2()

        # Sometimes, the block number at (0,0) is not 0.
        # It seems that it takes some time until everything settles down.
        self._generateSideBarLayout()
        self.setAlignment(QtCore.Qt.AlignLeft)
        
    def resizeEvent(self, e):
        QtGui.QTextEdit.resizeEvent(self, e)
        self._updateScrollBar2()
        self._generateSideBarLayout()
        # FIXME: this is a hack; do we have a better way to do it?
        #self.parent().sidebar.redraw()

    def showEvent(self, e):
        QtGui.QTextEdit.showEvent(self, e)
        self._updateScrollBar2()
        
    def setFilter(self, displayFilter):
        self.displayFilter = displayFilter
        self._display(self.data)
        self._updateScrollBar2()
        self._generateSideBarLayout()
        
    def getData(self):
        return self.data

    def getSegmentIndex(self, para):
        """
        @param para: paragraph number of the text pane
        @return: segment corresponding to the paragraph
        """
        try:
            return self.rownums[para]
        except IndexError:
            return None

    def getParagraphIndex(self, segid):
        p = bisect.bisect_left(self.rownums, segid)
        if self.rownums[p] == segid:
            return p
        else:
            return None

    def getSideBarLayout(self):
        return self.sideBarLayout
    
    def setKeyBindings(self, keyBindings):
        keyBindings.update(self.defaultKeyBindings)
        AccelKeyHandler.setKeyBindings(self, keyBindings)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Backspace:
            if self.textCursor().hasSelection():
                if self.blockNumberOfAnchor() != self.blockNumberOfCursor():
                    return
            elif self.textCursor().atBlockStart():
                return
        elif e.key() == QtCore.Qt.Key_Delete:
            if self.textCursor().hasSelection():
                if self.blockNumberOfAnchor() != self.blockNumberOfCursor():
                    return
            elif self.textCursor().atBlockEnd():
                return
        elif e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if self.data:
                self.data.select(self.rownums[self.currentParagraph])
                self._setParagraphBackground(self.currentParagraph,
                                             self.brushSelected)
                return
        elif e.key() == QtCore.Qt.Key_Tab:
            return
        elif e.key() >= 0x20 and e.key() <= 0xff and \
             self.blockNumberOfAnchor() != self.blockNumberOfCursor():
            return

        QtGui.QTextEdit.keyPressEvent(self, e)
    
    def insertFromMimeData(self, source):
        # Prevent text with newline or tab characters from being inserted.
        # Observed that Ctrl+V or middle mouse button invokes this method.
        if source.hasText():
            s = source.text()
            if '\t' in s or '\r' in s or '\n' in s:
                msg = "Can't paste text containing\n" \
                      "a tab or newline character."
                QtGui.QMessageBox.critical(self, "Error", msg)
                return        
        QtGui.QTextEdit.insertFromMimeData(self, source)
    
    def canInsertFromMimeData(self, source):
        # Disable drag & drop of text containing newline or tab characters.
        if source.hasText():
            s = source.text()
            if '\t' in s or '\r' in s or '\n' in s:
                return False
        return QtGui.QTextEdit.canInsertFromMimeData(self, source)
    
    def contextMenuEvent(self, event):
        # - Disable Cut and Delete menus if selected text contains
        #   a newline or tab character.
        # - Also, if the text in the clipboard has a newline or tab
        #   character, disable Paste menu.
        disableDelete = False
        cursor = self.textCursor()
        if cursor.hasSelection():
            p1 = self.document().findBlock(cursor.selectionStart()).blockNumber()
            p2 = self.document().findBlock(cursor.selectionEnd()).blockNumber()
            if p1 != p2:
                disableDelete = True
        s = self.clipboard.text()
        disablePaste = '\t' in s or '\r' in s or '\n' in s
        
        menu = self.createStandardContextMenu()
        for child in menu.children():
            if isinstance(child, QtGui.QAction):
                if not child.isSeparator():
                    name = unicode(child.text()) + ' ...' # for empty string
                    name = name.split()[0].replace('&','')
                    if name in ('Cut','Delete'):
                        child.setDisabled(disableDelete)
                    elif name == 'Paste':
                        child.setDisabled(disablePaste)
            
        menu.exec_(event.globalPos()) 
              
    def blockNumberByPosition(self, pos):
        return self.document().findBlock(pos).blockNumber()
    
    def blockNumberOfAnchor(self):
        return self.blockNumberByPosition(self.textCursor().anchor())
    
    def blockNumberOfCursor(self):
        return self.textCursor().blockNumber()
    
    def setFont(self, f):
        QtGui.QTextEdit.setFont(self, f)
        self._updateScrollBar2()
        self._generateSideBarLayout()

    def verticalScrollBar2(self, parent):
        """
        Create a separate scrollbar that simulates the behavior of the
        default (vertical) scrollbar.
        """
        if self.sb2 is None:
            sb2 = QScrollBar(parent)
            sb2.connect(sb2,SIGNAL("valueChanged(int)"),self.sb.setValue)
            sb2.connect(self.sb,SIGNAL("valueChanged(int)"),sb2.setValue)
            self.sb2 = sb2
        return self.sb2
            
    # model-to-gui
    def _cellChanged(self, i, c, v, w):
        """
        @param i: row index
        @param c: column index
        @param v: cell value
        @param w: old value
        """
        h = self.data.getColumnName(c)
        if h == 'transcript':
            p = bisect.bisect_left(self.rownums, i)
            cur = self.textCursor()
            block = cur.document().findBlockByNumber(p)
            current_text = unicode(block.text())
            # w (the old value) might be older than the text currently
            # displayed on the screen.
            if v == current_text: return
            self.disconnect(self, QtCore.SIGNAL("textChanged()"), self._textChanged)
            beg_pos = block.position()
            end_pos = beg_pos + len(w)
            cur.setPosition(beg_pos)
            cur.setPosition(end_pos, QtGui.QTextCursor.KeepAnchor)
            cur.insertText(v)
            self.connect(self, QtCore.SIGNAL("textChanged()"), self._textChanged)
            h = block.layout().boundingRect().height()
            if h != self.currentParagraphHeight:
                #self.emit(PYSIGNAL("paragraphHeightChanged"),(p,h))
                self._generateSideBarLayout()
                self.currentParagraphHeight = h
            
        
    def _insertRow(self, i, row):
        if not self.displayFilter(row): return
        p = bisect.bisect_left(self.rownums, i)
        for k in range(p,len(self.rownums)):
            self.rownums[k] += 1
        # self.rownums should be updated before the line is actually
        # inserted into the text pane because when that happens, other
        # components that depend on the list will try to look up the
        # values in the list.  if we haven't updated the list, they
        # will use the old values
        self.rownums.insert(p,i)
        # we are not changing text, but just moving it around
        # so, we don't want the _textChanged get activated
        self.disconnect(self, QtCore.SIGNAL("textChanged()"),self._textChanged)
        self.disconnect(self, QtCore.SIGNAL("cursorPositionChanged()"),self._cursorPositionChanged)
        self._setParagraphBackground(self.currentParagraph, self.brushNormal)
        self.currentParagraph = p
        cur = self.textCursor()
        islastblock = p == self.document().blockCount()
        if islastblock:
            cur.movePosition(QtGui.QTextCursor.End)
        else:
            pos = self.document().findBlockByNumber(p).position()
            cur.setPosition(pos)
        cur.insertBlock()
        if not islastblock:
            cur.movePosition(cur.PreviousBlock)
        cur.insertText(row['transcript'])
        cur.setPosition(self.document().findBlockByNumber(p).position())
        cur.movePosition(QtGui.QTextCursor.EndOfBlock)
        self.setTextCursor(cur)
        self.data.select(i)  # highlight waveform
        self.connect(self, QtCore.SIGNAL("textChanged()"),self._textChanged)
        self.connect(self, QtCore.SIGNAL("cursorPositionChanged()"),self._cursorPositionChanged)
        self.emit(QtCore.SIGNAL("paragraphInserted"), (p,))
        self._generateSideBarLayout()
        self._setParagraphBackground(self.currentParagraph, self.brushSelected)

    def _takeRow(self, i, r):
        p = bisect.bisect_left(self.rownums, i)
        if i == self.rownums[p]:
            del self.rownums[p]
            for k in range(p,len(self.rownums)):
                self.rownums[k] -= 1
            # we are not changing text, but just moving it around
            # so, we don't want the _textChanged get activated
            self.disconnect(self, QtCore.SIGNAL("textChanged()"),self._textChanged)
            cur = QtGui.QTextCursor(self.document())
            cur.beginEditBlock()
            cur.setPosition(self.document().findBlockByNumber(p).position())
            frm = self.document().rootFrame()
            if cur.movePosition(cur.NextBlock, cur.KeepAnchor):
                cur.deleteChar()
            else:
                cur.movePosition(cur.End, cur.KeepAnchor)
                cur.deleteChar()
                cur.deletePreviousChar()
            cur.endEditBlock()
            self.connect(self, QtCore.SIGNAL("textChanged()"),self._textChanged)
            #self.emit(PYSIGNAL("paragraphRemoved"), (p,))
            self._generateSideBarLayout()
            if self.rownums:
                if p >= len(self.rownums) and p > 0:
                    self.data.select(self.rownums[p-1])
                else:
                    self.data.select(self.rownums[p])
                
    def _select(self, i):
        if self.cursorPosAlreadySet:
            self.cursorPosAlreadySet = False
            return
        p = bisect.bisect_left(self.rownums, i)
        if p != self.currentParagraph:
            self.cursorPosAlreadySet = True
            cursor = self.textCursor()
            self._setParagraphBackground(self.currentParagraph, self.brushNormal)
            char = cursor.position() - cursor.block().position()
            target_block = self.document().findBlockByNumber(p)
            cursor.setPosition(target_block.position())
            self.currentParagraph = p
            self.currentParagraphHeight = target_block.layout().boundingRect().height()
            self._setParagraphBackground(p, self.brushSelected)
            self.setTextCursor(cursor)

    # self-to-self
    def _cursorPositionChanged(self):
        if self.cursorPosAlreadySet:
            self.cursorPosAlreadySet = False
            return
        block = self.textCursor().block()
        para = block.blockNumber()
        if self.data and self.currentParagraph != para:
            self.cursorPosAlreadySet = True
            self._setParagraphBackground(self.currentParagraph, self.brushNormal)
            self.data.select(self.rownums[para])
            self.currentParagraph = para
            h = block.layout().boundingRect().height()
            if h != self.currentParagraphHeight:
                # this can happen during drag&drop
                self._generateSideBarLayout()
                self.currentParagraphHeight = h
            self._setParagraphBackground(para, self.brushSelected)

    def _textChanged(self):
        # This is also called when format (color or text, etc.) changes.
        if self.data:
            p = self.currentParagraph
            segment = self.data[self.rownums[p]]
            newtext = unicode(self.document().findBlockByNumber(p).text())
            if segment['transcript'] == newtext: return
            segment['transcript'] = newtext
            h = self.document().findBlockByNumber(p).layout().boundingRect().height()
            if h != self.currentParagraphHeight:
                self._generateSideBarLayout()
                self.currentParagraphHeight = h

    # utilities
    def _setParagraphBackground(self, p, brush):
        cur = self.textCursor()
        pos = self.document().findBlockByNumber(p).position()
        cur.setPosition(pos)
        format = cur.blockFormat()
        format.setBackground(brush)
        cur.setBlockFormat(format)

    def _updateScrollBar2(self):
        if self.sb2 is not None:
            h = QFontMetrics(self.font()).lineSpacing()
            n = self.lines()
            p = self.viewport().height()
            max = n * h - p + 3 # don't know why have to add 3
            
            self.sb2.setMinValue(0)
            self.sb2.setMaxValue(max)
            self.sb2.setLineStep(20)
            self.sb2.setPageStep(p)
    
    def _generateSideBarLayout(self, *args):
        if not self.data:
            self.sideBarLayout = []
            self.sideBarLayoutChanged.emit([])
            return

        while True:
            n1 = self.cursorForPosition(QtCore.QPoint(0,0)).block().blockNumber()
            n2 = self.cursorForPosition(QtCore.QPoint(0,2)).block().blockNumber()
            if n1 <= n2: break
            time.sleep(0.1)

        L = []
        cursor = self.cursorForPosition(QtCore.QPoint(0,0))
        offset = self.verticalScrollBar().sliderPosition() 
        block = cursor.block()
        para = block.blockNumber()
        cursor = self.cursorForPosition(QtCore.QPoint(0,self.viewport().height()))
        lastBlockNumber = cursor.block().blockNumber()
        while para <= lastBlockNumber and para < len(self.data):
            layout = block.layout()
            if layout is None: break
            r = layout.boundingRect()
            p = layout.position()
            assert(para >= 0)  # to make sure
            seg = self.data[self.rownums[para]]
            
            L.append( (para,seg,int(p.y()-offset),int(r.height())) )
            block = block.next()
            para = block.blockNumber()
            
        if self.sideBarLayout != L:
            self.sideBarLayout = L
            self.sideBarLayoutChanged.emit(L)

if __name__ == "__main__":
    from transcriptdyn import *
    L = [[(None,None)]*10,
         ['sw',0,1.23,2.01,'A','male','native','how are you',1,1,1,'report'],
         ['sw',0,2.01,2.53,'B','female','native',"I'm fine",1,1,2,'report']]
    data = Transcript.importList(L)

    def myFilter(row):
        return row['speakerType'] == 'female'
            
    app = QtGui.QApplication([])
    w = TranscriptEdit()
    #w.setData(data, myFilter)
    w.setData(data)
    w.show()
    data.insertRow(1,['sw',0,2.01,2.53,'C','female','native',"Okay",1,1,2,'report'])
    app.exec_()
    
