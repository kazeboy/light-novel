import re
from janome.tokenizer import Tokenizer
import os


KANJI_RE = re.compile(r"[一-龯]")
HIRAGANA_RE = re.compile(r"^[ぁ-ゖー]+$")

_TOKENIZER = Tokenizer()

# Load JLPT kanji lists from data/jlpt_kanji/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JLPT_DIR = os.path.join(BASE_DIR, "data", "jlpt_kanji")


def load_kanji_file(filename: str) -> set:
    path = os.path.join(JLPT_DIR, filename)
    kanji_set = set()
    if not os.path.exists(path):
        return kanji_set

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            for char in line:
                if KANJI_RE.match(char):
                    kanji_set.add(char)

    return kanji_set


JLPT_N5 = load_kanji_file("n5.txt")
JLPT_N4 = load_kanji_file("n4.txt")
JLPT_N3 = load_kanji_file("n3.txt")
JLPT_N2 = load_kanji_file("n2.txt")
JLPT_N1 = load_kanji_file("n1.txt")

KNOWN_KANJI_BY_MODE = {
    "n4": JLPT_N5,
    "n3": JLPT_N5 | JLPT_N4,
    "n2": JLPT_N5 | JLPT_N4 | JLPT_N3,
    "n1": JLPT_N5 | JLPT_N4 | JLPT_N3 | JLPT_N2,
    "rare": JLPT_N5 | JLPT_N4 | JLPT_N3 | JLPT_N2 | JLPT_N1,
}


def token_has_unknown_kanji(surface: str, mode: str) -> bool:
    if mode == "all":
        return True
    known_set = KNOWN_KANJI_BY_MODE.get(mode, set())
    for char in surface:
        if KANJI_RE.match(char) and char not in known_set:
            return True
    return False


def kata_to_hira(text: str) -> str:
    """
    Convert katakana reading text into hiragana for EPUB ruby tags.
    Used after Janome returns readings in katakana.
    """
    return "".join(
        chr(ord(char) - 0x60) if "ァ" <= char <= "ヶ" else char for char in text
    )


def contains_kanji(text: str) -> bool:
    """
    Return True when the given text contains at least one kanji character.
    Used to decide whether a token is a candidate for furigana processing.
    """
    return bool(KANJI_RE.search(text))


def build_ruby(surface: str, reading: str) -> str:
    """
    Wrap a token in EPUB-compatible ruby markup using a hiragana reading.
    Used by the furigana transformation functions when a token needs annotation.
    """
    if not surface or not reading:
        return surface
    return f"<ruby>{surface}<rt>{reading}</rt></ruby>"


def add_furigana_all(text: str) -> str:
    """
    Add furigana ruby markup to all kanji-containing tokens in the given Japanese text.
    Used when the user selects the "all kanji" furigana mode.
    """
    parts = []
    for token in _TOKENIZER.tokenize(text):
        surface = token.surface
        reading = getattr(token, "reading", None)

        if not surface:
            continue

        if contains_kanji(surface) and reading and reading != "*":
            hira = kata_to_hira(reading)
            parts.append(build_ruby(surface, hira))
        else:
            parts.append(surface)

    return "".join(parts)


def add_furigana_by_level(text: str, mode: str) -> str:
    """
    Add furigana ruby markup based on JLPT level mode.
    Furigana is added when a token contains kanji not in the known set for that level.
    """
    parts = []
    for token in _TOKENIZER.tokenize(text):
        surface = token.surface
        reading = getattr(token, "reading", None)

        if not surface:
            continue

        if (
            contains_kanji(surface)
            and reading
            and reading != "*"
            and token_has_unknown_kanji(surface, mode)
        ):
            hira = kata_to_hira(reading)
            parts.append(build_ruby(surface, hira))
        else:
            parts.append(surface)

    return "".join(parts)


def apply_furigana(text: str, mode: str = "none") -> str:
    """
    Apply the selected furigana mode to a block of Japanese text.
    Supported modes are: none, all, n4, n3, n2, n1, rare.
    """
    if not text or mode == "none":
        return text
    if mode == "all":
        return add_furigana_all(text)
    if mode in {"n4", "n3", "n2", "n1", "rare"}:
        return add_furigana_by_level(text, mode)
    return text
