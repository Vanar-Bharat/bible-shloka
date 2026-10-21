#!/usr/bin/env python3
"""S2 naturalisation proposals for every proper name in the Bible (D-19).

Usage: naturalise.py SOURCE_DIR OUT_TSV
Reads the ingested TSVs, collects Greek name lemmas (capitalised) and Hebrew/Aramaic 'Np' lemmas,
and proposes a Sanskrit stem, gender and declension class for each. Every row is PENDING: the
reviewer confirms, and ratified rows move to register/names.tsv (which always wins).

Greek rules (Indo-Greek precedent: Aśokan aṃtiyoka, coin legends): letters to the nearest Sanskrit
sound (ζ->j, ξ->kṣ, ψ->ps, θ->th, φ->ph, χ->kh, η/ε->e, ω/ο->o, υ->u per D-18, ου->ū, rough breathing->h);
vowel hiatus inside the word is broken by a glide (e/i + V -> ey/iy, o/u + V -> ov/uv) or merged
(a+a -> ā); endings: -ος/-ης/-ας m -> a-stem, -ους -> u-stem, -α/-η f -> ā-stem, -ων -> -ona a-stem,
-ις -> i-stem, -ευς -> -eva a-stem, Semitic indeclinables -> a-stem (m) or ā-stem (f).
Hebrew rules: pointed consonants and vowels to Sanskrit letters (ח->h, ע and א silent, צ->ts,
ט->ṭ, ק->k, שׁ->ś, שׂ->s, ז->j); masculine names -> a-stem, feminine -> ā-stem; vocal shewa -> a.
"""
import csv, glob, os, re, sys, unicodedata, collections

GR = {'α':'a','β':'b','γ':'g','δ':'d','ε':'e','ζ':'j','η':'e','θ':'th','ι':'i','κ':'k','λ':'l','μ':'m','ν':'n',
      'ξ':'kṣ','ο':'o','π':'p','ρ':'r','σ':'s','ς':'s','τ':'t','υ':'u','φ':'ph','χ':'kh','ψ':'ps','ω':'o'}
VOW = 'aāiīuūeo'

def strip_gr(w):
    d = unicodedata.normalize('NFD', w)
    rough = '̔' in d[:4]
    return rough, ''.join(c for c in d if not unicodedata.combining(c)).lower()

def fix_hiatus(s):
    for _ in range(4):
        s = re.sub(r'aa|āa|aā|āā', 'ā', s)
        s = re.sub(r'(ai|au)([aāiīuūeo])', lambda m: m.group(1)[0] + ('y' if m.group(1) == 'ai' else 'v') + m.group(2), s)
        s = re.sub(r'([eiī])([aāiīuūeo])', r'\1y\2', s)
        s = re.sub(r'([ouū])([aāiīuūeo])', r'\1v\2', s)
        s = re.sub(r'([aā])([eiī])', r'\1y\2', s)
        s = re.sub(r'([aā])([ouū])', r'\1v\2', s)
    return s

def greek(lemma, gender):
    rough, w = strip_gr(lemma)
    w = w.replace('γγ', 'ṅg').replace('γκ', 'ṅk').replace('γχ', 'ṅkh').replace('ου', 'ū').replace('ει', 'ī')
    s = ''.join(GR.get(c, c) for c in w)
    if rough and s[0] in VOW: s = 'h' + s
    if s[0] == 'i' and len(s) > 1 and s[1] in VOW: s = 'y' + s[1:]      # Ἰησοῦς -> yesu (6.1.77)
    if s.startswith('rh'): s = 'r' + s[2:]
    for end, stem, cls, g in (('ūs', 'u', 'u', 'm'), ('eus', 'eva', 'a', 'm'), ('os', 'a', 'a', 'm'), ('es', 'a', 'a', 'm'),
                              ('as', 'a', 'a', 'm'), ('on', 'ona', 'a', 'm'), ('is', 'i', 'i', None)):
        if s.endswith(end):
            st = s[:-len(end)] + stem; return fix_hiatus(st), g or gender or 'm', cls, 'G-' + end
    if gender == 'f' and s[-1] in 'ae':
        return fix_hiatus(s[:-1] + 'ā'), 'f', 'ā', 'G-a'
    if s[-1] in VOW:   # indeclinable ending in a vowel
        return fix_hiatus(s[:-1] + ('ā' if gender == 'f' else 'a')), gender or 'm', 'ā' if gender == 'f' else 'a', 'G-indecl'
    return fix_hiatus(s + ('ā' if gender == 'f' else 'a')), gender or 'm', 'ā' if gender == 'f' else 'a', 'G-semitic'

HC = {'א':'','ב':'b','ג':'g','ד':'d','ה':'h','ו':'v','ז':'j','ח':'h','ט':'ṭ','י':'y','כ':'k','ך':'kh','ל':'l','מ':'m','ם':'m',
      'נ':'n','ן':'n','ס':'s','ע':'','פ':'p','ף':'ph','צ':'ts','ץ':'ts','ק':'k','ר':'r','ש':'ś','ת':'t'}
HV = {'ַ':'a','ָ':'ā','ֵ':'e','ֶ':'e','ִ':'i','ֹ':'o','ֺ':'o','ֻ':'u',
      'ֲ':'a','ֱ':'e','ֳ':'o','ְ':''}
def hebrew(surface, gender):
    w = max(surface.split('/'), key=len)   # drop prefixes/suffixes split by OSHB
    w = re.sub(r'[֑-ֽֿ֯׀׃-׆]', '', w)   # cantillation, meteg, punctuation
    out, i = [], 0
    while i < len(w):
        c = w[i]; i += 1
        if c in HC:
            base = HC[c]
            marks = ''
            while i < len(w) and unicodedata.combining(w[i]): marks += w[i]; i += 1
            if c == 'ש' and 'ׂ' in marks: base = 's'
            if c in 'בכפ' and 'ּ' not in marks: base = {'ב':'b','כ':'kh','פ':'ph'}[c]
            if c == 'ו' and marks == 'ּ': out.append('ū'); continue
            if c == 'ו' and 'ֹ' in marks and not out: base = 'v'
            elif c == 'ו' and marks in ('ֹ', ''): out.append('o' if marks else 'v'); continue
            if c == 'י' and not marks and out and out[-1] in ('i', 'e'): out[-1] = {'i':'ī','e':'e'}[out[-1]]; continue
            out.append(base)
            for m in marks:
                if m == '\u05B0' and len([x for x in out if x]) == 1: out.append('a')   # initial vocal shewa
                elif m in HV: out.append(HV[m])
    s = re.sub(r'(.)\1+', r'\1\1', ''.join(out))
    s = s.strip() or '?'
    s = fix_hiatus(s.lstrip('aāeiou') if False else s)
    if s[-1] == 'h' and len(s) > 2 and s[-2] in 'aā': s = s[:-1]           # final he mater lectionis
    if gender == 'f':
        stem = s[:-1] + 'ā' if s[-1] in 'aā' else s + 'ā'; return fix_hiatus(stem), 'f', 'ā', 'H-f'
    stem = s if s[-1] in 'a' else (s[:-1] + 'a' if s[-1] in 'āeo' else s + 'a')
    return fix_hiatus(stem), gender or 'm', 'a', 'H-m'

def main(src, out):
    seen = collections.OrderedDict()
    for f in sorted(glob.glob(os.path.join(src, '*', '*.tsv'))):
        for r in csv.DictReader(open(f, encoding='utf8'), delimiter='\t'):
            if r['lang'] == 'grc':
                if not r['lemma'][:1].isupper(): continue
                key = ('grc', r['lemma'])
            else:
                segs = r['morph'][1:].split('/')
                if not any(s[:2] == 'Np' for s in segs): continue
                nums = [p.strip() for p in r['lemma'].split('/') if p.strip()[:1].isdigit()]
                if not nums: continue
                key = (r['lang'], nums[-1])
            e = seen.setdefault(key, {'n': 0, 'first': r['ref'], 'surf': collections.Counter(), 'g': collections.Counter()})
            e['n'] += 1; e['surf'][r['surface']] += 1; e['g'][r['gender']] += 1
    fixed = {}
    reg = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'register', 'names.tsv')
    for row in csv.reader((l for l in open(reg, encoding='utf8') if not l.startswith('#')), delimiter='\t'):
        if row and row[0] != 'source': fixed[(row[0], row[1])] = row
    with open(out, 'w', encoding='utf8') as f:
        f.write('# Generated by tools/naturalise.py. All rows PENDING; register/names.tsv overrides.\n')
        f.write('source\tlemma\tsurface\tcount\tfirst_ref\tstem\tgender\tclass\trule\tstatus\n')
        for (lang, lemma), e in seen.items():
            g = e['g'].most_common(1)[0][0]
            surf = e['surf'].most_common(1)[0][0]
            if lang != 'grc' and lemma in ('3068', '3069', '3050'):   # the divine name: never automatic
                stem, gg, cls, rule, st = '-', 'm', '-', 'divine name: decision D-25', 'DECISION'
            elif (lang, lemma) in fixed:
                r = fixed[(lang, lemma)]; stem, gg, cls, rule, st = r[2], r[3], r[4], r[6], r[8]
            else:
                try:
                    stem, gg, cls, rule = greek(lemma, g) if lang == 'grc' else hebrew(surf, g)
                except Exception as ex:
                    stem, gg, cls, rule = '?', g, '?', f'error {ex}'
                stem = fix_hiatus(stem); st = 'PENDING'
            f.write(f'{lang}\t{lemma}\t{surf}\t{e["n"]}\t{e["first"]}\t{stem}\t{gg}\t{cls}\t{rule}\t{st}\n')
    print(f'{len(seen)} names written to {out}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
