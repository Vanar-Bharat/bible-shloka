#!/usr/bin/env python3
"""Render an IAST mula file to Devanagari shlokas (two padas per line, danda marks).
Loanwords (register/loanwords.tsv) use fixed spellings with nukta and stress sign (U+0951)."""
import sys as _s; _s.stdout.reconfigure(encoding='utf-8')  # Windows consoles default to cp1252
import sys, re, csv
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
LOAN = {}
for row in csv.reader(open('register/loanwords.tsv', encoding='utf8'), delimiter='\t'):
    if row and not row[0].startswith('#'): LOAN[row[0]] = row[1]
def word(w):
    return '-'.join(LOAN.get(part) or transliterate(part, sanscript.IAST, sanscript.DEVANAGARI) for part in w.split('-'))
def deva(p):
    # Sandhi joins at the IAST level: a consonant-final word fuses with the next word (शान्तिश्च,
    # थेयादस्मत्), and an avagraha word ('smi) fuses with the one before (कृतज्ञोऽस्मि).
    # Legacy loan words (refit-pending pilots) stay separate.
    groups = []
    for w in p.split():
        loan = any(part in LOAN for part in w.split('-'))
        prev = groups[-1] if groups else None
        if prev and not loan and not prev[1] and (w.startswith("'") or (prev[0][-1] not in 'aāiīuūṛṝeoḥṃ' )):
            prev[0] += w; continue
        groups.append([w, loan])
    return ' '.join(word(g) for g, _ in groups)
out, buf, n, ref = [], [], 0, ''
header = []
for line in open(sys.argv[1], encoding='utf8'):
    line = line.strip()
    if line.startswith('# ') and re.match(r'# \S+ \d+:\d+(-\d+)?$', line): ref = line[2:]; continue
    if line.startswith('#'): header.append(line); continue
    if not line: continue
    buf.append((line, ref))
    m = re.match(r'(.*?:)(\d+)-(\d+)$', ref)   # a pāda straddling two verses: later pādas belong to the second
    if m: ref = m.group(1) + m.group(3)
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
