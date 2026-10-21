#!/usr/bin/env python3
"""Devanagari for kept Greek words written in loanword IAST (ĕ ŏ short, ē ō long), with U+0951 on the stressed syllable.
Usage as module: deva(iast, stress_syllable_1based)."""
V = {'a':('अ',''),'ā':('आ','ा'),'i':('इ','ि'),'ī':('ई','ी'),'u':('उ','ु'),'ū':('ऊ','ू'),
     'ĕ':('ऎ','ॆ'),'ē':('ए','े'),'ŏ':('ऒ','ॊ'),'ō':('ओ','ो'),'e':('ए','े'),'o':('ओ','ो'),'ai':('ऐ','ै'),'au':('औ','ौ')}
C = {'kh':'ख','gh':'घ','th':'थ','dh':'ध','ph':'फ','bh':'भ','k':'क','g':'ग','c':'च','j':'ज','t':'त','d':'द',
     'n':'न','p':'प','b':'ब','m':'म','y':'य','r':'र','l':'ल','v':'व','s':'स','h':'ह','ś':'श','ṣ':'ष','z':'ज़'}
def parse(w):
    out, i = [], 0
    while i < len(w):
        two = w[i:i+2]
        if two in ('ai','au'): out.append(('V',two)); i += 2; continue
        if two in C and len(two) == 2: out.append(('C',two)); i += 2; continue
        ch = w[i]
        out.append(('V',ch) if ch in V else ('C',ch)); i += 1
    return out
def deva(w, stress):
    t = parse(w); s = ''; syl = 0; prev_c = False
    for kind, x in t:
        if kind == 'C':
            if prev_c: s += '्'
            s += C[x]; prev_c = True
        else:
            syl += 1
            s += V[x][1] if prev_c else V[x][0]
            if syl == stress: s += '॑'
            prev_c = False
    if prev_c: s += '्'
    return s
if __name__ == '__main__':
    import sys; print(deva(sys.argv[1], int(sys.argv[2])))
