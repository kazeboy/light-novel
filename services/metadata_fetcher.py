from typing import List
from urllib.parse import urlparse, quote_plus
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def derive_search_title(novel_title: str | None, novel_url: str) -> str:
    """
    Derive a clean search title from the scraped novel title or fall back to the URL slug.
    Used before querying NovelUpdates for richer metadata.
    """
    if (
        novel_title
        and novel_title.strip()
        and novel_title.strip().lower() != "unknown title"
    ):
        return novel_title.strip()

    path = urlparse(novel_url).path.strip("/")
    slug = path.split("/")[-1] if path else ""

    cleaned = slug.replace("-", " ").replace("_", " ").strip()

    if cleaned:
        return cleaned.title()

    return "Unknown Title"


def resolve_metadata(search_title: str) -> dict:
    """
    Create a normalized metadata dictionary with default placeholder fields.
    Used as a consistent structure before metadata is enriched from external sources.
    """
    return {
        "title": search_title,
        "author": None,
        "description": None,
        "cover_url": None,
        "alt_title": None,
        "genre": None,
        "rating": None,
        "year": None,
        "status": None,
        "country": None,
        "metadata_source": None,
        "metadata_url": None,
    }


def search_novelupdates_results(search_title: str, limit: int = 5) -> List[dict]:
    """
    Search NovelUpdates for matching series and return a small list of candidate results.
    Used when a new novel is added so the user can choose the correct metadata source.
    """
    search_url = f"https://www.novelupdates.com/series-finder/?sf=1&sh={quote_plus(search_title)}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        result_cards = page.locator("div.search_main_box_nu")
        count = min(result_cards.count(), limit)
        results: List[dict] = []

        for i in range(count):
            card = result_cards.nth(i)
            title_link = card.locator("div.search_body_nu div.search_title a").first

            if title_link.count() == 0:
                continue

            title = title_link.inner_text().strip()
            href = title_link.get_attribute("href")

            if href and href.startswith("/"):
                href = "https://www.novelupdates.com" + href

            results.append(
                {
                    "index": len(results) + 1,
                    "title": title,
                    "url": href,
                }
            )

        context.close()
        browser.close()
        return results


def choose_novelupdates_result(results: List[dict]) -> str | None:
    """
    Let the user choose the correct NovelUpdates result when multiple matches are found.
    Used interactively by main.py before fetching detailed metadata.
    """
    if not results:
        return None

    if len(results) == 1:
        return results[0]["url"]

    print("\nMultiple NovelUpdates matches found:")
    for item in results:
        print(f"  {item['index']}. {item['title']}")
        print(f"     {item['url']}")

    while True:
        choice = input("Select a result number, or press Enter to skip: ").strip()

        if not choice:
            return None

        if choice.isdigit():
            selected_index = int(choice)
            for item in results:
                if item["index"] == selected_index:
                    return item["url"]

        print(
            "Invalid choice. Please enter one of the listed numbers, or press Enter to skip."
        )


def fetch_novelupdates_metadata(series_url: str) -> dict:
    """
    Fetch detailed metadata from a NovelUpdates series page using Playwright and BeautifulSoup.
    Used to enrich local metadata with author, alt titles, genre, rating, year, status, country, and cover.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        page.goto(series_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        html = page.content()
        context.close()
        browser.close()

    soup = BeautifulSoup(html, "lxml")

    title = None
    author = None
    description = None
    cover_url = None
    alt_title = None
    genre = None
    rating = None
    year = None
    status = None
    country = None

    title_tag = soup.select_one("div.seriestitlenu")
    if title_tag:
        title = title_tag.get_text(" ", strip=True)

    author_tag = soup.select_one("div#showauthors")
    if author_tag:
        author = author_tag.get_text(" ", strip=True)

    desc_tag = soup.select_one("div#editdescription")
    if desc_tag:
        description = desc_tag.get_text(" ", strip=True)

    cover_tag = soup.select_one(".seriesimg img")
    if cover_tag and cover_tag.get("src"):
        cover_url = cover_tag["src"]

    alt_title_tag = soup.select_one("div#editassociated")
    if alt_title_tag:
        alt_lines = [
            line.strip()
            for line in alt_title_tag.get_text("\n", strip=True).splitlines()
            if line.strip()
        ]
        if alt_lines:
            alt_title = " | ".join(alt_lines)

    genre_container = soup.select_one("div#seriesgenre")
    if genre_container:
        genre_tags = genre_container.select("a.genre") or genre_container.select("a")
        genre_values = [
            tag.get_text(" ", strip=True)
            for tag in genre_tags
            if tag.get_text(" ", strip=True)
        ]
        if genre_values:
            genre = ", ".join(genre_values)

    rating_tag = soup.select_one("span.uvotes")
    if rating_tag:
        rating = rating_tag.get_text(" ", strip=True)
    else:
        rating_container = soup.find(
            "h5", class_="seriesother", string=lambda s: s and "Rating" in s
        )
        if rating_container:
            next_span = rating_container.find_next("span", class_="uvotes")
            if next_span:
                rating = next_span.get_text(" ", strip=True)

    year_tag = soup.select_one("div#edityear")
    if year_tag:
        year = year_tag.get_text(" ", strip=True)

    status_tag = soup.select_one("div#editstatus")
    if status_tag:
        status = status_tag.get_text(" ", strip=True)

    country_tag = soup.select_one("div#showlang")
    if country_tag:
        country = country_tag.get_text(" ", strip=True)
    else:
        type_tag = soup.select_one("span.type")
        if type_tag:
            type_text = type_tag.get_text(" ", strip=True)
            if "(" in type_text and ")" in type_text:
                country = type_text[
                    type_text.rfind("(") + 1 : type_text.rfind(")")
                ].strip()

    return {
        "title": title,
        "author": author,
        "description": description,
        "cover_url": cover_url,
        "alt_title": alt_title,
        "genre": genre,
        "rating": rating,
        "year": year,
        "status": status,
        "country": country,
        "metadata_source": "novelupdates",
        "metadata_url": series_url,
    }
