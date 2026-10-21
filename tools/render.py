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
def deva(p):
    # Join a consonant-final Sanskrit word to the next Sanskrit word (शान्तिश्च), and an avagraha word to the one before (वोऽस्तु).
    # Kept (loan) words always stay separate.
    out = []
    for w in p.split():
        d = word(w); loan = any(part in LOAN for part in w.split('-'))
        if out and not loan and not out[-1][1] and (d.startswith('ऽ') or out[-1][0].endswith('्')):
            out[-1] = (out[-1][0] + d, False); continue
        out.append((d, loan))
    return ' '.join(x for x, _ in out)
out, buf, n, ref = [], [], 0, ''
header = []
for line in open(sys.argv[1], encoding='utf8'):
    line = line.strip()
    if line.startswith('# ') and re.match(r'# \S+ \d+:\d+(-\d+)?$', line): ref = line[2:]; continue
    if line.startswith('#'): header.append(line); continue
    if not line: continue
    buf.append((line, ref))
    if len(buf) % 4 == 0:
        n += 1
        a, b, c, d = [deva(x[0]) for x in buf[-4:]]
        nums = sorted({int(v) for x in buf[-4:] for v in re.findall(r':(\d+)(?:-(\d+))?', x[1])[0] if v})
        bk = re.match(r'(.*?\d+):', buf[-4][1]).group(1)
        rng = f'{bk}:{nums[0]}' + (f'–{nums[-1]}' if nums[-1] != nums[0] else '')
        out.append(f'{a} {b} ।\n{c} {d} ॥{n}॥   [{rng}]')
print('\n'.join(header + ['# Pronunciation key: ॑ marks the stressed syllable of a kept word; ऎ/ऒ are short e/o; nukta letters (ह़ ख़) mark Hebrew sounds. See README.']))
print()
print('\n\n'.join(out))
