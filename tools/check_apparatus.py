#!/usr/bin/env python3
"""Coverage and filler gate (PIPELINE §5 S4, R7).

Usage: check_apparatus.py APPARATUS.yaml SOURCE.tsv
Coverage: every content lemma of every source verse is a key in that verse's map (keys may be a
lemma or a quoted phrase containing it) or in omitted:. Fillers: every logged filler is on the allow-list.
"""
import sys as _s; _s.stdout.reconfigure(encoding='utf-8')  # Windows consoles default to cp1252
import sys, os, csv, yaml, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from budget import content
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FILL = {l.strip() for l in open(os.path.join(ROOT, 'register', 'fillers.tsv'), encoding='utf8') if l.strip() and not l.startswith('#')}

def coverage(a, rows):
    verses = collections.OrderedDict()
    for r in rows:
        if content(r): verses.setdefault(r['ref'], []).append(r['lemma'])
    errs = []
    for ref, lemmas in verses.items():
        e = a.get(ref)
        if not e: errs.append(f'{ref}: no apparatus entry'); continue
        keys = ' '.join(str(k) for k in list((e.get('map') or {}).keys()) + list((e.get('omitted') or {}).keys()))
        for lem in lemmas:
            if lem not in keys: errs.append(f'{ref}: {lem} neither mapped nor omitted')
        for f in e.get('fillers') or []:
            if f not in FILL: errs.append(f'{ref}: filler "{f}" not on the allow-list')
    return errs

def main(app, src):
    a = yaml.safe_load(open(app, encoding='utf8'))
    errs = coverage(a, list(csv.DictReader(open(src, encoding='utf8'), delimiter='\t')))
    for x in errs: print('FAIL', x)
    print(f'{app}: {len(errs)} errors'); return 1 if errs else 0

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
