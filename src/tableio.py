
#
# ChangeLogs:
# $Log: tableio.py,v $
# Revision 1.12  2008/03/26 18:04:34  haejoong
# bug fix: importTdf() incorrectly considers an empty line EOF
#
# Revision 1.11  2008/02/07 23:10:01  haejoong
# raise an error if a record lacks some fields
#
# Revision 1.10  2008/01/28 21:08:49  haejoong
# better error handling in file opening (importTDF)
#
# Revision 1.9  2006/06/27 19:03:28  haejoong
# tdf reader now handles different formats of newline characters
#
# Revision 1.8  2006/04/12 14:55:24  haejoong
# fixes for error handling
#
# Revision 1.7  2006/01/26 15:46:46  haejoong
# *** empty log message ***
#
# Revision 1.6  2006/01/23 16:32:29  haejoong
# improved exception handling
#
# Revision 1.5  2006/01/19 17:53:17  haejoong
# added some error handling for importTdf
#
# Revision 1.4  2005/12/15 19:08:40  haejoong
# added missing "
#
# Revision 1.3  2005/12/15 19:05:55  haejoong
# added error handling for TableIo.importTdf
#
#

import codecs
import re
from error import *

__all__ = ['TableIo']

version = "$Revision: 1.12 $"

class TableIo:
    def printTable(self):
        size = [len(str(x)) for x,t in self.header]
        for row in self.table:
            for i,c in enumerate(row):
                if type(c)==str or type(c)==unicode:
                    n = len(c)
                else:
                    n = len(str(c))
                if n > size[i]:
                    size[i] = n

        def printRow(row,bar=True):
            s = ""
            for i,c in enumerate(row):
                if type(c) == int or type(c) == float:
                    s += "%%%ds|" % size[i] % str(c)
                else:
                    s += "%%-%ds|" % size[i] % c
            print s[:-1] 

        printRow([s for s,t in self.header])
        for row in self.table:
            printRow(row)
            
    def importList(cls, L):
        data = cls(L[0])
        for i,row in enumerate(L[1:]):
            data.insertRow(i,row)
        data.resetUndoStack()
        return data

    importList = classmethod(importList)

    def exportTdf(self, filename):
        try:
            _,_,_,writer = codecs.lookup('utf-8')
            f = writer(file(filename,'w'))
            f.write("\t".join([a[0]+';'+a[1].__name__
                               for a in self.header]) + "\n")
            for item in self.metadata.items():
                f.write(";;MM %s\t%s\n" % item)
            for row in self.table:
                for c in row[:-1]:
                    if c is None:
                        f.write("\t")
                    else:
                        t = type(c)
                        if t==str or t==unicode:
                            f.write(c+"\t")
                        else:
                            f.write(str(c)+"\t")
                if row[-1] is None:
                    f.write("\n")
                else:
                    t = type(row[-1])
                    if t==str or t==unicode:
                        f.write(row[-1]+"\n")
                    else:
                        f.write(str(row[-1])+"\n")
        except IOError, e:
            raise Error(ERR_TDF_EXPORT, str(e))

    def importTdf(cls, filename, strict=True):
        _,_,reader,_ = codecs.lookup('utf-8')
        try:
            f = reader(file(filename))
        except IOError, e:
            raise Error(ERR_TDF_IMPORT, e)
        def newline():
            try:
                x = f.readline()
                if x == '':
                    return None
                else:
                    return x.rstrip("\r\n")
            except Exception, e:
                raise Error(ERR_TDF_IMPORT, e)
        head = []
        for h in newline().split("\t"):
            try:
                a,b = h.split(';')
            except ValueError:
                raise Error(ERR_TDF_IMPORT, "invalid header")
            head.append((a,eval(b)))
        tab = cls(head)
        l = newline()
        lno = 2
        while l is not None:
            if l[:2] != ';;': break
            if l[2:4] == 'MM':
                nam,val = re.split("\t+",l[4:].strip())
                tab.metadata[nam] = val
            l = newline()
            lno += 1
        while l is not None:
            if l[:2] != ';;':
                cells = l.rstrip("\n").split("\t")
                length_cmp = cmp(len(cells), len(head))
                if length_cmp == 1:
                    if strict:
                        msg = "record has too many fields"
                        raise Error(ERR_TDF_IMPORT,
                                    "[line %d] %s" % (lno, msg))
                    else:
                        del cells[len(head):]
                elif length_cmp == -1:
                    if strict:
                        msg = "record is missing some fields"
                        raise Error(ERR_TDF_IMPORT,
                                    "[line %d] %s" % (lno, msg))
                    else:
                        for i in range(len(cells), len(head)):
                            cell_type = head[i][1]
                            cells.append(cell_type()) 
                row = []
                for i, cell in enumerate(cells):
                    cell_type = head[i][1]
                    try:
                        row.append(cell_type(cell))
                    except ValueError, e:
                        raise Error(ERR_TDF_IMPORT,
                                    "[%d:%d] %s" % (lno,i,str(e)))
                tab.insertRow(None,row)
            l = newline()
            lno += 1
        tab.resetUndoStack()
        return tab

    importTdf = classmethod(importTdf)
