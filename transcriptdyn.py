import tableproxy
from transcript import Transcript

__all__ = ['Transcript']

Transcript = tableproxy.getProxy(Transcript)
        
if __name__ == "__main__":
    L = [[(None,None)]*10,
         ['sw',0,1.23,2.01,'A','male','native','how are you',1,1,1,'report'],
         ['sw',0,2.01,2.53,'B','female','native',"I'm fine",1,1,2,'report']]
    trans = Transcript.importList(L)
    trans.printTable()
