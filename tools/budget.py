#!/usr/bin/env python3
"""S1 budget and S2 register workload, from the ingested source TSVs.

Usage: budget.py SOURCE_DIR OUT_TSV
Content words: Hebrew segments N V A P D count 1, pronominal suffix S counts 0.5;
Greek: everything except article, preposition, conjunction, particle, interjection.
Predicted shlokas = content words / 11.34 (Gita-calibrated, pilot ratio r = 1.0).
Proper names: Hebrew 'Np' segments; Greek lemmas starting with a capital letter.
"""
import os, sys, glob, csv, collections
GC = 11.34
GRK_FUNC = {'RA', 'P', 'C', 'X', 'I'}

def content(row):
    if row['lang'] == 'grc':
        return 0 if row['pos'] in GRK_FUNC else 1
    c = 0
    for seg in row['morph'][1:].split('/'):
        if seg[:1] in 'NVAPD': c += 1
        elif seg[:1] == 'S': c += 0.5
    return c

def lemma_key(row):
    if row['lang'] == 'grc': return 'G:' + row['lemma']
    nums = [p.strip() for p in row['lemma'].split('/') if p.strip()[:1].isdigit()]
    return ('H:' + nums[-1]) if nums else None

def is_name(row):
    if row['lang'] == 'grc': return row['lemma'][:1].isupper()
    return any(seg[:2] == 'Np' for seg in row['morph'][1:].split('/'))

def main(src, out):
    books = collections.OrderedDict()
    names, lemmas, freq = set(), set(), collections.Counter()
    for d in sorted(glob.glob(os.path.join(src, '*')), key=lambda p: p):
        pass
    order = [l.split('\t')[0] for l in open(os.path.join(os.path.dirname(__file__), 'book_order.txt'), encoding='utf8').read().split()] \
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'book_order.txt')) else sorted(os.listdir(src))
    for b in order:
        verses, cw, bnames = set(), 0.0, set()
        for f in sorted(glob.glob(os.path.join(src, b, '*.tsv'))):
            for row in csv.DictReader(open(f, encoding='utf8'), delimiter='\t'):
                verses.add(row['ref']); cw += content(row)
                k = lemma_key(row)
                if k:
                    lemmas.add(k); freq[k] += 1
                    if is_name(row): names.add(k); bnames.add(k)
        books[b] = (len(verses), cw, cw / GC, len(bnames))
    with open(out, 'w', encoding='utf8') as f:
        f.write('book\tverses\tcontent_words\tpredicted_shlokas\tproper_names\n')
        for b, (v, cw, s, n) in books.items():
            f.write(f'{b}\t{v}\t{cw:.0f}\t{s:.0f}\t{n}\n')
    V = sum(x[0] for x in books.values()); S = sum(x[2] for x in books.values())
    print(f'books {len(books)}  verses {V}  predicted shlokas {S:.0f}')
    print(f'distinct lemmas {len(lemmas)}  of which proper names {len(names)}')
    for t in (1, 5, 20, 100):
        print(f'lemmas occurring >= {t}x: {sum(1 for k in lemmas if freq[k] >= t and k not in names)} (non-name)')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
