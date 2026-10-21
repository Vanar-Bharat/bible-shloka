#!/usr/bin/env python3
"""S3-S6 orchestrator: draft, gate, return errors to the maker, then cross-vendor review.

Usage:
  draft_loop.py BOOK CH --src SOURCE_DIR --maker VENDOR:MODEL --reviewer VENDOR:MODEL [--dry-run]
                [--max-rounds 4] [--chunk-words 70] [--max-calls 40]
  VENDOR is anthropic | openai | gemini. Keys come from the environment (ANTHROPIC_API_KEY,
  OPENAI_API_KEY, GEMINI_API_KEY), loaded from the Spine vault by the caller; never from files here.

What it guarantees (the key criteria, in code):
  * R2: maker and reviewer vendors must differ, or it refuses to run.
  * D-19: every chunk passes tools/check_mula.py (metre, Sanskrit letters, sandhi lint, hiatus) and
    tools/check_apparatus.py (coverage, filler allow-list) before it is accepted; failures go back
    to the maker with the exact error lines, up to --max-rounds.
  * D-12: the review is written to review/ as findings; nothing in the mūla changes from it here.
  * M9: every call is appended to audit/log.jsonl; --max-calls caps spend per run.
Output: mula/<dir>/<ch>.txt (+ .deva.txt), apparatus/<dir>/<ch>.yaml, review/<dir>/<ch>.<vendor>-1.json,
        register/new_terms.pending.yaml (append). A chunk that never passes is written to
        build/failed/ and the run stops, so a human sees it; nothing failing is ever committed.
--dry-run writes the prompts to build/prompts/ and calls nothing.
"""
import argparse, csv, json, os, re, sys, time, urllib.request, yaml, collections, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import check_mula, check_apparatus
from budget import content

DIRS = dict(zip(open(os.path.join(HERE, 'book_order.txt'), encoding='utf8').read().split(),
    'genesis exodus leviticus numbers deuteronomy joshua judges ruth 1samuel 2samuel 1kings 2kings 1chronicles '
    '2chronicles ezra nehemiah esther job psalms proverbs ecclesiastes song isaiah jeremiah lamentations ezekiel '
    'daniel hosea joel amos obadiah jonah micah nahum habakkuk zephaniah haggai zechariah malachi matthew mark luke '
    'john acts romans 1corinthians 2corinthians galatians ephesians philippians colossians 1thessalonians '
    '2thessalonians 1timothy 2timothy titus philemon hebrews james 1peter 2peter 1john 2john 3john jude '
    'revelation'.split()))

# ---------- providers (swappable engines, M5) ----------
def post(url, body, headers):
    req = urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json', **headers})
    with urllib.request.urlopen(req, timeout=600) as r: return json.load(r)

def call(engine, system, user):
    vendor, model = engine.split(':', 1)
    if vendor == 'anthropic':
        j = post('https://api.anthropic.com/v1/messages',
                 {'model': model, 'max_tokens': 16000, 'system': system, 'messages': [{'role': 'user', 'content': user}]},
                 {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'})
        return ''.join(b.get('text', '') for b in j['content'])
    if vendor == 'openai':
        j = post('https://api.openai.com/v1/chat/completions',
                 {'model': model, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]},
                 {'authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']})
        return j['choices'][0]['message']['content']
    if vendor == 'gemini':
        j = post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                 {'systemInstruction': {'parts': [{'text': system}]}, 'contents': [{'role': 'user', 'parts': [{'text': user}]}]},
                 {'x-goog-api-key': os.environ['GEMINI_API_KEY']})
        return ''.join(p.get('text', '') for p in j['candidates'][0]['content']['parts'])
    raise SystemExit(f'unknown vendor {vendor}')

def audit(event):
    os.makedirs(os.path.join(ROOT, 'audit'), exist_ok=True)
    with open(os.path.join(ROOT, 'audit', 'log.jsonl'), 'a', encoding='utf8') as f:
        f.write(json.dumps({'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **event}, ensure_ascii=False) + '\n')

# ---------- context for the maker ----------
def tsv(path):
    return [r for r in csv.reader((l for l in open(path, encoding='utf8') if not l.startswith('#')), delimiter='\t') if r]

def names_for(rows):
    table = {}
    for f in ('names.proposed.tsv', 'names.tsv'):           # ratified register overrides proposals
        p = os.path.join(ROOT, 'register', f)
        if not os.path.exists(p): continue
        rr = tsv(p); h = rr[0]
        for r in rr[1:]:
            d = dict(zip(h, r)); table[(d['source'], d['lemma'])] = d
    out = {}
    for r in rows:
        key = ('grc', r['lemma']) if r['lang'] == 'grc' else (r['lang'], ([p.strip() for p in r['lemma'].split('/') if p.strip()[:1].isdigit()] or [''])[-1])
        if key in table: out[key] = table[key]
    return out

def terms_for(rows):
    reg = yaml.safe_load(open(os.path.join(ROOT, 'register', 'terms.yaml'), encoding='utf8')) or []
    lem = {r['lemma'] for r in rows}
    return [t for t in reg if any(str(t.get('source', '')).startswith(l) for l in lem if len(l) > 1)]

def chunks(rows, limit):
    verses = collections.OrderedDict()
    for r in rows: verses.setdefault(r['ref'], []).append(r)
    cur, cw = [], 0
    for ref, vr in verses.items():
        c = sum(content(r) for r in vr)
        if cur and cw + c > limit: yield cur; cur, cw = [], 0
        cur += vr; cw += c
    if cur: yield cur

def maker_prompt(rows, extra=''):
    fill = ', '.join(l.strip() for l in open(os.path.join(ROOT, 'register', 'fillers.tsv'), encoding='utf8') if l.strip() and not l.startswith('#'))
    system = open(os.path.join(ROOT, 'prompts', 'maker.md'), encoding='utf8').read().replace('{FILLERS}', fill)
    src = '\n'.join('\t'.join(r[k] for k in ('ref', 'surface', 'lemma', 'morph', 'gender', 'number', 'person')) for r in rows)
    nm = '\n'.join(f"{d['lemma']}\tstem {d['stem']}\t{d['gender']}\tclass {d['class']}\t{d['status']}" for d in names_for(rows).values()) or '(none)'
    tm = yaml.safe_dump(terms_for(rows), allow_unicode=True, sort_keys=False) or '(none)'
    target = round(sum(content(r) for r in rows) / 11.34)
    user = (f'SOURCE (ref, surface, lemma, morph, gender, number, person):\n{src}\n\nNAMES:\n{nm}\n\nTERMS:\n{tm}\n'
            f'TARGET: about {target} ślokas ({4*target} pādas); must be a multiple of 4 pādas.\n{extra}')
    return system, user

def parse(text):
    m = re.search(r'\{.*\}', text, re.S)
    return json.loads(m.group(0))

def gate(mula, app, rows, scratch):
    with open(scratch, 'w', encoding='utf8') as f: f.write(mula)
    e, w = check_mula.check(scratch)
    e += check_apparatus.coverage(app, rows)
    return e, w

# ---------- main loop ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('book'); ap.add_argument('ch', type=int)
    ap.add_argument('--src', required=True); ap.add_argument('--maker', required=True); ap.add_argument('--reviewer', required=True)
    ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--max-rounds', type=int, default=4)
    ap.add_argument('--chunk-words', type=int, default=70); ap.add_argument('--max-calls', type=int, default=40)
    a = ap.parse_args()
    if a.maker.split(':')[0] == a.reviewer.split(':')[0]:
        raise SystemExit('R2: maker and reviewer must be different vendors')
    d = DIRS[a.book]
    rows = list(csv.DictReader(open(os.path.join(a.src, a.book, f'{a.ch:03d}.tsv'), encoding='utf8'), delimiter='\t'))
    build = os.path.join(ROOT, 'build'); os.makedirs(os.path.join(build, 'prompts'), exist_ok=True)
    calls, mula_parts, app_all, new_terms = 0, [], {}, []
    for i, ch_rows in enumerate(chunks(rows, a.chunk_words), 1):
        extra, ok = '', False
        for rnd in range(1, a.max_rounds + 1):
            system, user = maker_prompt(ch_rows, extra)
            if a.dry_run:
                open(os.path.join(build, 'prompts', f'{a.book}-{a.ch:03d}-{i:02d}.md'), 'w', encoding='utf8').write(system + '\n\n---\n\n' + user)
                ok = True; break
            if calls >= a.max_calls: raise SystemExit('budget cap reached (--max-calls)')
            calls += 1; text = call(a.maker, system, user)
            audit({'stage': 'S3', 'engine': a.maker, 'book': a.book, 'ch': a.ch, 'chunk': i, 'round': rnd, 'chars': len(text)})
            try:
                j = parse(text); body = '\n'.join(l for l in j['mula'].splitlines() if not l.startswith('# ') or re.match(r'# \S+ \d+:\d+(-\d+)?$', l))
                e, w = gate(body, j.get('apparatus') or {}, ch_rows, os.path.join(build, 'chunk.txt'))
            except Exception as ex:
                e, w, j, body = [f'output was not the required JSON: {ex}'], [], {}, ''
            audit({'stage': 'S4', 'book': a.book, 'ch': a.ch, 'chunk': i, 'round': rnd, 'errors': len(e), 'warnings': len(w)})
            if not e:
                mula_parts.append(body); app_all.update(j.get('apparatus') or {}); new_terms += j.get('new_terms') or []
                ok = True; break
            extra = ('\nYOUR PREVIOUS DRAFT FAILED THE GATE. Fix every line below and return the full JSON again.\n'
                     + '\n'.join(e) + '\n\nPREVIOUS DRAFT:\n' + body)
        if not ok:
            os.makedirs(os.path.join(build, 'failed'), exist_ok=True)
            open(os.path.join(build, 'failed', f'{a.book}-{a.ch:03d}-{i:02d}.txt'), 'w', encoding='utf8').write(body + '\n\n' + '\n'.join(e))
            raise SystemExit(f'chunk {i} failed the gate after {a.max_rounds} rounds; see build/failed/')
    if a.dry_run:
        print(f'dry run: prompts in build/prompts/ for {a.book} {a.ch}'); return
    vs = sorted({r['ref'] for r in rows}, key=lambda x: int(x.split('.')[-1]))
    head = f'# {a.book} {a.ch}:1-{vs[-1].split(".")[-1]} | draft 1 | maker: {a.maker} | reviewer 1: {a.reviewer}, {time.strftime("%d %b %Y")}\n'
    for sub in ('mula', 'apparatus', 'review'): os.makedirs(os.path.join(ROOT, sub, d), exist_ok=True)
    mp = os.path.join(ROOT, 'mula', d, f'{a.ch:03d}.txt')
    open(mp, 'w', encoding='utf8').write(head + '\n'.join(mula_parts) + '\n')
    yaml.safe_dump(app_all, open(os.path.join(ROOT, 'apparatus', d, f'{a.ch:03d}.yaml'), 'w', encoding='utf8'), allow_unicode=True, sort_keys=False)
    subprocess.run([sys.executable, os.path.join(HERE, 'render.py'), mp], stdout=open(mp.replace('.txt', '.deva.txt'), 'w', encoding='utf8'), check=True)
    if new_terms:
        with open(os.path.join(ROOT, 'register', 'new_terms.pending.yaml'), 'a', encoding='utf8') as f:
            yaml.safe_dump([{**t, 'ref': f'{a.book}.{a.ch}', 'status': 'PENDING'} for t in new_terms], f, allow_unicode=True, sort_keys=False)
    # S5 review by a different vendor: findings only (D-12)
    rsys = open(os.path.join(ROOT, 'prompts', 'reviewer.md'), encoding='utf8').read()
    src = '\n'.join('\t'.join(r[k] for k in ('ref', 'surface', 'lemma', 'morph')) for r in rows)
    calls += 1; rv = call(a.reviewer, rsys, f'SOURCE:\n{src}\n\nMŪLA:\n{open(mp, encoding="utf8").read()}')
    audit({'stage': 'S5', 'engine': a.reviewer, 'book': a.book, 'ch': a.ch, 'chars': len(rv)})
    open(os.path.join(ROOT, 'review', d, f'{a.ch:03d}.{a.reviewer.split(":")[0]}-1.json'), 'w', encoding='utf8').write(rv)
    print(f'{a.book} {a.ch}: passed the gate; {calls} calls; review written')

if __name__ == '__main__':
    main()
