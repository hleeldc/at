from table import TableModel
from transcriptio import TranscriptIo

__all__ = ['Transcript']

class Transcript(TableModel,TranscriptIo):
    HEADER = [('file',unicode), ('channel',int), ('start',float), ('end',float),
              ('speaker',unicode), ('speakerType',unicode), ('speakerDialect',unicode),
              ('transcript',unicode), ('section',int), ('turn',int), ('segment',int),
              ('sectionType',unicode), ('suType',unicode)]
    def __init__(self, *args):
        TableModel.__init__(self, self.HEADER[:])
