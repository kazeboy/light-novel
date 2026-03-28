import re
from janome.tokenizer import Tokenizer


KANJI_RE = re.compile(r"[一-龯]")
HIRAGANA_RE = re.compile(r"^[ぁ-ゖー]+$")

# A lightweight starter set of common kanji for the initial "rare" mode.
# This can be expanded later with a fuller joyo/JLPT list.
COMMON_KANJI = set(
    "日一国会人年大十二本中長出三同時政事自行社見月分後前生五間上東四今金九入学高円子外八六下来気小七山話女北午百書先名川千水半男西電校語土木聞食車何南万毎白天母火右読友左休父雨"
)

_TOKENIZER = Tokenizer()


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


def is_common_kanji_token(text: str) -> bool:
    """
    Return True when every kanji in the token belongs to the starter common-kanji set.
    Used by the initial rare-kanji mode to decide whether furigana should be skipped.
    """
    kanji_chars = [char for char in text if KANJI_RE.match(char)]
    if not kanji_chars:
        return True
    return all(char in COMMON_KANJI for char in kanji_chars)


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


def add_furigana_rare(text: str) -> str:
    """
    Add furigana ruby markup only to kanji-containing tokens that are outside the starter common-kanji set.
    Used when the user selects the initial "rare kanji" furigana mode.
    """
    parts = []
    for token in _TOKENIZER.tokenize(text):
        surface = token.surface
        reading = getattr(token, "reading", None)

        if not surface:
            continue

        if (
            contains_kanji(surface)
            and not is_common_kanji_token(surface)
            and reading
            and reading != "*"
        ):
            hira = kata_to_hira(reading)
            parts.append(build_ruby(surface, hira))
        else:
            parts.append(surface)

    return "".join(parts)


def apply_furigana(text: str, mode: str = "none") -> str:
    """
    Apply the selected furigana mode to a block of Japanese text.
    Supported modes are: none, all, and rare.
    """
    if not text or mode == "none":
        return text
    if mode == "all":
        return add_furigana_all(text)
    if mode == "rare":
        return add_furigana_rare(text)
    return text
