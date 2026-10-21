#!/usr/bin/env python3
"""Mūla gate: every check a draft must pass before review (PIPELINE §5 S4).

1. Metre: anuṣṭubh rules (tools/anushtubh.py).
2. Sanskrit letters only: IAST Sanskrit alphabet; no foreign letters (ĕ ŏ ē ō ħ ʕ ʔ ...).
   Ratified 21 Oct 2026: Sanskrit vyākaraṇa is sacrosanct; names are naturalised.
3. External sandhi lint: a word ending in a vowel followed by a word starting with a vowel
   an error where the hiatus can never survive Pāṇinian sandhi: a + a, and i/ī/u/ū/ṛ/ai/au + vowel
   (pragṛhya duals are the known exception; list them in register/pragrhya.txt).
   Hiatus after a/ā (from -aḥ, -āḥ or -e + vowel, 8.3.19 / 6.1.78) is legal but is reported as a
   warning so the reviewer confirms the underlying form.
4. Whole ślokas: pāda count divisible by 4.
5. Fillers: particles listed in register/fillers.tsv only (warning if a filler is not logged in the apparatus).
Exit 1 on any error. Usage: check_mula.py FILE [FILE...]
"""
import sys as _s; _s.stdout.reconfigure(encoding='utf-8')  # Windows consoles default to cp1252
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anushtubh as A
SANSKRIT = set("aāiīuūṛṝḷeoṃḥkgṅcjñṭḍṇtdnpbmyrlvśṣsh '-")
VOW_END = re.compile(r'(ai|au|[aāiīuūṛṝeo])$')
VOW_START = re.compile(r'^(ai|au|[aāiīuūṛṝeo])')

PR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'register', 'pragrhya.txt')
PRAGRHYA = set(open(PR, encoding='utf8').read().split()) if os.path.exists(PR) else set()

def padas(path):
    return [l.strip() for l in open(path, encoding='utf8') if l.strip() and not l.startswith('#') and l.strip() != '|']

def check(path):
    errs, warns = [], []
    ps = padas(path)
    e, w = A.check(ps); errs += e; warns += w
    for n, p in enumerate(ps, 1):
        bad = sorted({c for c in p.lower() if c not in SANSKRIT})
        if bad: errs.append(f'pāda {n} "{p}": non-Sanskrit letters {"".join(bad)}')
        raw = p.split()
        for a, b in zip(raw, raw[1:]):   # within a pāda: final m before a consonant is anusvāra (8.3.23)
            if a.endswith('m') and b[0] not in "aāiīuūṛṝeo'":
                errs.append(f'pāda {n}: "{a} {b}" final m before consonant must be ṃ')
            if a.endswith('aḥ') and len(a) > 2 and b[0] in 'gjḍdbnmyrlvh':   # -aḥ before voiced consonant -> -o (6.1.114)
                errs.append(f'pāda {n}: "{a} {b}" -aḥ before voiced consonant must be -o')
        for w in raw:   # Sanskrit has no vowel hiatus inside a word (e.g. *pneuma): only ai/au digraphs
            v = re.sub(r'ai|au', 'A', w.replace("'", ''))
            if re.search(r'[aāiīuūṛṝeoA][aāiīuūṛṝeoA]', v):
                errs.append(f'pāda {n}: "{w}" vowel hiatus inside a word')
        words = p.replace("'", ' ').split()
        for a, b in zip(words, words[1:]):
            ea, sb = VOW_END.search(a), VOW_START.match(b)
            if not (ea and sb): continue
            x, y = ea.group(1), sb.group(1)
            if x == 'a' and y == 'a':   # never survives sandhi (a+a -> ā; -aḥ/-e + a -> -o/-e ')
                errs.append(f'pāda {n}: "{a} {b}" needs sandhi (a + a)')
            elif b in PRAGRHYA or a in PRAGRHYA:
                pass
            elif x in ('i', 'ī', 'u', 'ū', 'ṛ', 'ṝ', 'ai', 'au'):
                errs.append(f'pāda {n}: "{a} {b}" needs sandhi ({x} + vowel)')
            elif x in ('a', 'ā'):
                warns.append(f'pāda {n}: "{a} {b}" hiatus; valid only after visarga loss or -e/-o sandhi')
    if len(ps) % 4: errs.append(f'{len(ps)} pādas: not whole ślokas')
    return errs, warns

if __name__ == '__main__':
    bad = 0
    for f in sys.argv[1:]:
        if '.deva.' in f: continue
        head = open(f, encoding='utf8').read(400)
        legacy = 'status: refit-pending' in head
        e, w = check(f)
        if legacy:   # pilot drafts made before the naturalisation ruling: metre only
            e = A.check(padas(f))[0]
        for x in w: print('WARN', f, x)
        for x in e: print('FAIL', f, x)
        print(f'{f}: {len(e)} errors, {len(w)} warnings' + (' (legacy: refit pending)' if legacy else ''))
        bad += bool(e)
    sys.exit(1 if bad else 0)
