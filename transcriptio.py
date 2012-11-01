
#
# ChangeLogs:
# $Log: transcriptio.py,v $
# Revision 1.14  2008/12/08 18:15:23  haejoong
# typo fix: unkown -> unknown
#
# Revision 1.13  2008/11/19 18:03:06  haejoong
# fixed a problem in handling PREVIOUSPOST tag when loading NG sgm file
#
# Revision 1.12  2008/08/01 19:47:59  haejoong
# use "sgm_tag" instead of None for the speaker id of sgm tags
#
# Revision 1.11  2006/06/27 19:03:50  haejoong
# added newswire sgm support
#
# Revision 1.10  2006/04/12 14:55:24  haejoong
# fixes for error handling
#
# Revision 1.9  2006/02/05 03:31:28  haejoong
# added import/export newsgroup sgm functions
#
# Revision 1.8  2006/02/03 22:16:52  haejoong
# added importTxt
#
# Revision 1.7  2006/01/31 16:19:20  haejoong
# importTrs(): don't allow "\n" in transcription text (replace it with " ")
#
# Revision 1.6  2006/01/26 15:50:03  haejoong
# new conversion algorithm for transcriber file
#
# Revision 1.5  2006/01/19 17:54:23  haejoong
# added error handling for importTrs
#
# Revision 1.4  2005/11/19 15:56:07  haejoong
# - importTrs: section boundaries and types are recorded in the metadata
#
# Revision 1.3  2005/11/01 15:56:15  haejoong
# added importTyp (not perfect yet)
#
# Revision 1.2  2005/10/25 15:16:55  haejoong
# importWeblogSgm: should consider empty lines
#
# Revision 1.1.1.1  2005/10/24 20:41:01  haejoong
# initial imports
#
# Revision 1.1.1.1.2.1  2005/10/18 19:00:17  haejoong
# initialized the ChangeLogs
#
#

from tableio import TableIo
from xml.dom import minidom
from xml.parsers.expat import ExpatError
import os
import re
import codecs
import bisect
from error import *

__all__ = ['TranscriptIo']

version = "$Revision: 1.14 $".split()[1]

class TranscriptIo(TableIo):
    def importTrs(cls, filename):
        segId = 0
        secId = 0
        trnId = 0
        tab = cls()
        secBs = []
        secTs = []
        
        try:
            dom = minidom.parse(filename)
        except ExpatError, e:
            raise Error(ERR_TRANS_IMPORT, e)
            
        trans = dom.getElementsByTagName('Trans')[0]
        audioFile = trans.attributes['audio_filename'].value
        speakers = {None:None}
        for speaker in trans.getElementsByTagName('Speaker'):
            speakers[speaker.attributes['id'].value] = speaker
        for section in trans.getElementsByTagName('Section'):
            sectionType = section.attributes['type'].value
            sectionBeg = float(section.attributes['startTime'].value)
            sectionEnd = float(section.attributes['endTime'].value)
            secBs.append(sectionBeg)
            secTs.append(sectionType)
            tab.setMetadata
            #if sectionType == 'nontrans':
            #    secId += 1
            #    continue
            for turn in section.getElementsByTagName('Turn'):
                turnBeg = float(turn.attributes['startTime'].value)
                turnEnd = float(turn.attributes['endTime'].value)
                if turn.attributes.has_key('speaker'):
                    spkrIds = turn.attributes['speaker'].value.split()
                else:
                    spkrIds = [None]
                    print "WARNING: no speaker for the turn [%d,%d]" % (turnBeg,turnEnd)
                openSegments = []
                for c in turn.childNodes:
                    cls = c.__class__
                    if cls == minidom.Text:
                        if openSegments:
                            openSegments[-1]['transcript'] += c.data.strip().replace("\n"," ")
                    elif cls == minidom.Element:
                        tag = c.tagName
                        if tag == 'Sync':
                            t = float(c.attributes['time'].value)
                            for seg in openSegments:
                                seg['end'] = t
                            openSegments = []
                            who = c.nextSibling.nextSibling
                            if who and who.tagName=='Who':
                                continue
                            tab.insertRow(segId)
                            seg = tab[segId]
                            seg['file'] = audioFile
                            seg['channel'] = 0
                            seg['start'] = t
                            seg['section'] = secId
                            seg['turn'] = trnId
                            seg['segment'] = segId
                            seg['sectionType'] = sectionType
                            seg['transcript'] = ""
                            try:
                                speaker = speakers[spkrIds[0]]
                            except IndexError:
                                raise Error(ERR_TRANS_IMPORT,
                                            "turn speaker not specified "
                                            "around %f" % seg['start'])
                            except KeyError:
                                raise Error(ERR_TRANS_IMPORT,
                                            "not registered speaker %s "
                                            "around %f" % (spkrIds[0],seg['start']))
                            if speaker is not None:
                                if speaker.attributes.has_key('type'):
                                    seg['speakerType'] = speaker.attributes['type'].value
                                if speaker.attributes.has_key('name'):
                                    seg['speaker'] = speaker.attributes['name'].value
                                if speaker.attributes.has_key('dialect'):
                                    seg['speakerDialect'] = speaker.attributes['dialect'].value
                            segId += 1
                            openSegments.append(seg)
                        elif tag == 'Who':
                            tab.insertRow(segId)
                            seg = tab[segId]
                            seg['file'] = audioFile
                            seg['channel'] = 0
                            seg['start'] = t
                            seg['section'] = secId
                            seg['turn'] = trnId
                            seg['segment'] = segId
                            seg['sectionType'] = sectionType
                            seg['transcript'] = ""
                            turnspkri = int(c.attributes['nb'].value) - 1
                            try:
                                speaker = speakers[spkrIds[turnspkri]]
                            except IndexError:
                                raise Error(ERR_TRANS_IMPORT,
                                            "overlapping speaker #%d is not specified "
                                            "around %f" % (turnspkri+1,seg['start']))
                            except KeyError:
                                raise Error(ERR_TRANS_IMPORT,
                                            "not registered speaker %s "
                                            "around %f" % (spkrIds[turnspkri],seg['start']))
                            if speaker is not None:
                                if speaker.attributes.has_key('type'):
                                    seg['speakerType'] = speaker.attributes['type'].value
                                if speaker.attributes.has_key('name'):
                                    seg['speaker'] = speaker.attributes['name'].value
                                if speaker.attributes.has_key('dialect'):
                                    seg['speakerDialect'] = speaker.attributes['dialect'].value
                            segId += 1
                            openSegments.append(seg)
                        elif openSegments:
                            openSegments[-1]['transcript'] += " " + c.toxml() + " "
                        else:
                            raise "you shouldn't see this!!!"
                    else:
                        print "WARNING: don't know how to handle this:", cls
                for seg in openSegments:
                    seg['end'] = turnEnd
                openSegments = []
                trnId += 1
                
            secId += 1
        secBs.append(9999999.0)
        secTs.append(None)
        tab.setMetadata("sectionBoundaries",secBs)
        tab.setMetadata("sectionTypes",secTs)
        tab.resetUndoStack()
        return tab
    
    importTrs = classmethod(importTrs)

    def exportTrs(self, filename):
        try:
            self._exportTrs(filename)
        except IOError, e:
            raise Error(ERR_TRANS_EXPORT, str(e))
        
    def _exportTrs(self, filename):
        encf, decf, readf, writef = codecs.lookup('utf-8')

        f = writef(file(filename,"w"))

        # pass 1
        h = {}
        #section_ends = {None:None}
        turn_ends = {None:None}
        #overlaps = {}
        #overlapSeg1 = {}
        #overlapSeg2 = {}
        turnMembership = {}
        #prevsec = None
        prevtrn = None
        prevseg = None
        turnseg = self[0]
        t1 = t2 = -9999999.99   # previous segment's start/end time
        for row in self:
            s1 = row['start']   # current segment's start time
            s2 = row['end']     # current segment's end time
            name = row['speaker']
            typ = row['speakerType']
            dialect = row['speakerDialect']
            info = (name, typ, dialect)
            if name in h:
                if  h[name] != info:
                    raise Error(ERR_TRANS_EXPORT,
                                "inconsistent speaker information")
            else:
                h[name] = info

            if t1<s2 and s1<t2:
                if t1!=s1 or t2!=s2:
                    print t1,t2,s1,s2
                    raise Error(ERR_TRANS_EXPORT,
                                "error: can't handle overlapping turn")
                turn = (prevspkr,name)
                turnMembership[row] = turn
                turnMembership[prevseg] = turn
                turn_ends[prevseg] = s1
            else:
                turn = name
                turnMembership[row] = turn
            if turn != prevtrn:
                turn_ends[turnseg] = s1
                turnseg = row
            t1 = s1
            t2 = s2
            prevspkr = name
            prevseg = row
            prevtrn = turn
            
        #section_ends[prevsec] = t2
        turn_ends[turnseg] = t2

        speakers = h.keys()
        def sortf(a,b):
            if a is None:
                return 1
            elif b is None:
                return -1
            elif a.find('#') >= 0 and b.find('#') >= 0:
                a1,a2 = a.split('#')
                b1,b2 = b.split('#')
                return cmp(int(a2), int(b2))
            else:
                return cmp(a,b)

        speakers.sort(sortf)
        for i,name in enumerate(speakers):
            h[name] = (i+1,) + h[name]

        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Trans SYSTEM "trans-14.dtd">
<Trans scribe="tdf2trs" audio_filename="%s">
<Speakers>
""" % row['file'])

        speakerIds = {}
        for name in speakers:
            speakerIds[name] = "spk%d" % h[name][0]
            print >>f, '<Speaker id="spk%d" name="%s" type="%s" dialect="%s"/>' % h[name]
        print >>f, "</Speakers>"
        print >>f, "<Episode>"

        #prevsec = None
        prevtrn = None
        t1 = t2 = None
        secTs = self.getMetadata("sectionTypes", True)
        secBs = self.getMetadata("sectionBoundaries", True)
        secI = 0
        secE = secBs[secI+1]
        print >>f, '<Section type="%s" startTime="%f" endTime="%f">' % \
              (secTs[secI], secBs[secI], secE)
        for row in self:
            s1 = row['start']
            segment = row['segment']
            section = row['section']
            if secE <= s1:
                if secE >= 0.0:
                    if prevtrn:
                        print >>f, '</Turn>'
                    print >>f, '</Section>'
                #secType = row['sectionType']
                secI += 1
                secE = secBs[secI+1]
                print >>f, '<Section type="%s" startTime="%f" endTime="%f">' % \
                      (secTs[secI], secBs[secI], secE)
                #prevsec = section
                #prevtrn = None

            #turn = row['turn']
            turn = turnMembership[row]
            if turn != prevtrn:
                if prevtrn is not None:
                    print >>f, "</Turn>"
                if type(turn) == tuple:
                    try:
                        spkr1 = speakerIds[turn[0]]
                    except KeyError:
                        spkr1 = ''
                    try:
                        spkr2 = speakerIds[turn[1]]
                    except KeyError:
                        spkr2 = ''
                    print >>f, '<Turn speaker="%s %s" startTime="%f" endTime="%f">' % \
                          (spkr1, spkr2, s1, turn_ends[row])
                else:
                    try:
                        spkrId = speakerIds[turn]
                    except KeyError:
                        spkrId = ''
                    print >>f, '<Turn speaker="%s" startTime="%f" endTime="%f">' % \
                          (spkrId, s1, turn_ends[row])
                prevtrn = turn

            if type(turn) == tuple:
                if turn == prevtrn:
                    print >>f, '<Who nb="2"/>'
                else:
                    print >>f, '<Who nb="1"/>'
            else:
                print >>f, '<Sync time="%f"/>' % s1
            print >>f, re.sub("<","&lt;",row['transcript'])

        print >>f, '</Turn>'
        print >>f, '</Section>'
        print >>f, '</Episode>'
        print >>f, '</Trans>'


    def importWeblogSgm(cls, filename, encoding='utf-8'):
        encf, decf, reader, writer = codecs.lookup(encoding)

        fileid = os.path.basename(filename)
        data = cls()

        f = reader(file(filename))
        t = 0.0
        saved_spkr = "sgm_tag"
        for l in f:
            m = re.match(r"^\s*<POSTER>(.*)</POSTER>\s*$", l)
            if m:
                saved_spkr = m.group(1)

            if l.lstrip() and l.lstrip()[0] == '<':
                spkr = "sgm_tag"
            else:
                spkr = saved_spkr

            if l.strip()[:7] == '</POST>':
                saved_spkr = "sgm_tag"

            r = [fileid,0,t,t+100.0,spkr,'unknown','unknown',l.strip(),
                 0,0,0,None]
            data.insertRow(row=r)
            t += 100.0

        secBs = [0.0,9999999.99]
        secTs = [None,None]
        data.setMetadata("sectionBoundaries", secBs)
        data.setMetadata("sectionTypes", secTs)
        
        data.resetUndoStack()
        return data

    importWeblogSgm = classmethod(importWeblogSgm)

    def exportWeblogSgm(self, filename):
        encf, decf, reader, writer = codecs.lookup('utf-8')

        f = writer(file(filename,"w"))
        for row in self:
            print >>f, row['transcript']
        f.close()
            
    def importNewsgroupSgm(cls, filename, encoding='utf-8'):
        encf, decf, reader, writer = codecs.lookup(encoding)

        fileid = os.path.basename(filename)
        data = cls()

        f = reader(file(filename))
        t = 0.0
        saved_spkr = "sgm_tag"
        previouspost = False
        for l in f:
            m = re.match(r"^\s*<POSTER>(.*)</POSTER>\s*$", l)
            if m:
                saved_spkr = m.group(1)

            if not previouspost:
                if l.lstrip() and l.lstrip()[0] == '<':
                    m = re.match(r'^\s*<QUOTE\s+PREVIOUSPOST="\s*$', l)
                    if m:
                        spkr = "PREVIOUSPOST"
                        previouspost = True
                    else:
                        spkr = "sgm_tag"
                else:
                    spkr = saved_spkr

                if l.strip()[:7] == '</POST>':
                    saved_spkr = "sgm_tag"
                
            r = [fileid,0,t,t+100.0,spkr,'unknown','unknown',l.strip(),
                 0,0,0,None]
            data.insertRow(row=r)
            t += 100.0

            if previouspost and re.match(r'.*"/?>$', l.strip()[:3]):
                previouspost = False
            
        secBs = [0.0,9999999.99]
        secTs = [None,None]
        data.setMetadata("sectionBoundaries", secBs)
        data.setMetadata("sectionTypes", secTs)
        
        data.resetUndoStack()
        return data

    importNewsgroupSgm = classmethod(importNewsgroupSgm)
    exportNewsgroupSgm = exportWeblogSgm


    def importNewswireSgm(cls, filename, encoding='utf-8'):
        encf, decf, reader, writer = codecs.lookup(encoding)

        fileid = os.path.basename(filename)
        data = cls()

        f = reader(file(filename))
        t = 0.0
        spkr = "sgm_tag"
        textcount = 0
        for l in f:
            if l.strip() == '</TEXT>':
                spkr = "sgm_tag"

            if l.startswith("<"):
                r = [fileid,0,t,t+100.0,"sgm_tag",'unknown','unknown',l.strip(),
                     0,0,0,None]
            else:
                r = [fileid,0,t,t+100.0,spkr,'unknown','unknown',l.strip(),
                     0,0,0,None]

            if l.strip() == '<TEXT>':
                textcount += 1
                spkr = 'TEXT%d' % textcount

            data.insertRow(row=r)
            t += 100.0

        secBs = [0.0,9999999.99]
        secTs = [None,None]
        data.setMetadata("sectionBoundaries", secBs)
        data.setMetadata("sectionTypes", secTs)
        
        data.resetUndoStack()
        return data

    importNewswireSgm = classmethod(importNewswireSgm)
    exportNewswireSgm = exportWeblogSgm


    def importRT04Typ(cls, filename, encoding='utf-8'):
        _,_,reader,writer = codecs.lookup(encoding)
        f = reader(file(filename))
        data = cls()
        fileid = os.path.basename(filename)
        
        p_tag = re.compile(r"^<(sr|sf|st|sn|t|b|o|e)\s+([0-9]+\.[0-9]+)>\s*(.*)$")
        e_tag = re.compile(r"^\s*<<\s*(male|female|other)\s*,(?:\s*(non-native)\s*,)?\s*(\S+)\s*>>\s*$")

        l = f.readline()
        previousSegmentIsOpen = False
        lineNum = 1
        secNum = 0
        trnNum = 0
        segNum = 0
        secTyp = None
        while l:
            m = p_tag.match(l)
            if m is not None:
                tag, t, extra = m.groups()
                if tag == 'sf': tag = 'sr'
                t = float(t)

                if previousSegmentIsOpen == True:
                    data[-1]["end"] = t

                if tag in ('sr','st','t','b'):
                    l = f.readline().strip()
                    lineNum += 1
                    previousSegmentIsOpen = True
                else:
                    l = ""
                    if tag == 'o' or tag == 'sn':
                        previousSegmentIsOpen = True
                    else:
                        previousSegmentIsOpen = False

                if tag=='sr' or tag=='st' or tag=='sn':
                    secNum += 1
                    trnNum = 0
                    segNum = 0
                    secTyp = tag
                elif tag=='t':
                    trnNum += 1
                elif tag=='b':
                    segNum += 1
                
                if tag != 'e':
                    data.insertRow(row=[fileid,None,None,None,None,None,None,None,
                                        secNum,trnNum,segNum,secTyp])
                    seg = data[-1]
                    if extra:
                        m = e_tag.match(extra)
                        if m:
                            seg["speakerType"], seg["speakerDialect"], seg["speaker"] = m.groups()
                        else:
                            raise Error(ERR_TYP_IMPORT,
                                        "wrong speaker information in "
                                        "the transcript line %d" % lineNum)
                    elif len(data)>1 and tag == 'b':
                        seg2 = data[-2]
                        seg["speakerType"] = seg2["speakerType"]
                        seg["speakerDialect"] = seg2["speakerDialect"]
                        seg["speaker"] = seg2["speaker"]
                    seg["channel"] = 1
                    seg["start"] = t
                    seg["transcript"] = l

            l = f.readline()
            lineNum += 1
        data.resetUndoStack()
        return data

    importRT04Typ = classmethod(importRT04Typ)

    def exportTxt(self, filename):
        try:
            f = codecs.getwriter("utf-8")(file(filename,"w"))
        except IOError, e:
            raise Error(ERR_TXT_EXPORT, e.strerror)
        
        A = ord('A')
        base = ''
        cnt1 = 0
        cnt2 = -1
        h = {}
        for row in self:
            spkr = row['speaker']
            trans = row['transcript']
            start = "%.3f" % row['start']
            end = "%.3f" % row['end']
            if spkr in h:
                spkrid = h[spkr]
            else:
                spkrid = base + chr(A+cnt1)
                cnt1 += 1
                if cnt1 >= 24:
                    cnt2 += 1
                    base = chr(A+cnt2)
                    cnt1 = 0
                h[spkr] = spkrid
            print >>f, start, end, spkrid+":", trans
            
