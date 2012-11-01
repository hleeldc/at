
__all__ = ["partition"]

def combination1(L,n,S,R):
    if n == 0:
        R[tuple(S[:])] = 1
        return
    for a in range(len(L)):
        S.append(L[a])
        M = L[:a] + L[a+1:]
        combination1(M,n-1,S,R)
        S.pop()

def combination(L,n):
    R = {}
    combination1(L,n,[],R)
    R = R.keys()
    R.sort()
    return R

def num_partition1(n,S,R):
    if n == 0:
        R[tuple(S)] = 1
        return
    for m in range(1,n+1):
        S.append(m)
        num_partition1(n-m,S,R)
        S.pop()

def num_partition(n):
    R = {}
    num_partition1(n,[],R)
    R = R.keys()
    R.sort()
    return R

def partition1(P,L,S,R):
    if not L:
        R[tuple(S)] = 1
        return
    for i,p in enumerate(P):
        for C in combination(L,p):
            S.append(C)
            M = L[:]
            for c in C:
                M.remove(c)
            partition1(P[1:],M,S,R)
            S.pop()

def partition(L):
    R = {}
    for P in num_partition(len(L)):
        partition1(P,L,[],R)
    R = R.keys()
    R.sort()
    return R

