#!/usr/bin/env python3
"""Draft every chapter that has no mūla yet, in dependency order, stopping at the first gate failure.

Usage: run_bible.py --src SOURCE_DIR --maker VENDOR:MODEL --reviewer VENDOR:MODEL [--dry-run] [--limit N]
Order: flagship Philemon first (done), then the rest of Paul (shortest first, so the register grows on
small texts), then the other NT books, then the OT. This is the drafting order, not the reading
order (D-04 governs publication). Each chapter goes through tools/draft_loop.py, so every gate applies.
"""
import argparse, os, subprocess, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
from draft_loop import DIRS
PAUL = ['Phlm', 'Titus', '2Thess', '1Thess', 'Phil', 'Col', '2Tim', 'Eph', '1Tim', 'Gal', '2Cor', '1Cor', 'Rom']
OTHER_NT = ['3John', '2John', 'Jude', '2Pet', '1John', '1Pet', 'Jas', 'Heb', 'Mark', 'Matt', 'Luke', 'John', 'Acts', 'Rev']
ORDER = PAUL + OTHER_NT + [b for b in DIRS if b not in PAUL + OTHER_NT]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True); ap.add_argument('--maker', required=True); ap.add_argument('--reviewer', required=True)
    ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args(); n = 0
    for b in ORDER:
        for f in sorted(glob.glob(os.path.join(a.src, b, '*.tsv'))):
            ch = int(os.path.basename(f)[:3])
            if os.path.exists(os.path.join(ROOT, 'mula', DIRS[b], f'{ch:03d}.txt')): continue
            cmd = [sys.executable, os.path.join(HERE, 'draft_loop.py'), b, str(ch), '--src', a.src, '--maker', a.maker, '--reviewer', a.reviewer]
            if a.dry_run: cmd.append('--dry-run')
            if subprocess.run(cmd).returncode: sys.exit(f'stopped at {b} {ch}')
            n += 1
            if a.limit and n >= a.limit: return
    print(f'{n} chapters processed')

if __name__ == '__main__':
    main()
