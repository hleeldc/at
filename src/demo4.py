""" Demonstrate how to build a transcription tool using
Transcript, TranscriptEdit and TranscriptWaveform.
"""

from qt import *
from at import *
import os
import codecs
encf, decf, reader, writer = codecs.lookup('utf-8')

class XTrans(QMainWindow):
    def __init__(self, reverse=False):
        QMainWindow.__init__(self)

        # data model
        self.data = None
        
        # central widget
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        self.trans = TranscriptEditWithSideBar(splitter, reverse)
        self.tred = self.trans.getTranscriptEdit()
        self.wave = TranscriptWaveform(splitter)
        self.setCentralWidget(splitter)

        # filename for saving purpose
        self.filename = None
        self.fileFormat = None
        self.formatName = {".tdf":"LDC .tdf transcript",
                           ".trs":"Transcriber transcript",
                           ".wl.sgm":"LDC Weblog SGML file"}

        self.audioFiles = []
        
        # menu
        menuBar = self.menuBar()
        menu_File = QPopupMenu(self)
        menu_File.insertItem("&New", self.menu_File_New)
        menu_File.insertItem("&Open", self.menu_File_Open)
        menu_File.insertItem("&Save", self.menu_File_Save)
        menu_File.insertItem("Sa&ve As", self.menu_File_SaveAs)
        menu_File.insertSeparator()
        menu_File.insertItem("Open &audio file", self.menu_File_OpenAudio)
        menu_File.insertItem("&Close audio file", self.menu_File_CloseAudio)
        menu_File.insertSeparator()
        menu_File_Import = QPopupMenu(self)
        menu_File.insertItem("&Import", menu_File_Import)
        menu_File_Import.insertItem("&Transcriber", self.menu_File_Import_Transcriber)
        menu_File_Import.insertItem("SGML: We&blog", self.menu_File_Import_WeblogSgm)
        menu_File_Export = QPopupMenu(self)
        menu_File.insertItem("&Export", menu_File_Export)
        menu_File_Export.insertItem("&Transcriber", self.menu_File_Export_Transcriber)
        menu_File_Export.insertItem("SGML: We&blog", self.menu_File_Export_WeblogSgm)
        menu_File.insertSeparator()
        menu_File.insertItem("E&xit", self.menu_File_Exit)
        menu_Edit = QPopupMenu(self)
        menu_Edit.insertItem("&Associate transcript to audio", self.menu_Edit_Assoc)
        menu_View = QPopupMenu(self)
        menu_View.insertItem("Change &font", self.menu_View_ChangeFont)
        menu_View_BySpeaker = QPopupMenu(self)
        menu_View.insertItem("View by speaker", menu_View_BySpeaker)
        menuBar.insertItem("&File", menu_File)
        menuBar.insertItem("&Edit", menu_Edit)
        menuBar.insertItem("&View", menu_View)
        self.menu_View_BySpeaker = menu_View_BySpeaker
        self.connect(menu_View_BySpeaker, SIGNAL("activated(int)"),
                     self.updateViewBySpeakerMenuItemId)
        self.viewBySpeakerMenu2spkr = {}

        # key bindings
        self.accel = QAccel(self)
        aid = self.accel.insertItem(QKeySequence("Ctrl+Return"))
        self.accel.connectItem(aid, self.splitSegment)
        aid = self.accel.insertItem(QKeySequence("Ctrl+J"))
        self.accel.connectItem(aid, self.joinSegments)
        aid = self.accel.insertItem(QKeySequence("Ctrl+Delete"))
        self.accel.connectItem(aid, self.deleteSegment)

        aid = self.accel.insertItem(QKeySequence("Alt+A"))
        self.accel.connectItem(aid, self.zoomIn)
        aid = self.accel.insertItem(QKeySequence("Alt+Z"))
        self.accel.connectItem(aid, self.zoomOut)
        
    def save(self, filename, format):
        if format == ".tdf":
            self.data.exportTdf(filename)
        elif format == ".trs":
            self.data.exportTrs(filename)
        elif format == ".wl.sgm":
            self.data.exportWeblogSgm(filename)
        else:
            QMessageBox.critical(
                self, "Save Error",
                "Can't handle file format %s.\n"
                "Saving aborted." % format,
                "OK")
            return
        self.filename = filename
        self.fileFormat = format
        self.setCaption("XTrans: "+os.path.basename(filename))
        
    def saveAs(self, filenameHint, format, formatName):
        filename = QFileDialog.getSaveFileName(
            filenameHint,
            "%s (*%s);; All (*.*)" % (formatName,format),
            self).ascii()
        if filename:
            if os.path.exists(filename):
                if os.path.isdir(filename):
                    QMessageBox.critical(
                        self, "Save Error",
                        "'%s' is a directory" % filename,
                        "OK")
                    return
                else:
                    res = QMessageBox.warning(
                        self, "Warning",
                        "'%s' will be overwritten" % filename,
                        "OK", "Cancel")
                    if res == 1:
                        return
            self.save(filename, format)

    
    def menu_File_New(self):
        self.data = Transcript()
        self.trans.setData(self.data)
        self.wave.setData(self.data)

        # filename for saving purpose
        self.filename = None
        self.fileFormat = ".tdf"
        
    def menu_File_Open(self, filename=None):
        if filename is None or type(filename)==int:
            filename = QFileDialog.getOpenFileName(
                "",
                "LDC TDF format (*.tdf);;"
                "All (*.*)",
                self
                ).ascii()
            if filename is None: return
            if not os.path.exists(filename):
                QMessageBox.critical(
                    self, "Open Error",
                    "'%s' doesn't exist" % filename,
                    "OK")
                return
            if os.path.isdir(filename):
                QMessageBox.critical(
                    self, "Open Error",
                    "'%s' is a directory" % filename,
                    "OK")
                return
        self.data = Transcript.importTdf(filename)
        self.data.sort('start')
        self.trans.setData(self.data)
        self.wave.setData(self.data)

        # filename for saving purpose
        self.filename = filename
        self.fileFormat = ".tdf"

        self.buildViewBySpeakerMenu()
        self.setCaption("XTrans: "+os.path.basename(filename))

    def menu_File_OpenAudio(self):
        filename = QFileDialog.getOpenFileName(
            "",
            "Audio files (*.wav *.sph);;"
            "All (*.*)",
            self
            ).ascii()
        if filename is None: return
        if not os.path.exists(filename):
            QMessageBox.critical(
                self, "Open Error",
                "'%s' doesn't exist" % filename,
                "OK")
            return
        if os.path.isdir(filename):
            QMessageBox.critical(
                self, "Open Error",
                "'%s' is a directory" % filename,
                "OK")
            return
        sndfile = self.wave.addSndFile(filename)
        for ch in range(0,sndfile.getChannels()):
            self.wave.placeWaveform(filename, ch, self.wave.numWaveforms())
            #self.wave.getWaveform(filename, ch).setFixedHeight(50)

    def menu_File_Save(self):
        if self.data is None: return
        if self.filename is None:
            self.saveAs("", ".tdf", self.formatName[".tdf"])
        elif self.fileFormat != ".tdf":
            self.saveAs(self.filename+".tdf", ".tdf", self.formatName[".tdf"])
        else:
            self.save(self.filename, ".tdf")

    def menu_File_SaveAs(self):
        if self.data is None: return
        if self.filename is None:
            self.saveAs("", ".tdf", self.formatName[".tdf"])
        elif self.fileFormat != ".tdf":
            self.saveAs(self.filename+".tdf", ".tdf", self.formatName[".tdf"])
        else:
            self.saveAs(self.filename, ".tdf", self.formatName[".tdf"])
                
    def menu_File_OpenAudio(self):
        filename = QFileDialog.getOpenFileName(
            "",
            "Audio files (*.wav *.sph);;"
            "All (*.*)",
            self
            ).ascii()
        if filename is None: return
        sndfile = self.wave.addSndFile(filename)
        if sndfile:
            self.audioFiles.append(filename)
            for ch in range(0,sndfile.getChannels()):
                self.wave.placeWaveform(filename, ch, self.wave.numWaveforms())

    def menu_File_CloseAudio(self):
        desc = "Please choose files to close in the list box below,\n" \
               "and press the OK button."
        d = ListDialog(self.audioFiles, description=desc,
                       caption="Close Audio File", parent=self)
        d.exec_loop()
        for f in d.getSelectedItems():
            self.wave.removeSndFile(f)
            self.audioFiles.remove(f)
    
    def menu_File_Import_Transcriber(self, filename=None):
        if filename is None or type(filename)==int:
            filename = QFileDialog.getOpenFileName(
                "",
                "%s (*.trs);; All (*.*)" % self.formatName[".trs"],
                self
                ).ascii()
            if filename is None: return
            if not os.path.exists(filename):
                QMessageBox.critical(
                    self, "Open Error",
                    "'%s' doesn't exist" % filename,
                    "OK")
                return
            if os.path.isdir(filename):
                QMessageBox.critical(
                    self, "Open Error",
                    "'%s' is a directory" % filename,
                    "OK")
                return
        self.data = Transcript.importTrs(filename)
        self.data.sort('start')
        self.trans.setData(self.data)
        self.wave.setData(self.data)

        # filename for saving purpose
        self.filename = filename
        self.fileFormat = ".trs"

        self.buildViewBySpeakerMenu()
        self.setCaption("XTrans: "+os.path.basename(filename))

    def menu_File_Import_WeblogSgm(self, filename=None):
        if filename is None or type(filename)==int:
            filename = QFileDialog.getOpenFileName(
                "",
                "%s (*.sgm);; All (*.*)" % self.formatName[".wl.sgm"],
                self
                ).ascii()
            if filename is None: return
            if not os.path.exists(filename):
                QMessageBox.critical(
                    self, "Open Error",
                    "'%s' doesn't exist" % filename,
                    "OK")
                return
            if os.path.isdir(filename):
                QMessageBox.critical(
                    self, "Open Error",
                    "'%s' is a directory" % filename,
                    "OK")
                return
        self.data = Transcript.importWeblogSgm(filename)
        self.data.sort('start')
        self.trans.setData(self.data)
        self.wave.setData(self.data)

        # filename for saving purpose
        self.filename = filename
        self.fileFormat = ".wl.sgm"

        self.buildViewBySpeakerMenu()
        self.setCaption("XTrans: "+os.path.basename(filename))

    def menu_File_Export_Transcriber(self):
        if self.data is None: return
        if self.filename is None:
            self.saveAs("", ".trs", self.formatName[".trs"])
        else:
            self.saveAs(self.filename, ".trs", self.formatName[".trs"])
    
    def menu_File_Export_WeblogSgm(self):
        if self.data is None: return
        if self.filename is None:
            self.saveAs("", ".wl.sgm", self.formatName[".wl.sgm"])
        else:
            self.saveAs(self.filename, ".wl.sgm", self.formatName[".wl.sgm"])
    
    def menu_File_Exit(self):
        QApplication.exit(0)
        
    def menu_Edit_Assoc(self):
        data = self.trans.textedit.getData()
        if data is not None:
            d = TransAudioAssocDialog(data, self.wave)
            d.exec_loop()

    def menu_View_ChangeFont(self):
        self.trans.setFont(QFontDialog.getFont(self.tred.font(),self)[0])
    
    def updateViewBySpeakerMenuItemId(self, i):
        if i not in self.viewBySpeakerMenu2spkr:
            self.trans.setFilter(lambda x:True)
            self.wave.setFilter(lambda x:True)
        else:
            spkr = self.viewBySpeakerMenu2spkr[i]
            self.trans.setFilter(lambda x:x['speaker']==spkr)
            self.wave.setFilter(lambda x:x['speaker']==spkr)
        
    def buildViewBySpeakerMenu(self):
        self.menu_View_BySpeaker.clear()
        self.viewBySpeakerMenu2spkr = {}
        h = {}
        for row in self.data:
            h[row['speaker']] = 1
        spkrs = h.keys()
        spkrs.sort()
        self.menu_View_BySpeaker.insertItem("-- all --")
        for spkr in spkrs:
            if spkr is None:
                s = "None"
            elif spkr == "":
                s = " "
            else:
                s = spkr
            px = QPixmap(10,10)
            px.fill(QColor(self.trans.getSpeakerColor(spkr)))
            p = QPainter(px)
            p.drawRect(0,0,10,10)
            p.end()
            i = self.menu_View_BySpeaker.insertItem(QIconSet(px),s)
            self.viewBySpeakerMenu2spkr[i] = spkr
    
    def splitSegment(self):
        if self.data is None: return
        charIdx = self.tred.getCursorPosition()[1]
        segIdx = self.data.getSelection()
        seg = self.data[segIdx]
        lst = seg.toList()

        i = seg.getColumnIndex('transcript')
        trans = seg[i]
        seg[i] = trans[:charIdx]
        lst[i] = trans[charIdx:]

        i = seg.getColumnIndex('start')
        j = seg.getColumnIndex('end')
        t0 = seg[i]
        t1 = seg[j]
        tt = (t0 + t1) / 2.0
        seg[j] = tt
        lst[i] = tt

        if segIdx+1 >= len(self.data):
            segIdx2 = segIdx + 1
        else:
            for segIdx2 in range(segIdx+1,len(self.data)):
                if tt < self.data[segIdx2]['start']:
                    break
            else:
                segIdx2 += 1
        self.data.insertRow(segIdx2,lst)

    def joinSegments(self):
        if self.data is None: return
        segIdx = self.data.getSelection()
        if segIdx >= len(self.data): return
        para, charIdx = self.tred.getCursorPosition()

        seg1 = self.data[segIdx]
        segIdx2 = None
        seg2 = None
        fileid = seg1['file']
        channel = seg1['channel']
        speaker = seg1['speaker']
        for para in range(para+1,self.tred.paragraphs()):
            segIdx2 = self.tred.getSegmentIndex(para)
            seg2 = self.data[segIdx2]
            if fileid == seg2['file'] and \
               channel == seg2['channel'] and \
               speaker == seg2['speaker']:
                break
        else:
            QMessageBox.warning(
                self, "Join Error",
                "Can't find the next segment on the current\n"
                "\"virtual channel\"  Join aborted",
                "OK")
            return

        self.data.takeRow(segIdx2)
        seg1['transcript'] += " " + seg2['transcript']
        seg1['end'] = seg2['end']

        self.tred.setCursorPosition(segIdx,charIdx)

    def deleteSegment(self):
        if self.data is None: return
        segIdx = self.data.getSelection()
        if segIdx >= len(self.data): return
        self.data.takeRow(segIdx)

    def zoomIn(self):
        self.wave.zoomAtCenter(2.0)
        #self.wave.zoomInAtCursor()

    def zoomOut(self):
        self.wave.zoomAtCenter(0.5)
        #self.wave.zoomOutAtCursor()
        
if __name__ == "__main__":
    import sys
    from optparse import OptionParser
    app = QApplication([])

    parser = OptionParser()
    parser.add_option("-i", "--file", dest="filename",
                      help="open FILE at start", metavar="FILE")
    parser.add_option("-f", "--format", dest="format", default='.tdf',
                      help="input file in of FORMAT format", metavar="FORMAT")
    parser.add_option("-r", "--right-to-left", dest="bidi",
                      action="store_true", default=False,
                      help="text goes from right to left")
    (options, args) = parser.parse_args()
    
    if options.bidi or \
       (len(args)>0 and args[0] == "arabic"):
        bidi = True
    else:
        bidi = False

    w = XTrans(reverse=bidi)
    w.setCaption("XTrans")
    app.setMainWidget(w)
    w.show()

    if options.filename:
        if options.format == '.tdf':
            w.menu_File_Open(options.filename)
        elif options.format == '.trs':
            w.menu_File_Import_Transcriber(options.filename)
        elif options.format == '.wl.sgm':
            w.menu_File_Import_WeblogSgm(options.filename)
            
    app.exec_loop()
