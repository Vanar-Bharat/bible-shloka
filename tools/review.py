#!/usr/bin/env python3
import sys as _s; _s.stdout.reconfigure(encoding='utf-8')
"""S5 review of an existing mūla chapter by a different vendor (R2). Findings only (D-12).

Usage: review.py BOOK CH --src SOURCE_DIR --reviewer VENDOR:MODEL [--maker-vendor anthropic] [--env-file PATH]
Writes review/<dir>/<ch>.<vendor>-N.json and logs the call to audit/log.jsonl.
"""
import argparse, csv, glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
from draft_loop import DIRS, call, audit, load_env

ap = argparse.ArgumentParser()
ap.add_argument('book'); ap.add_argument('ch', type=int)
ap.add_argument('--src', required=True); ap.add_argument('--reviewer', required=True)
ap.add_argument('--maker-vendor', default='anthropic'); ap.add_argument('--env-file', default='~/.bible-shloka/keys.env')
a = ap.parse_args(); load_env(a.env_file)
vendor = a.reviewer.split(':')[0]
if vendor == a.maker_vendor: sys.exit('R2: reviewer must be a different vendor from the maker')
d = DIRS[a.book]; mp = os.path.join(ROOT, 'mula', d, f'{a.ch:03d}.txt')
rows = list(csv.DictReader(open(os.path.join(a.src, a.book, f'{a.ch:03d}.tsv'), encoding='utf8'), delimiter='\t'))
src = '\n'.join('\t'.join(r[k] for k in ('ref', 'surface', 'lemma', 'morph')) for r in rows)
system = open(os.path.join(ROOT, 'prompts', 'reviewer.md'), encoding='utf8').read()
out = call(a.reviewer, system, f'SOURCE:\n{src}\n\nMŪLA:\n{open(mp, encoding="utf8").read()}')
audit({'stage': 'S5', 'engine': a.reviewer, 'book': a.book, 'ch': a.ch, 'chars': len(out)})
os.makedirs(os.path.join(ROOT, 'review', d), exist_ok=True)
n = 1 + len(glob.glob(os.path.join(ROOT, 'review', d, f'{a.ch:03d}.{vendor}-*.json')))
p = os.path.join(ROOT, 'review', d, f'{a.ch:03d}.{vendor}-{n}.json')
open(p, 'w', encoding='utf8').write(out); print('review written:', p)
