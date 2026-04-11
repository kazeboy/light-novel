# skill: add-jlpt-feature
> Reusable Claude procedure for extending Japanese language and JLPT study features.
> Usage: "Execute the add-jlpt-feature skill for [feature description]"

---

## Role
You are a Python developer extending the Japanese language features of the light-novel tool.
Before writing any code, read `context/architecture.md` (furigana system section) and `context/conventions.md`.

## Input
A description of the new Japanese/JLPT feature. Examples:
- "Add a vocabulary extraction mode that lists unknown kanji per chapter"
- "Add a new furigana mode that shows readings only for N1 kanji"
- "Export an Anki deck from a downloaded novel's unknown vocabulary"

## Understanding the Existing System

### Furigana pipeline
```
apply_furigana(text, mode)          ← services/furigana.py — entry point
    ├── add_furigana_all(text)       ← mode = "all"
    └── add_furigana_by_level(text, mode)  ← mode = n4/n3/n2/n1/rare
            └── token_has_unknown_kanji(surface, mode)
                    └── KNOWN_KANJI_BY_MODE[mode]  ← set of known kanji for the level
```

### JLPT kanji data
- Files: `data/jlpt_kanji/n1.txt` through `n5.txt`
- Format: one kanji per line (or multiple per line — the loader iterates characters)
- Loaded at module import time as frozen sets: `JLPT_N5`, `JLPT_N4`, `JLPT_N3`, `JLPT_N2`, `JLPT_N1`
- Combined sets: `KNOWN_KANJI_BY_MODE` dict maps mode string → set of "known" kanji at that level

**Never modify the `.txt` files** — they are authoritative reference data.

### Janome tokenizer
```python
from janome.tokenizer import Tokenizer
_TOKENIZER = Tokenizer()

for token in _TOKENIZER.tokenize(text):
    surface = token.surface       # the actual word/character
    reading = token.reading       # katakana reading (may be "*" if unknown)
```

Convert katakana reading to hiragana with `kata_to_hira(reading)` before using in ruby tags.

## Steps

1. **Define the feature clearly** — What input does it take? What output does it produce? Does it integrate into the EPUB pipeline, or is it a standalone export?

2. **Locate the right file** — New furigana modes belong in `services/furigana.py`. New study exports (Anki, vocabulary lists) should go in a new `services/study_export.py`. New AI-assisted features go in `services/ai.py`.

3. **Add the mode string** (if adding a new furigana mode) — Add it to `KNOWN_KANJI_BY_MODE` dict and to the `apply_furigana()` dispatch. Update the mode prompt in `main.py` to include the new option.

4. **Follow the token loop pattern** — Any new analysis that walks Japanese text should use the same `_TOKENIZER.tokenize(text)` loop. Don't create a second Tokenizer instance.

5. **Keep the pipeline non-blocking** — If the feature is optional or slow, make it easy to skip. Follow the pattern: `if mode != "none": do_the_thing()`.

6. **Docstring every new function** — One-liner: what it does + when it's called.

7. **Test manually** — Run `python lngrab.py` on a syosetu.com novel with the new mode active. Inspect the resulting EPUB or export file for correctness.

## Constraints
- JLPT data files (`data/jlpt_kanji/`) are read-only — never write or modify them
- New Tokenizer instances are expensive — always use the module-level `_TOKENIZER` singleton
- Furigana modes are always string values — never integers
- AI-assisted features (e.g. vocabulary explanation) go in `services/ai.py`, not in `furigana.py`

## Output Format
1. The modified or new service file(s)
2. Any changes to `main.py` (mode prompt additions)
3. A note on what the feature produces and how to verify it works
