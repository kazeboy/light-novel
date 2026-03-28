from bs4 import BeautifulSoup

BAD_SELECTORS = [
    "script",
    "style",
    "noscript",
    "iframe",
    "form",
    "button",
    "nav",
    "footer",
    ".sharedaddy",
    ".jp-relatedposts",
    ".comments-area",
    "#comments",
]

BAD_TEXT_PATTERNS = [
    "previous",
    "next",
    "table of contents",
    "toc",
    "shmtranslations",
    "support us",
    "patreon",
    "discord",
    "buy me a coffee",
]


def is_bad_text(text: str) -> bool:
    """
    Return True when a line of text matches known junk or navigation patterns.
    Used by chapter-cleaning logic to skip links, prompts, and site-specific boilerplate.
    """
    lower = text.lower()
    return any(pattern in lower for pattern in BAD_TEXT_PATTERNS)


def clean_chapter_html(container) -> tuple[str, str]:
    """
    Clean a chapter content container and return both sanitized HTML and plain text.
    Used by source scrapers before saving chapter JSON and building EPUB files.
    """
    working = BeautifulSoup(str(container), "lxml")

    # Remove unwanted tags
    for selector in BAD_SELECTORS:
        for tag in working.select(selector):
            tag.decompose()

    html_parts: list[str] = []
    text_parts: list[str] = []

    for element in working.find_all(["p", "h2", "h3", "blockquote", "li"]):
        text = element.get_text(" ", strip=True)

        if not text:
            continue

        # Remove navigation / junk text
        if is_bad_text(text):
            continue

        # Remove very short lines
        if len(text) < 3:
            continue

        html_parts.append(str(element))
        text_parts.append(text)

    clean_html = "\n".join(html_parts).strip()
    clean_text = "\n\n".join(text_parts).strip()
    return clean_html, clean_text
