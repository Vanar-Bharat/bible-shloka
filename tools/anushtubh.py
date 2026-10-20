#!/usr/bin/env python3
"""Anushtubh (shloka) metre validator for IAST text.

Rules (pathya form): each pada has 8 syllables; syllable 5 is laghu (light),
syllable 6 is guru (heavy); syllable 7 is guru in odd padas and laghu in even
padas. Variant (vipula) forms in odd padas are reported as warnings.
A syllable is guru if its vowel is long (aa ii uu RR e ai o au) or if it is
followed by anusvara/visarga or by two or more consonants. Final syllable of a
pada is free (anceps).
Usage: anushtubh.py FILE  (one pada per line; '|' or blank lines ignored;
lines starting with # are comments)
"""
import re, sys
LONG = {'ā','ī','ū','ṝ','e','o','ē','ō','ai','au','eu'}  # ē ō: long e/o in loanwords; eu: Greek diphthong
SHORT = {'a','i','u','ṛ','ḷ','ĕ','ŏ'}  # ĕ ŏ: short e/o in Hebrew/Greek loanwords
ASP = ['kh','gh','ch','jh','ṭh','ḍh','th','dh','ph','bh']
CONS = set('kgṅcjñṭḍṇtdnpbmyrlvśṣsh') | {'ħ','ʕ','ʔ'}  # ħ Hebrew het, ʕ ayin, ʔ aleph
METRE = {}  # loanword -> metrical spelling (register/loanwords.tsv column 'metre'), e.g. iēsū -> yēsū
try:
    import csv, os
    _f = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'register', 'loanwords.tsv')
    for _r in csv.reader(open(_f, encoding='utf8'), delimiter='\t'):
        if _r and not _r[0].startswith('#') and len(_r) > 6 and _r[6].strip():
            METRE[_r[0]] = _r[6].strip()
except OSError:
    pass
def tokens(p):
    p = p.lower().replace("'", '').replace('\u0301', '')  # acute = stress, no weight
    words = []
    for w in p.split():
        words.append('-'.join(METRE.get(part, part) for part in w.split('-')))
    p = '|'.join(words).replace('-', '')   # '|' marks a word boundary: no diphthong across it
    out, i = [], 0
    while i < len(p):
        if p[i] == '|': i += 1; continue
        two = p[i:i+2]
        if two in ('ai','au','eu'): out.append(('V',two)); i += 2; continue
        if two in ASP: out.append(('C',two)); i += 2; continue
        c = p[i]
        if c in LONG or c in SHORT: out.append(('V',c))
        elif c in 'ṃḥ': out.append(('M',c))
        elif c in CONS: out.append(('C',c))
        i += 1
    return out
def weights(p):
    t = tokens(p); w = []
    for k,(kind,v) in enumerate(t):
        if kind != 'V': continue
        j, cons, mark = k+1, 0, False
        while j < len(t) and t[j][0] != 'V':
            if t[j][0] == 'M': mark = True
            else: cons += 1
            j += 1
        heavy = v in LONG or mark or cons >= 2
        w.append('G' if heavy else 'L')
    return w
def check(padas):
    errs = []; warns = []
    for n,p in enumerate(padas, 1):
        w = weights(p); odd = n % 2 == 1
        tag = f'pada {n} "{p}" [{"".join(w)}]'
        if len(w) != 8: errs.append(f'{tag}: {len(w)} syllables, need 8'); continue
        if odd:
            if not (w[4]=='L' and w[5]=='G' and w[6]=='G'):
                warns.append(f'{tag}: odd pada not pathya (vipula?)')
        else:
            if not (w[4]=='L' and w[5]=='G' and w[6]=='L'):
                errs.append(f'{tag}: even pada needs L G L at 5-7')
        if w[1]=='L' and w[2]=='L': errs.append(f'{tag}: syllables 2-3 both light')
    if len(padas) % 4: warns.append(f'{len(padas)} padas: not a whole number of shlokas')
    return errs, warns
if __name__ == '__main__':
    lines = [l.strip() for l in open(sys.argv[1], encoding='utf8')]
    padas = [l for l in lines if l and not l.startswith('#') and l != '|']
    e, w = check(padas)
    for x in w: print('WARN', x)
    for x in e: print('FAIL', x)
    print(f'{len(padas)} padas, {len(e)} errors, {len(w)} warnings')
    sys.exit(1 if e else 0)
