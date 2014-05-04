from PyQt4 import QtCore
from PyQt4 import QtGui
from qwave import *
import qwave4
import bisect
import copy
import os
import sip

__all__ = ["TranscriptWaveform", "TransAudioAssocDialog"]

class TranscriptWaveform(Waveform):
    def __init__(self, *args, **kw):
        Waveform.__init__(self, *args, **kw)
        self._id2path = {}
        self._path2id = {}
        self._filter = lambda x:True

        ##
        ## public properties
        self.data = None    # data proxy
        # this is the segment (data row) that is associated with
        # the currently selected region
        self.currentSegment = None
        self.currentSegmentIdx = None

    def setData(self, data):
        self.data = data
        self.connect(data.emitter, QtCore.SIGNAL("select"), self._select)
        self.connect(data.emitter, QtCore.SIGNAL("cellChanged"), self._cellChanged)
        self.connect(data.emitter, QtCore.SIGNAL("takeRow"), self._takeRow)
        
    def setFilter(self, filter):
        self._filter = filter

    def getAssociationMap(self):
        return copy.copy(self._id2path)

    def getAssociationForWaveform(self, wform):
        """
        Given waveform, returns an associated transcript file id and
        channel.
        """
        sndfile = wform.getSndFile()
        filename = sndfile.getFileName()
        channel = wform.getChannel()
        try:
            return self._path2id[filename,channel]
        except KeyError:
            return None
        
    def setAssociation(self, fileid, ch1, filepath, ch2):
        self._id2path[fileid,ch1] = (filepath,ch2)
        self._path2id[filepath,ch2] = (fileid,ch1)

    def unsetAssociation(self, fileid, ch):
        if (fileid,ch) in self._id2path:
            filepath, ch2 = self._id2path[(fileid,ch)]
            del self._path2id[(filepath,ch2)]
            del self._id2path[(fileid,ch)]

    def waveformSelectionChanged(self, beg, dur, wform):
        """ This method responds to the waveformSelectionChanged signal
        of WaveformSelectionProxy.

        There are three cases when the selection is changed:

          1. The selection is being created.
        
          2. The selection is being resized and it is associated with
          a segment.

          3. The selection is being resized but it is not associated with
          any segment.

        In case 1, nothing is done until the selection overlaps
        with a segment.  If it overlaps with any segments, we interpret
        this as a selection of the overlapped segment.  Thus, the first
        overlapped segment becomes the selection.

        In case 2, the span of the associated segment is changed as the
        span of the selection is changed.

        In case 3, nothing is done.
        """

        # this prevents selection from going beyond 0.0
        if beg < 0.0:
            self.selection.expandSelection(wform,0.0)
            return
        
        # this sets the TimeLabels
        Waveform.waveformSelectionChanged(self, beg, dur, wform)

        if wform.isSelectionResizing():
            if self.currentSegment is not None:
                # Case 2.
                fileid = self.currentSegment['file']
                ch = self.currentSegment['channel']
                spkr = self.currentSegment['speaker']
                n = self.currentSegment.num
                oldStartTime = self.currentSegment['start']
                oldEndTime = self.currentSegment['end']
                newStartTime = beg
                newEndTime = beg + dur
                try:
                    secBs = self.data.getMetadata('sectionBoundaries',True)
                except KeyError:
                    secBs = None
                if oldStartTime > newStartTime:
                    for i in range(n-1,-1,-1):
                        row = self.data[i]
                        if row['file']==fileid and \
                           row['channel']==ch and \
                           row['speaker']==spkr:
                            if row['end'] > beg:
                                newStartTime = row['end']
                                self.selection.expandSelection(wform,row['end'])
                            break
                    if secBs:
                        i = bisect.bisect_left(secBs,newStartTime)
                        if secBs[i] < newEndTime:
                            newStartTime = secBs[i]
                if oldEndTime < newEndTime:
                    for i in range(n+1, len(self.data)):
                        row = self.data[i]
                        if row['file']==fileid and \
                           row['channel']==ch and \
                           row['speaker']==spkr:
                            if row['start'] < beg + dur:
                                newEndTime = row['start']
                                self.selection.expandSelection(wform,row['start'])
                            break
                    if secBs:
                        i = bisect.bisect_right(secBs,newEndTime) -1
                        if secBs[i] > newStartTime:
                            newEndTime = secBs[i]

                if self.currentSegment['start'] > newStartTime:
                    for i in range(n-1,-1,-1):
                        if self.data[i]['start'] > newStartTime:
                            r = self.data.takeRow(n)
                            self.data.insertRow(i, r)
                            break
                elif self.currentSegment['start'] < newStartTime:
                    for i in range(n+1, len(self.data)):
                        if self.data[i]['start'] < newStartTime:
                            r = self.data.takeRow(n)
                            self.data.insertRow(i, r)
                            break

                self.currentSegment['start'] = newStartTime
                self.currentSegment['end'] = newEndTime
            # Case 3.
            return

        # control reaches here, then the selection is being created
        # thus, existing selection-segment association should be reset
        self.currentSegment = None
        self.currentSegmentIdx = None
        self.setSelectionColorScheme(focused=QtGui.QColor(QtCore.Qt.red))

        # Case 1: check ovelapping segments.
        if wform.getKeyState() == QtCore.Qt.ControlModifier and \
           not self.player.isDevicePlaying():
            sndfile = wform.getSndFile()
            filename = sndfile.getFileName()
            ch = wform.getChannel()
            try:
                fileid, ch = self._path2id[(filename,ch)]
            except KeyError:
                return

            end = beg + dur
            h = []
            for row in self.data:
                if self._filter(row) and \
                   row['file']==fileid and \
                   row['channel']==ch:
                    t1 = row['start']
                    t2 = row['end']
                    if t1 < end and  t2 > beg:
                        h.append((t2-t1,row.num))
            if h:
                h.sort()
                self.data.select(h[0][1])


    ####################
    # model-to-gui
    #
    def _cellChanged(self, i, c, v, w):
        """
        @param i: row index
        @param c: column index
        @param v: cell value
        @param w: old value
        """
        h = self.data.getColumnName(c)
        if h == 'start':
            if self.currentSegment and  i == self.currentSegment.num:
                f = self.currentSegment['file']
                ch = self.currentSegment['channel']
                try:
                    fn,ch = self._id2path[f,ch]
                except KeyError:
                    return
                e = self.currentSegment['end']
                self.markRegionS(fn, ch, v, e)
        elif h == 'end':
            if self.currentSegment and  i == self.currentSegment.num:
                f = self.currentSegment['file']
                ch = self.currentSegment['channel']
                try:
                    fn,ch = self._id2path[f,ch]
                except KeyError:
                    return
                s = self.currentSegment['start']
                self.markRegionS(fn, ch, s, v)

    def _select(self, i):
        row = self.data[i]
        f = row['file']
        ch = row['channel']
        s = row['start']
        e = row['end']
        try:
            fn,ch = self._id2path[(f,ch)]
        except KeyError:
            return
        
        # create the selection and
        # associate it with the segment(row=self.data[i])
        self.setSelectionColorScheme(focused=QtGui.QColor(QtCore.Qt.blue))
        self.markRegionS(fn, ch, s, e)
        self.currentSegment = row
        self.currentSegmentIdx = row.num

    def _takeRow(self, i, r):
        if i == self.currentSegmentIdx:
            self.currentSegment = None
            self.currentSegmentIdx = None
            
############################################################
# Transcript-audio association
#
class MyLineEdit(QtGui.QLineEdit):
    """ To be used as a label with sunken frame.

    QLabel can't handle long string nicely because it takes too much of the
    available space.  MyLineEdit can be considered as a window of the
    long string.  Only a portion of the string is displayed on the
    windows at a time, saving the space.
    """
    def __init__(self, *args):
        QtGui.QLineEdit.__init__(self, *args)
        self.setReadOnly(True)
        #self.setFrameStyle(self.Box | self.Sunken)
        #self.setLineWidth(1)
        #self.setMidLineWidth(0)

class MyLabel(QtGui.QLabel):
    """ Label with sunken box frame.
    """
    def __init__(self, *args):
        QtGui.QLabel.__init__(self, *args)
        self.setFrameStyle(self.Box | self.Sunken)
        self.setLineWidth(1)
        self.setMidLineWidth(0)

class MyComboBox(QtGui.QComboBox):
    """ Specialized for audio channels.

    This combo box is used in conjunction with another combo box called
    primary combo box.  User selects the name of the audio file from the
    primary combo box and its index is delivered to the reset slot.
    We map this index to a SndFile object corresponding to the selected
    audio file, then channels existing on the SndFile is added to this
    combo box.
    """
    def __init__(self, sndfiles, parent=None):
        """
        @param sndfiles: List of SndFiles.  This list is aligned with
        the items in the primary combo box.
        """
        QtGui.QComboBox.__init__(self, parent)
        self.sndfiles = sndfiles
        self.addItem("-- select --")
        
    def reset(self, i):
        """
        @param i: Index of the selected item of the primary combo box.
        """
        if i == 0: return
        self.clear()
        self.addItem("-- select --")
        for ch in range(self.sndfiles[i-1].getChannels()):
            self.insertItem(ch+1, str(ch))
        
class TransAudioAssocDialog(QtGui.QDialog):
    def __init__(self, data, wave, parent=None):
        """
        @param data: Transcript data.
        @type data: Transcript
        @param wave: Waveform.
        @type wave: TranscriptWaveform
        """
        QtGui.QDialog.__init__(self, parent)
        vbox = QtGui.QVBoxLayout(self)
        grid = QtGui.QGridLayout()
        vbox.addLayout(grid)
        grid.setSpacing(5)
        grid.setMargin(5)

        assoc = wave.getAssociationMap()
        sndfiles = wave.getSndFiles()

        h = {}
        for row in data:
            h[(row['file'],row['channel'])] = 1
        trans = h.keys()
        trans.sort()
        
        grid.addWidget(QtGui.QLabel("Transcript",self), 0, 0)
        grid.addWidget(QtGui.QLabel("Channel",self), 0, 1)
        grid.addWidget(QtGui.QLabel("Audio file",self), 0, 3)
        grid.addWidget(QtGui.QLabel("Channel",self), 0, 4)

        comboList = sndfiles.keys()
        comboList.sort()
        sndFileList = [sndfiles[k] for k in comboList]

        table = []
        for i,(fileid,filech) in enumerate(trans):
            r = i + 1
            grid.addWidget(MyLineEdit(fileid,self),r,0)
            grid.addWidget(MyLabel(str(filech),self),r,1)
            grid.addWidget(QtGui.QLabel("  ->  ",self),r,2)
            combo1 = QtGui.QComboBox(self)
            combo2 = MyComboBox(sndFileList, self)
            combo1.addItem("-- select --")
            for i,k in enumerate(comboList):
                combo1.insertItem(i+1, os.path.basename(k))
            self.connect(combo1,QtCore.SIGNAL("activated(int)"),combo2.reset)
            grid.addWidget(combo1,r,3)
            grid.addWidget(combo2,r,4)

            if (fileid,filech) in assoc:
                sndfile, ch = assoc[fileid,filech]
                i = comboList.index(sndfile) + 1
                combo1.setCurrentIndex(i)
                combo2.reset(i)
                combo2.setCurrentIndex(ch+1)
                
            table.append([(fileid,filech), combo1, combo2])
            
        hbox = QtGui.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.setMargin(10)
        b1 = QtGui.QPushButton("OK", self)
        b2 = QtGui.QPushButton("Cancel", self)
        hbox.addWidget(b1)
        hbox.addWidget(b2)

        self.connect(b1,QtCore.SIGNAL("clicked()"),self._clicked_OK)
        self.connect(b2,QtCore.SIGNAL("clicked()"),self._clicked_Cancel)

        # fields
        self.grid = grid
        self.table = table
        self.comboSndfiles = comboList
        self.wave = wave
        
    def _clicked_OK(self):
        for k, combo1, combo2 in self.table:
            i = combo1.currentIndex()
            ch = combo2.currentIndex()
            if i > 0 and ch > 0:
                sndfile = self.comboSndfiles[i-1]
                self.wave.setAssociation(k[0],k[1],sndfile,ch-1)
            else:
                self.wave.unsetAssociation(k[0],k[1])
        self.done(self.Accepted)
    def _clicked_Cancel(self):
        self.done(self.Rejected)


