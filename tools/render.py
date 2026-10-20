#!/usr/bin/env python3
"""Render an IAST mula file to Devanagari shlokas (two padas per line, danda marks).
Loanwords (register/loanwords.tsv) use fixed spellings with nukta and stress sign (U+0951)."""
import sys, re, csv
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
LOAN = {}
for row in csv.reader(open('register/loanwords.tsv', encoding='utf8'), delimiter='\t'):
    if row and not row[0].startswith('#'): LOAN[row[0]] = row[1]
def word(w):
    return '-'.join(LOAN.get(part) or transliterate(part, sanscript.IAST, sanscript.DEVANAGARI) for part in w.split('-'))
def deva(p): return ' '.join(word(w) for w in p.split())
out, buf, n, ref = [], [], 0, ''
for line in open(sys.argv[1], encoding='utf8'):
    line = line.strip()
    if line.startswith('# ') and ':' in line and '|' not in line: ref = line[2:]; continue
    if not line or line.startswith('#'): continue
    buf.append((line, ref))
    if len(buf) % 4 == 0:
        n += 1
        a, b, c, d = [deva(x[0]) for x in buf[-4:]]
        refs = sorted({x[1] for x in buf[-4:]}, key=lambda r: [int(t) for t in re.findall(r'\d+', r)])
        out.append(f'{a} {b} ।\n{c} {d} ॥{n}॥   [{", ".join(refs)}]')
print('\n\n'.join(out))
