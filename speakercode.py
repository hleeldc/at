import string
import random

__all__ = ['SpeakerCode']

# make a color list

R = ["33","CC","FF"]
G = ["33","66","99","CC","FF"]
B = ["66","99","FF"]
COLORS = []
for r in range(3):
    for g in range(5):
        for b in range(3):
            COLORS.append("#%s%s%s" % (R[r],G[g],B[b]))
random.seed(90)
random.shuffle(COLORS)


class SpeakerCode(dict):
    def __init__(self):
        dict.__init__(self)
        self._color = {}
        self.default_color = {}
        self.default_code = {}
        self.n = 0
        self.garbageColor = []

    def __getitem__(self,k):
        if self.has_key(k):
            return dict.__getitem__(self,k)
        else:
            if self.garbageColor:
                new_code, new_color = self.garbageColor.pop()
                self[k] = self.default_code[k] = new_code
                self._color[k] = self.default_color[k] = new_color
                return new_code
            else:
                self._color[k] = self.default_color[k] = COLORS[self.n%45]
                n = self.n
                c = []
                while n >= 27:
                    c.append(n%27)
                    n = n / 27
                c.append(n)
                x = 1
                n = 0
                for i in range(len(c)):
                    n += c[i] * x
                    if c[i] == 0:
                        n += x * 1
                        c[i] = 1
                    x *= 27
                self.n = n + 1
                c.reverse()
                c = map(lambda x:chr(ord('A')+x-1), c)
                code = string.join(c,'')
                self[k] = self.default_code[k] = code
                return code

    def clear(self):
        dict.clear(self)
        self._color = {}
        self.default_color = {}
        self.default_code = {}
        self.n = 0
        
    def color(self, k):
        if not self.has_key(k):
            self.__getitem__(k)
        return self._color[k]

##     def set_color(self, k, c):
##         """
##         set color for spkr k to c
        
##         """
##         self.__getitem__(k)     # make sure that the new entry is created
##         old_code = self[k]
##         old_color = self._color[k]
##         if c == old_color: return
##         for spkr,color in self._color.items():
##             if color == c:
##                 del self._color[spkr]
##                 del self[spkr]
                
##         self.garbageColor.append((old_code, old_color))
##         self._color[k] = c
        
##     def color_reset(self, k):
##         if self.has_key(k):
##             self._color[k] = self.default_color[k]

##     def code_reset(self, k):
##         if self.has_key(k):
##             self[k] = self.default_code[k]
