#!/usr/bin/env python3
"""S0 ingest: OSHB (WLC Hebrew/Aramaic) and MorphGNT (SBLGNT Greek) to one TSV per chapter.

Usage: ingest.py OSHB_WLC_DIR MORPHGNT_DIR OUT_DIR
Output: OUT_DIR/<Book>/<ch>.tsv with columns
  ref  n  surface  lemma  morph  lang  pos  gender  number  person
lang: hbo (Hebrew), arc (Aramaic), grc (Greek). gender m/f/c/n or '' ; number s/p/d or ''.
One row per word; Hebrew prefixes/suffixes stay inside the word (segments split by '/').
Prints per-book word counts so they can be compared with the upstream totals.
"""
import sys as _s; _s.stdout.reconfigure(encoding='utf-8')  # Windows consoles default to cp1252
import os, re, sys, glob, collections

OT = ['Gen','Exod','Lev','Num','Deut','Josh','Judg','Ruth','1Sam','2Sam','1Kgs','2Kgs','1Chr','2Chr',
      'Ezra','Neh','Esth','Job','Ps','Prov','Eccl','Song','Isa','Jer','Lam','Ezek','Dan','Hos','Joel',
      'Amos','Obad','Jonah','Mic','Nah','Hab','Zeph','Hag','Zech','Mal']
NT = {'61':'Matt','62':'Mark','63':'Luke','64':'John','65':'Acts','66':'Rom','67':'1Cor','68':'2Cor',
      '69':'Gal','70':'Eph','71':'Phil','72':'Col','73':'1Thess','74':'2Thess','75':'1Tim','76':'2Tim',
      '77':'Titus','78':'Phlm','79':'Heb','80':'Jas','81':'1Pet','82':'2Pet','83':'1John','84':'2John',
      '85':'3John','86':'Jude','87':'Rev'}

def heb_features(morph):
    """OSHB morph, e.g. 'HR/Ncfsa', 'HVqp3ms'. Returns lang, pos of the main segment, gender, number, person."""
    lang = {'H': 'hbo', 'A': 'arc'}[morph[0]]
    segs = morph[1:].split('/')
    # main segment: first noun/verb/adjective/pronoun, else the last segment
    main = next((s for s in segs if s[:1] in 'NVAP'), segs[-1])
    pos, g, nmb, per = main[:1], '', '', ''
    if pos in 'NA' and len(main) >= 4:          # N c f s a : type, gender, number, state
        g, nmb = main[2], main[3]
    elif pos == 'V' and len(main) >= 3:        # V stem conj [person] gender number | participle: gender number state
        rest = main[3:]
        if main[2] in 'rs':                    # participle
            g, nmb = (rest[0], rest[1]) if len(rest) >= 2 else ('', '')
        elif rest and rest[0] in '123':
            per, g, nmb = rest[0], rest[1:2], rest[2:3]
        elif len(rest) >= 2:
            g, nmb = rest[0], rest[1]
    elif pos == 'P' and len(main) >= 5:        # P p 3 m s
        per, g, nmb = main[2], main[3], main[4]
    gmap = {'m': 'm', 'f': 'f', 'b': 'c', 'c': 'c'}
    return lang, pos, gmap.get(g, ''), nmb if nmb in 'spd' else '', per if per in '123' else ''

def grk_features(pos, parse):
    """MorphGNT: pos like 'N-', parse like '----DSF-' (person tense voice mood case number gender degree)."""
    per, nmb, g = parse[0], parse[5], parse[6]
    return 'grc', pos.rstrip('-'), {'M': 'm', 'F': 'f', 'N': 'n'}.get(g, ''), {'S': 's', 'P': 'p'}.get(nmb, ''), per if per in '123' else ''

def write(out, book, rows_by_ch):
    for ch, rows in rows_by_ch.items():
        d = os.path.join(out, book); os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f'{int(ch):03d}.tsv'), 'w', encoding='utf8') as f:
            f.write('ref\tn\tsurface\tlemma\tmorph\tlang\tpos\tgender\tnumber\tperson\n')
            for r in rows: f.write('\t'.join(map(str, r)) + '\n')

def main(wlc, gnt, out):
    counts = collections.OrderedDict()
    W = re.compile(r'<w ([^>]*)>(.*?)</w>', re.S)
    for book in OT:
        x = open(os.path.join(wlc, book + '.xml'), encoding='utf8').read()
        rows_by_ch = collections.OrderedDict(); total = 0
        for ref, body in re.findall(r'<verse osisID="([^"]+)">(.*?)</verse>', x, re.S):
            ch = ref.split('.')[1]; n = 0
            for attrs, surf in W.findall(body):
                a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
                if 'morph' not in a: continue
                n += 1; total += 1
                lang, pos, g, nmb, per = heb_features(a['morph'])
                surf = re.sub(r'<[^>]+>', '', surf)
                rows_by_ch.setdefault(ch, []).append((ref, n, surf, a.get('lemma', ''), a['morph'], lang, pos, g, nmb, per))
        write(out, book, rows_by_ch); counts[book] = total
    for f in sorted(glob.glob(os.path.join(gnt, '*-morphgnt.txt'))):
        book = NT[os.path.basename(f)[:2]]
        rows_by_ch = collections.OrderedDict(); total = 0; last = None; n = 0
        for line in open(f, encoding='utf8'):
            bcv, pos, parse, text, word, norm, lemma = line.split()
            ch, v = int(bcv[2:4]), int(bcv[4:6])
            ref = f'{book}.{ch}.{v}'
            n = n + 1 if ref == last else 1; last = ref; total += 1
            lang, p, g, nmb, per = grk_features(pos, parse)
            rows_by_ch.setdefault(ch, []).append((ref, n, word, lemma, f'{pos} {parse}', lang, p, g, nmb, per))
        write(out, book, rows_by_ch); counts[book] = total
    for b, c in counts.items(): print(f'{b}\t{c}')
    print(f'TOTAL\t{sum(counts.values())}\tOT {sum(counts[b] for b in OT)}\tNT {sum(v for k, v in counts.items() if k not in OT)}')

if __name__ == '__main__':
    main(*sys.argv[1:4])
