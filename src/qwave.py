from PyQt4 import QtCore
from PyQt4 import QtGui
import qwave4
import os
import sys
import math
import copy
import sip
import locale

__all__ = ["Waveform", "WaveformWithResizableSelection"]

iconStopButton = [
    "16 16 2 1",
    "a c #ff8888",
    "  c none",
    "                ",
    "                ",
    "                ",
    "                ",
    "    aaaaaaaa    ",
    "    aaaaaaaa    ",
    "    aaaaaaaa    ",
    "    aaaaaaaa    ",
    "    aaaaaaaa    ",
    "    aaaaaaaa    ",
    "    aaaaaaaa    ",
    "    aaaaaaaa    ",
    "                ",
    "                ",
    "                ",
    "                ",
    ]

iconPlayButton = [
    "16 16 2 1",
    "a c #448844",
    "  c none",
    "                ",
    "                ",
    "                ",
    "                ",
    "    aa          ",
    "    aaaa        ",
    "    aaaaaa      ",
    "    aaaaaaaa    ",
    "    aaaaaaaa    ",
    "    aaaaaa      ",
    "    aaaa        ",
    "    aa          ",
    "                ",
    "                ",
    "                ",
    "                ",
    ]

iconRepeatButton = [
    "16 16 2 1",
    "a c #8888ff",
    "  c none",
    "                ",
    "                ",
    "                ",
    "                ",
    "                ",
    "   aaa   aaa    ",
    "  aaaaa aaaaa   ",
    "  a   aaa   a   ",
    "  a   aaa   a   ",
    "  aaaaa aaaaa   ",
    "   aaa   aaa    ",
    "                ",
    "                ",
    "                ",
    "                ",
    "                ",
    ]

iconPauseButton = [
    "16 16 2 1",
    "a c #cc88ff",
    "  c none",
    "                ",
    "                ",
    "                ",
    "                ",
    "     aa  aa     ",
    "     aa  aa     ",
    "     aa  aa     ",
    "     aa  aa     ",
    "     aa  aa     ",
    "     aa  aa     ",
    "     aa  aa     ",
    "     aa  aa     ",
    "                ",
    "                ",
    "                ",
    "                ",
    ]


class MagControl(QtGui.QSlider):
    """ Controls the waveform amplifier.
    """
    def __init__(self, waveform, vruler, parent=None):
        QtGui.QSlider.__init__(self, parent)
        self.waveform = waveform
        self.vruler = vruler
        self.setRange(-50,50)
        self.setValue(0)
        self.valueChanged.connect(self.setAmplitude)

    def setAmplitude(self, v):
        self.waveform.setAmplitudeRatio(math.pow(1.35,v/10.0))
        self.vruler.redraw()
        self.vruler.update()

    
class OutputControl(QtGui.QWidget):
    """ Controls 1) the relative volume, and 2) output channels.
    """
    def __init__(self, wform, player, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.player = player
        self.sndfile = wform.getSndFile()
        self.channel = wform.getChannel()
        self.left = QtGui.QCheckBox(parent)
        self.right = QtGui.QCheckBox(parent)
        self.vol = QtGui.QSlider(parent)

        if self.channel % 2 == 0:
            self.left.setChecked(True)
            self.right.setChecked(False)
            player.setOutputChannel(self.sndfile, self.channel, 0)
        else:
            self.left.setChecked(False)
            self.right.setChecked(True)
            player.setOutputChannel(self.sndfile, self.channel, 1)
        self.vol.setRange(0,200)
        self.vol.setValue(100)
        player.setWeight(self.sndfile, self.channel, 1.0)

        self.left.toggled.connect(self.setOutLeft)
        self.right.toggled.connect(self.setOutRight)
        self.vol.valueChanged.connect(self.setVol)
        
        layout = QtGui.QVBoxLayout(self)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.left)
        hbox.addWidget(self.right)
        layout.addLayout(hbox)
        layout.addWidget(self.vol)
        
        self.left.setMaximumWidth(16)
        self.right.setMaximumWidth(16)
        hbox.setSpacing(0)
        layout.setAlignment(self.vol, QtCore.Qt.AlignHCenter)
        layout.setStretchFactor(self.vol, 1)
        layout.setContentsMargins(0,0,0,0)
      
    def setVol(self, v):
        if self.left.isChecked() or self.right.isChecked():
            self.player.setWeight(self.sndfile, self.channel, v/100.0)

    def setOutLeft(self, v):
        if v:
            self.player.setWeight(self.sndfile, self.channel, self.vol.value()/100.0)
            if self.right.isChecked():
                self.player.setOutputChannel(self.sndfile,self.channel,-1)
            else:
                self.player.setOutputChannel(self.sndfile,self.channel,0)
        else:
            if self.right.isChecked():
                self.player.setWeight(self.sndfile, self.channel, self.vol.value()/100.0)
                self.player.setOutputChannel(self.sndfile,self.channel,1)
            else:
                self.player.setWeight(self.sndfile, self.channel, 0.0)

    def setOutRight(self, v):
        if v:
            self.player.setWeight(self.sndfile, self.channel, self.vol.value()/100.0)
            if self.left.isChecked():
                self.player.setOutputChannel(self.sndfile,self.channel,-1)
            else:
                self.player.setOutputChannel(self.sndfile,self.channel,1)
        else:
            if self.left.isChecked():
                self.player.setWeight(self.sndfile, self.channel, self.vol.value()/100.0)
                self.player.setOutputChannel(self.sndfile,self.channel,0)
            else:
                self.player.setWeight(self.sndfile, self.channel, 0.0)


class WaveformWithResizableSelection(qwave4.Waveform):
    """  WaveformWithResizableSelection combines WaveformSelectionProxy
    and WaveformCursorProxy to support a resizable selection.

    In terms of programming model, this class allows programmers to
    avoid dealing with WaveformSelectionProxy and WaveformCursorProxy
    directly.  Instead, it creates an illusion that this waveform
    class defines the selection, cursor and player cursor in it and
    manages them by default.
    """
    
    def __init__(self, sndfile, ch, beg, dur,
                 selProxy, curProxy, parent=None):
        qwave4.Waveform.__init__(self, sndfile, ch, beg, dur, parent)
        selProxy.registerWaveform(self)
        curProxy.registerWaveform(self)
        self.selectionProxy = selProxy
        self.cursorProxy = curProxy
        self.resizing = False
        self.resizeModifier = QtCore.Qt.ShiftModifier
        self.keyState = None
        self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.setMouseTracking(True)

    def isSelectionResizing(self):
        """ Tells whether the selection is being resized.

        @return: Whether the selection is being resized.
        @rtype: Boolean
        """
        return self.resizing

    def setSelectionResizing(self, v):
        self.resizing = v
        
    def setResizeModifier(self, modifier):
        """ Set resize modifier.

        Resize modifier is the key that activate resizing. User should
        hold this key while moving the mouse in order to resize the
        selection.

        @param modifier: The modifier key.
        @type modifier: Qt.ButtonState
        """
        self.resizeModifier = modifier

    def getKeyState(self):
        """
        @return: The button state at the time of the last mouse event
        on the waveform.  It's actually the value of Event::state()
        call.
        @type: Qt.ButtonState
        """
        return self.keyState
        
    def getResizeModifier(self):
        """ Resize modifier is a modifier key, e.g. "Ctrl", "Shift",
        etc.  To resize a selected region on the waveform, the user
        can point the mouse to an edge of the region while holding
        the modifier key.

        @return: Resize modifier.
        @rtype: Qt.ButtonState
        """
        return self.resizeModifier

    def setAmplitude(self, v):
        self.setAmplitudeRatio(math.pow(1.35,-v/10.0))

    def mousePressEvent(self, e):
        self.keyState = e.modifiers()
        if self.keyState & self.resizeModifier:
            if self.selectionProxy.getSelectedWaveform() == self:
                x = self.cursorProxy.getCursorPositionSeconds()
                beg = self.selectionProxy.getBeginSeconds()
                end = beg + self.selectionProxy.getWidthSeconds()
                delta = self.getSecondsPerPixel() * 2.0
                if abs(x-beg) < delta:
                    self.resizing = True
                    self.selectionProxy.expandSelectionBegin(self, beg)
                    self.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
                elif abs(x-end) < delta:
                    self.resizing = True
                    self.selectionProxy.expandSelectionEnd(self, end)
                    self.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
        else:
            self.resizing = False
            qwave4.Waveform.mousePressEvent(self, e)
            self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
            
    def mouseReleaseEvent(self, e):
        qwave4.Waveform.mouseReleaseEvent(self, e)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        if self.resizing:
            self.resizing = False
                
    def mouseMoveEvent(self, e):
        self.keyState = e.modifiers()
        qwave4.Waveform.mouseMoveEvent(self, e)

        if self.keyState & self.resizeModifier and \
           e.buttons() == QtCore.Qt.NoButton and \
           self.selectionProxy.getSelectedWaveform() == self:
            x = self.cursorProxy.getCursorPositionSeconds()
            beg = self.selectionProxy.getBeginSeconds()
            end = beg + self.selectionProxy.getWidthSeconds()
            delta = self.getSecondsPerPixel() * 2.0
            if min(abs(x-beg),abs(x-end)) < delta:
                self.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
            else:
                self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        elif e.buttons() & QtCore.Qt.LeftButton:
            self.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
            x = self.cursorProxy.getCursorPositionSeconds()
            beg = self.getBeginSeconds()
            end = beg + self.getWidthSeconds()
            if x < beg and x >= 0.0:
                self.display(x)
            elif x > end:
                self.display(beg + x - end)
        else:
            self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))


class WaveformGrid(QtGui.QWidget):
    """ WaveformGrid is a grid containing a stack of waveforms.

    It has a ruler at the top row, and you can add as many waveforms as
    you want from the second row.  Column 1 is the vertical ruler,
    column 3 is a slider that is used to magnify the waveform, and
    column 4 is a slider for volume control and a check box for mutt.
    But, you don't need to worry about these, they are created and
    managed automatically.
    """
    def __init__(self, player, waveformCls=WaveformWithResizableSelection, parent=None):
        """
        @param parent:
        @type parent: Waveform
        """
        QtGui.QWidget.__init__(self, parent)
        self.waveformCls = waveformCls
        self.ruler1 = qwave4.WaveformRuler(True, self)
        self.ruler2 = qwave4.WaveformRuler(False, self)
        self.selection = qwave4.WaveformSelectionProxy(self)
        self.cursor = qwave4.WaveformCursorProxy(self)
        #self.magAndOutCons = []
        #self.waveforms = []
        self.widgets = []
        self.player = player
        # ruler waveform is a waveform that horizontal rulers are connected to
        self.rulerWaveform = None
        self.ignoreWaveformHorizontallyChanged = False
        self.mutex = QtCore.QMutex()
        self.grid = None
        self.resetLayout()
                
    def __len__(self):
        return self.grid.rowCount()-2

    def _widgetrowidx(self, widget, col):
        for i in range(1,len(self.widgets)+1):
            if self.grid.itemAtPosition(i,col).widget() == widget:
                return i
            
    def _waveformHorizontallyChanged(self, beg, dur):
        self.mutex.lock()
        if self.ignoreWaveformHorizontallyChanged:
            self.mutex.unlock()
            return
        self.ignoreWaveformHorizontallyChanged = True
        self.mutex.unlock()
        for _, wform, _, _ in self.widgets:
            if id(wform) == id(self.sender()): continue
            s = wform.getBeginSeconds()
            d = wform.getWidthSeconds()
            if s != beg or d != dur:
                wform.display(beg, dur)
        self.mutex.lock()
        self.ignoreWaveformHorizontallyChanged = False
        self.mutex.unlock()
                
    def getCellWidth(self, c):
        return self.grid.cellGeometry(0,c).width()
    
    def getSelectionProxy(self):
        return self.selection

    def getCursorProxy(self):
        return self.cursor
    
    def getRowIndex(self, sndfile, ch):
        for i, (_,wform,_,_) in enumerate(self.widgets):
            if wform.getSndFile() == sndfile and wform.getChannel() == ch:
                return i

    def getWaveform(self, sndfile, ch):
        for _, wform, _, _ in self.widgets:
            if wform.getSndFile() == sndfile and wform.getChannel() == ch:
                return wform

    def getWaveforms(self):
        return [x[1] for x in self.widgets]
    
    def insertRow(self, sndfile, ch, row, waveformOnly=False):
        if row < 0:
            logical_row_num = 0
        elif row > len(self.widgets):
            logical_row_num = len(self.widgets)
        else:
            logical_row_num = row

        if len(self.widgets) > 0:
            # get any existing waveform
            w0 = self.grid.itemAtPosition(1,1).widget()
            beg = w0.getBeginSeconds()
            dur = w0.getWidthSeconds()
        else:
            # FIXME: user needs to specify these
            beg = 0.0
            dur = 60.0

        # add the waveform to the grid
        wave = self.waveformCls(
            sndfile, ch, beg, dur, self.selection, self.cursor, self)
        wave.show()  # prevents segfault
        
        if waveformOnly == False:
            vr = qwave4.WaveformVRuler(self)
            mc = MagControl(wave, vr, self)
            oc = OutputControl(wave, self.player, self)
            vr.connectToWaveform(wave)
        else:
            vr = mc = oc = None

        # connect rulers to the first waveform
        if self.rulerWaveform == None:
            self.ruler1.connectToWaveform(wave)
            self.ruler2.connectToWaveform(wave)
            self.rulerWaveform = wave
            
        wave.waveformHorizontallyChanged.connect(self._waveformHorizontallyChanged)
       
        self.widgets.insert(logical_row_num, (vr,wave,mc,oc))
        self.resetLayout()
        
        return True

    def removeRow(self, row):
        if row < 0 or row >= len(self.widgets): return

        # wipe out the target row
        for j in range(4):
            if self.widgets[row][j]:
                sip.delete(self.widgets[row][j])
        del self.widgets[row]
        
        # reset ruler waveform
        if len(self.widgets) > 0:
            self.rulerWaveform = self.widgets[0][1]
            self.ruler1.connectToWaveform(self.rulerWaveform)
            self.ruler2.connectToWaveform(self.rulerWaveform)
        else:
            self.rulerWaveform = None
            
        self.resetLayout()

    def resetLayout(self):
        # reorganize the layout
        if self.layout():
            self.grid = None
            sip.delete(self.layout())
        grid = QtGui.QGridLayout()
        grid.setSpacing(2)
        grid.setContentsMargins(0,0,0,0)
        grid.addWidget(self.ruler1, 0, 1)
        grid.addWidget(self.ruler2, len(self.widgets)+1, 1)
        
        for i, widgets in enumerate(self.widgets):
            grid.setRowStretch(i+1,1)  # do this before widgets are laid out
            for j in range(4):
                if widgets[j]:
                    grid.addWidget(widgets[j], i+1, j)

        self.setLayout(grid)
        self.grid = grid
            
        
    def swapRows(self, r1, r2):
        if r1 < 0 or r1 >= len(self.widgets) or \
           r2 < 0 or r2 >= len(self.widgets):
            return

        save1 = self.widgets[r1]
        save2 = self.widgets[r2]
        del self.widgets[r1]
        del self.widgets[r2]
        
        if r1 < r2:
            self.widgets.insert(r1, save2)
            self.widgets.insert(r2, save1)
        elif r2 < r1:
            self.widgets.insert(r2, save1)
            self.widgets.insert(r1, save2)
            
        self.resetLayout()
        
    def moveRow(self, r1, r2):
        if r1 < 0 or r1 >= len(self.widgets):
            return
        if r2 < 0:
            r2 = 0
        elif r2 > len(self.widgets):
            r2 = len(self.widgets)

        save = self.widgets[r1]
        del self.widgets[r1]
        
        if r1 < r2:
            self.widgets.insert(r2-1,save)
        elif r1 > r2:
            self.widgets.insert(r2,save)

        self.resetLayout()
        
    def hideRow(self, row):
        if row < 0 or row >= len(self.widgets):
            return
        for j in range(4):
            self.widgets[row][j].hide()

    def showRow(self, row):
        if row < 0 or row >= len(self.widgets):
            return
        for j in range(4):
            self.widgets[row][j].show()

    def numRows(self):
        return len(self.widgets)
    

class MyEntry(QtGui.QLineEdit):
    def __init__(self, w, parent=None):
        """
        @param w: instance of Waveform
        """
        QtGui.QLineEdit.__init__(self, parent)
        self.wave = w

    def customEvent(self, e):
        if e.type() == qwave4.PlayerPosition:
            self.setTime(self.wave.player.playerPosition())

    def setTime(self, t):
        self.setText(qwave4.time2str(t, 4))
        
class Waveform(QtGui.QWidget):
    """ Waveform is an all-in-one class that includes waveforms,
    audio player, and palyback control.
    """

    def __init__(self, parent=None, waveformCls=WaveformWithResizableSelection):
        QtGui.QWidget.__init__(self, parent)
        self.waveformCls = waveformCls

        ####################
        # UI
        #
        tm = MyEntry(self, self)
        tb = qwave4.TimeLabel(self)
        te = qwave4.TimeLabel(self)
        td = qwave4.TimeLabel(self)

        playIcon = QtGui.QIcon(QtGui.QPixmap(iconPlayButton))
        repeatIcon = QtGui.QIcon(QtGui.QPixmap(iconRepeatButton))
        pauseIcon = QtGui.QIcon(QtGui.QPixmap(iconPauseButton))
        stopIcon = QtGui.QIcon(QtGui.QPixmap(iconStopButton))
        
        playBtn = QtGui.QPushButton(playIcon,'')
        repeatBtn = QtGui.QPushButton(repeatIcon,'')
        pauseBtn = QtGui.QPushButton(pauseIcon,'')
        stopBtn = QtGui.QPushButton(stopIcon,'')

        speedSlider = QtGui.QSlider(self)
        speedBtn = QtGui.QPushButton("1.00", self)

        if sys.platform == 'win32':
            player = qwave4.getPlayer(self.winId())
        else:
            player = qwave4.getPlayer()
        grid = WaveformGrid(player, self.waveformCls, self)

        sb = qwave4.WaveformScrollBar(self)

        vbox = QtGui.QVBoxLayout(self)
        hbox = QtGui.QHBoxLayout()
        
        vbox.addLayout(hbox)
        hbox.addWidget(tm)
        hbox.addWidget(tb)
        hbox.addWidget(te)
        hbox.addWidget(td)
        hbox.addStretch()
        hbox.addWidget(playBtn)
        hbox.addWidget(repeatBtn)
        hbox.addWidget(pauseBtn)
        hbox.addWidget(stopBtn)
        hbox.addWidget(speedSlider)
        hbox.addWidget(speedBtn)
        vbox.addWidget(grid)
        vbox.addWidget(sb)
        vbox.setStretchFactor(hbox,0)
        vbox.setStretchFactor(grid,1)

        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(5)
        vbox.setContentsMargins(0,0,0,0)
        hbox.setSpacing(2)
        
        tb.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Sunken)
        te.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Sunken)
        td.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Sunken)

        tm.setFixedSize(85,20)
        tb.setFixedSize(85,20)
        te.setFixedSize(85,20)
        td.setFixedSize(85,20)

        tm.setAlignment(QtCore.Qt.AlignRight)
        tb.setAlignment(QtCore.Qt.AlignRight)
        te.setAlignment(QtCore.Qt.AlignRight)
        td.setAlignment(QtCore.Qt.AlignRight)

        playBtn.setFixedSize(20,20)
        repeatBtn.setFixedSize(20,20)
        pauseBtn.setFixedSize(20,20)
        stopBtn.setFixedSize(20,20)

        playBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        repeatBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        pauseBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        stopBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        
        speedSlider.setOrientation(QtCore.Qt.Horizontal)
        speedSlider.setFixedWidth(60)
        speedSlider.setMinimum(-10)
        speedSlider.setMaximum(10)

        speedBtn.setFixedSize(24,16)
        f = speedBtn.font()
        f.setPixelSize(8)
        speedBtn.setFont(f)

        ####################
        # behaviour
        #
        regex = QtCore.QRegExp("((([0-9]+):)?([0-9]+):)?([0-9]+\.?[0-9]*)")
        validator = QtGui.QRegExpValidator(regex, tm)
        tm.setValidator(validator)
        
        player.initialize()
        player.enableTicker()
        ticker = player.getPlayerTicker()

        cursor = grid.getCursorProxy()
        selection = grid.getSelectionProxy()
        selectionColor = QtGui.QColor(QtCore.Qt.red)
        unfocusedRegionColor = QtGui.QColor(QtCore.Qt.yellow)
        selection.setColorScheme(selectionColor, unfocusedRegionColor)

        ticker.registerReceiver(tm)
        ticker.registerReceiver(sb)
        ticker.registerReceiver(cursor)

        playBtn.clicked.connect(self.play)
        repeatBtn.clicked.connect(self.repeat)
        pauseBtn.clicked.connect(self.pauseOrResume)
        stopBtn.clicked.connect(self.stop)
        speedSlider.valueChanged.connect(self.setSpeed)
        speedBtn.clicked.connect(self.resetSpeed)
        selection.waveformSelectionChanged.connect(self.waveformSelectionChanged)
        tm.returnPressed.connect(self._gotoTime)

        ####################
        # fields
        #
        self.selectionColor = selectionColor
        self.unfocusedRegionColor = unfocusedRegionColor

        self.grid = grid
        self.sb = sb

        self.tm = tm
        self.tb = tb
        self.te = te
        self.td = td
        self.playBtn = playBtn
        self.repeatBtn = repeatBtn
        self.pauseBtn = pauseBtn
        self.stopBtn = stopBtn
        self.speedBtn = speedBtn
        self.speedSlider = speedSlider
        self.hasRuler = False
        self.sndfiles = {}
        self.dummysndfiles = {}

        ##
        ## public properties
        self.player = player
        self.cursor = cursor
        self.selection = selection  # the selection proxy
        
    ####################
    # signal emitters
    #
    def waveformSelectionChanged(self, beg, dur, wform):
        """ Process the WaveformSelectionProxy.waveformSelectionChanged
        signal to set labels (TimeLabels) that display the configuration
        of the selection.
        """
        
        self.tb.setTime(beg)
        self.te.setTime(beg+dur)
        self.td.setTime(dur)
        
    ####################
    # player control
    #
    def play(self):
        self.pauseBtn.setDown(False)
        beg = self.selection.getBeginSeconds()
        dur = self.selection.getWidthSeconds()
        self.player.play(beg, dur)

    def playRegion(self, beg, dur):
        self.pauseBtn.setDown(False)
        self.player.play(beg, dur)
        
    def repeat(self):
        self.pauseBtn.setDown(False)
        beg = self.selection.getBeginSeconds()
        dur = self.selection.getWidthSeconds()
        self.player.repeat(beg, dur)
        
    def pauseOrResume(self):
        if self.player.isDevicePlaying():
            self.player.pause()
            self.pauseBtn.setDown(True)
        else:
            self.player.resume()
            self.pauseBtn.setDown(False)

    def stop(self):
        self.pauseBtn.setDown(False)
        self.player.stop()

    def setSpeed(self, r):
        speed = math.pow(2.0,r/10.0)
        self.player.setSpeed(speed)
        self.speedBtn.setText("%.2f"%speed)

    def resetSpeed(self):
        self.speedSlider.setValue(0)
    
    ##############################
    # waveform layout
    #
    def placeWaveform(self, filename, ch, i, waveformOnly=False):
        try:
            sndfile = self.sndfiles[filename]
        except KeyError:
            return

        if self.grid.insertRow(sndfile, ch, i, waveformOnly):
            w = self.grid.getWaveform(sndfile, ch)
            self.sb.registerWaveform(w)
            w.waveformMouseMoved.connect(self._setCursorLocOnTimeLabel)
            self.player.setWeight(sndfile, ch, 1.0)
        else:
            row = self.grid.getRowIndex(sndfile, ch)
            self.grid.moveRow(row, i)

    def hideWaveform(self, filename, ch):
        try:
            sndfile = self.sndfiles[filename]
        except KeyError:
            return
        row = self.grid.getRowIndex(sndfile, ch)
        self.grid.hideRow(row)
        #self.player.setWeight(sndfile, ch, 0.0)

    ##############################
    # sndfiles
    #
    def addSndFile(self, filename, addToPlayer=True):
        """
        @param filename: A unicode string.
        """
        if filename in self.sndfiles: return
        s = qwave4.SndFile(filename.encode(locale.getpreferredencoding()))
        self.player.addSndFile(s)
        for ch in range(0,s.getChannels()):
            self.player.setWeight(s, ch, 0.0)
        self.sndfiles[filename] = s
        return s

    def addDummySndFile(self, sndfile):
        name = sndfile.getFileName()
        if name in self.sndfiles: return
        self.sndfiles[name] = sndfile
        self.dummysndfiles[name] = True
        return sndfile
        
    def removeSndFile(self, filename):
        """ Remove the given audio file from the waveform display and player.
        """
        try:
            sndfile = self.sndfiles[filename]
        except KeyError:
            return
        for ch in range(sndfile.getChannels()):
            w = self.grid.getWaveform(sndfile, ch)
            self.sb.unregisterWaveform(w)
            i = self.grid.getRowIndex(sndfile, ch)
            if i is not None:
                self.grid.removeRow(i)
        self.player.stop()
        self.player.removeSndFile(sndfile)
        del self.sndfiles[filename]

    def removeDummySndFile(self, sndfile):
        filename = sndfile.getFileName()
        if filename not in self.sndfiles: return
        for ch in range(sndfile.getChannels()):
            w = self.grid.getWaveform(sndfile, ch)
            self.sb.unregisterWaveform(w)
            i = self.grid.getRowIndex(sndfile, ch)
            if i is not None:
                self.grid.removeRow(i)
        del self.sndfiles[filename]
        del self.dummysndfiles[filename]
        
    def getSndFiles(self):
        """
        @return: Dictionary of audio filename and SndFile.
        """
        return copy.copy(self.sndfiles)
    
    ### other
    def getLeftMargin(self):
        return self.grid.getCellWidth(0)
        
    def numWaveforms(self):
        return self.grid.numRows()

    def getMaxEndTime(self):
        t = -9999999.0
        for sndfile in self.sndfiles.values():
            if sndfile.getFileName() in self.dummysndfiles:
                continue
            t = max(t,sndfile.getLengthSeconds())
        return t

    def getWaveforms(self):
        return self.grid.getWaveforms()
    
    def getWaveform(self, filename, ch):
        """ Returns the specified waveform.

        @param filename: Audio file name containing the waveform.
        @type filename: str
        @param ch: Channel of the audio file containing the waveform.
        @type ch: int
        """
        if filename in self.sndfiles:
            return self.grid.getWaveform(self.sndfiles[filename], ch)
    
    def getChannels(self, filename):
        if filename in self.sndfiles:
            return self.sndfiles[filename].getChannels()
        else:
            return None
        
    def getSelectedRegionS(self):
        x = self.selection.getBeginSeconds()
        y = x + self.selection.getWidthSeconds()
        wid = self.selection.getSelectedWaveform()
        return (wid, x, y)

    def getCursorPositionS(self):
        return self.cursor.getCursorPositionSeconds()
        
    def setSelectionColorScheme(self, focused=None, unfocused=None):
        """ Set colors for selection and unfocused regions.

        @param focused: The color of the selection.
        @type focused: QColor
        @param unfocused: The color of the unfocused regions.
        @type unfocused: QColor
        """
        if focused is None:
            focused = self.selectionColor
        if unfocused is None:
            unfocused = self.unfocusedRegionColor
        self.selection.setColorScheme(focused, unfocused)
        beg = self.selection.getBeginSeconds()
        dur = self.selection.getWidthSeconds()
        wform = self.selection.getSelectedWaveform()
        self.selection.select(beg, dur, wform)

    def markRegionS(self, filename, ch, beg, end, scroll=True):
        try:
            sndfile = self.sndfiles[filename]
        except KeyError:
            return

        wform = self.grid.getWaveform(sndfile, ch)
        if wform is None: return
        
        s = wform.getBeginSeconds()
        w = wform.getWidthSeconds()
        d = wform.getSecondsPerPixel()

        if scroll:
            if s + d > end:
                s = beg;
            elif s + w - d < beg:
                s = end - w
            for path,sndfile in self.sndfiles.items():
                for ch in range(sndfile.getChannels()):
                    w = self.grid.getWaveform(sndfile, ch)
                    if w is not None:
                        w.display(s)

        self.selection.select(beg, end-beg, wform)
        self.tb.setTime(beg)
        self.te.setTime(end)
        self.td.setTime(end-beg)
            
            
    def zoomInRegion(self, beg, end):
        for wform in self.grid.getWaveforms():
            wform.display(beg, end-beg)

    def zoomInAtCursor(self):
        wforms = self.grid.getWaveforms()
        if wforms:
            a = wforms[0].getBeginSeconds()
            dur = wforms[0].getWidthSeconds() / 2.0
            x = self.cursor.getCursorPositionSeconds()
            beg = a + (x-a)/2.0
            for wform in wforms:
                wform.display(beg, dur)
                #wform.display(beg+dur/2.0)

    def zoomOutAtCursor(self):
        wforms = self.grid.getWaveforms()
        if wforms:
            a = wforms[0].getBeginSeconds()
            dur = wforms[0].getWidthSeconds() * 2.0
            x = self.cursor.getCursorPositionSeconds()
            beg = a - (x-a)
            for wform in wforms:
                wform.display(beg, dur)

    def zoomAtCenter(self, f):
        """ Zoom in/out at the center of the displayed waveform.
        It takes an argument f which is a zoom factor.  If f is larger than
        1.0, the interval of the viewing window is extended, thus the
        waveform is zoomed out.  If f is smaller than 1.0, the viewing
        window gets smaller and the waveform is zoomed in.

        @param f: Zoom factor.
        @type f: float
        """
        wforms = self.grid.getWaveforms()
        if wforms:
            dur = wforms[0].getWidthSeconds()
            dur2 = dur / f
            a = wforms[0].getBeginSeconds() + (dur-dur2)/2.0
            for wform in wforms:
                wform.display(a, dur2)

    def moveCenterAtCursor(self):
        wforms = self.gridWidgets.keys()
        if wforms:
            dur = wforms[0].getWidthSeconds()
            x = self.cursor.getCursorPositionSeconds()
            beg = x - dur/2.0
            for wform in wforms:
                wform.display(beg, dur)

    def moveCenterAt(self, t):
        wforms = self.grid.getWaveforms()
        if wforms:
            dur = wforms[0].getWidthSeconds()
            beg = t - dur/2.0
            wforms[0].display(beg, dur)
            
    def _setCursorLocOnTimeLabel(self, waveform, t):
        """ Used to connect Waveform.waveformMouseMoved and
        TimeLabel.setTime.
        """
        self.tm.setTime(t)

    def _gotoTime(self):
        grp = self.tm.validator().regExp().capturedTexts()
        #for i in range(len(grp)): print i, grp[i]
        hh = grp[3].toInt()[0] * 3600
        mm = grp[4].toInt()[0] * 60
        ss = grp[5].toFloat()[0]
        self.moveCenterAt(hh + mm + ss)
        
        
if __name__ == "__main__":
    app = QtGui.QApplication([])
    vbox = QtGui.QWidget()
    layout = QtGui.QVBoxLayout(vbox)
    w = Waveform(vbox)
    def f():
        w.hideWaveform("sw.wav", 0)
        wf1 = w.getWaveform("sw.wav",0)
        wf2 = w.getWaveform("sw.wav",1)
        print wf1.getCanvas().width(), wf1.getCanvas().height()
        print wf2.getCanvas().width(), wf2.getCanvas().height()
    b = QtGui.QPushButton("do something", vbox)
    layout.addWidget(w)
    layout.addWidget(b)
    b.connect(b,QtCore.SIGNAL("clicked()"),f)
    vbox.show()
    w.addSndFile("sw.wav")
    w.placeWaveform("sw.wav", 0, 0)
    w.placeWaveform("sw.wav", 1, 0)
    app.exec_()
    
