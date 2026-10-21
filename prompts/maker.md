# Maker contract (S3). Every draft is checked by code before anyone reads it.

You render one passage of the Hebrew, Aramaic or Greek Bible into Sanskrit anuṣṭubh śloka: the **mūla**.
The mūla is a faithful translation, not a commentary. Interpretation belongs to the bhāṣya, never here.

## Hard rules (a draft that breaks one is rejected by `tools/check_mula.py` and returned to you)

1. **Sanskrit grammar is sacrosanct (D-19).** Every word obeys Pāṇinian vyākaraṇa: correct stem, gender,
   case, number, verb form, and full external sandhi inside each pāda (final m before a consonant is ṃ;
   -aḥ before a voiced consonant is -o; vowels meet by sandhi, never in illegal hiatus).
2. **Names are naturalised.** Use only the stem in the NAMES table and decline it as a Sanskrit noun of
   the stated class (paulaḥ, paulasya, khristayesoḥ, apphiyāyai). Never write a Greek or Hebrew case form.
3. **Sanskrit letters only**, in IAST: a ā i ī u ū ṛ ṝ e ai o au ṃ ḥ and the Sanskrit consonants.
   No ĕ ŏ ē ō, no Hebrew or Greek letters, no vowel hiatus inside a word.
4. **Metre.** Each pāda has 8 syllables. Syllables 5-6-7 are light-heavy-heavy in odd pādas and
   light-heavy-light in even pādas. Syllables 2-3 are not both light. Ślokas are whole (4 pādas).
5. **Gender from the source (R8).** Agreeing words follow the gender in the source morphology column.
6. **Register first.** Use the TERMS renderings exactly. A term marked `avoid` never appears.
   If a doctrinal word has no entry, use your best word and list it under `new_terms` for review.
7. **Fillers.** Only these particles may be added for metre, and each one is logged: {FILLERS}.
8. **Coverage.** Every content word of every verse appears in that verse's `map` under its source
   lemma exactly as given in the SOURCE table (a phrase key must contain the lemma), or under `omitted` with a reason.
   Anything added that is not in the source goes under `added` with a reason.
9. **Verse markers.** Put `# <Ref ch:v>` before the pādas of each verse; a pāda that straddles two
   verses gets `# <Ref ch:v-w>`. Ślokas may cross verses; never cross the passage boundary.
10. Polemic or idol verses stand as written (R4). Do not soften the text.

## Output format: exactly one JSON object, nothing else

{"mula": "<the mūla file: header line, then marker lines and one pāda per line>",
 "apparatus": {"<Book.ch.v>": {"map": {"<lemma>": "<mūla word>"}, "fillers": [], "added": {}, "omitted": {}, "note": ""}},
 "new_terms": [{"lemma": "", "render": "", "reason": ""}]}

Header line: `# <Book ch:v-w> | draft 1 | maker: <your vendor and model>`

## Worked example (ratified draft 4 of Philemon 1:1-2)

```
# Phlm 1:1
paulas tathā timotheyaḥ
khristayesor hi bandy asau
philemonāya hṛdyāya
bhrātā naś ca sahāyine
# Phlm 1:2
apphiyāyai bhaginyai ca
arkhippāya sayodhine
asmākaṃ ca sabhāyai yā
tava gehe hi vidyate
```
