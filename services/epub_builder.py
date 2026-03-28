import os
import json
from ebooklib import epub
from slugify import slugify
import subprocess
from html import escape


def load_meta(folder: str) -> dict:
    """
    Load the saved metadata dictionary from meta.json in a novel output folder.
    Used by the EPUB builder and rebuild flow as the local source of truth for book metadata.
    """
    path = os.path.join(folder, "meta.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_chapter_files(folder: str) -> list[dict]:
    """
    Load all saved chapter JSON files from the local archive and sort them by chapter index.
    Used by the EPUB builder to reconstruct the book without re-downloading chapters.
    """
    chapters_folder = os.path.join(folder, "chapters")
    files = sorted(f for f in os.listdir(chapters_folder) if f.endswith(".json"))

    chapters = []
    for filename in files:
        path = os.path.join(chapters_folder, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["__source_filename"] = filename
            chapters.append(data)

    chapters.sort(key=lambda ch: ch.get("index", 0))
    return chapters


def build_cover_page() -> epub.EpubHtml:
    """
    Build a dedicated XHTML cover page for the EPUB using the embedded cover image.
    Used by the EPUB builder so readers open on a real cover page instead of metadata only.
    """
    cover_page = epub.EpubHtml(title="Cover", file_name="cover.xhtml", lang="en")
    cover_page.content = """
    <html>
      <head><title>Cover</title></head>
      <body style="margin:0; padding:0; text-align:center;">
        <img src="cover.jpg" alt="Cover" style="max-width:100%; height:auto;" />
      </body>
    </html>
    """
    return cover_page


def build_info_page(meta: dict) -> epub.EpubHtml:
    """
    Build an EPUB front-matter page that displays book information and enriched metadata.
    Used before the table of contents so title, author, genre, rating, and description are visible in the ebook.
    """
    title = meta.get("title", "Unknown Title")
    alt_title = (
        meta.get("alt_title")
        or meta.get("alternate_title")
        or meta.get("alternative_title")
    )
    author = meta.get("author")
    translator = meta.get("translator")
    description = meta.get("description")
    genre = meta.get("genre")
    rating = meta.get("rating")
    year = meta.get("year")
    status = meta.get("status")
    country = meta.get("country")

    info_sections = [f"<h1>{escape(title)}</h1>"]

    if alt_title:
        info_sections.append(
            f"<p><strong>Alternate Title:</strong> {escape(alt_title)}</p>"
        )
    if author:
        info_sections.append(f"<p><strong>Author:</strong> {escape(author)}</p>")
    if translator:
        info_sections.append(
            f"<p><strong>Translator:</strong> {escape(translator)}</p>"
        )
    if genre:
        info_sections.append(f"<p><strong>Genre:</strong> {escape(genre)}</p>")
    if rating:
        info_sections.append(f"<p><strong>Rating:</strong> {escape(rating)}</p>")
    if year:
        info_sections.append(f"<p><strong>Year:</strong> {escape(year)}</p>")
    if status:
        info_sections.append(f"<p><strong>Status:</strong> {escape(status)}</p>")
    if country:
        info_sections.append(
            f"<p><strong>Country of Origin:</strong> {escape(country)}</p>"
        )
    if description:
        info_sections.append(f"<h2>Description</h2><p>{escape(description)}</p>")

    info_html = "".join(info_sections)

    info_page = epub.EpubHtml(
        title="Book Information", file_name="book-info.xhtml", lang="en"
    )
    info_page.content = f"""
    <html>
      <head><title>Book Information</title></head>
      <body>
        {info_html}
      </body>
    </html>
    """
    return info_page


def build_epub_from_json(folder: str) -> str:
    """
    Build an EPUB file from the local metadata, cover image, and chapter JSON archive.
    Called after downloads finish or in rebuild-only mode to generate the final ebook without re-scraping.
    """
    meta_path = os.path.join(folder, "meta.json")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    title = meta.get("title", "Unknown Title")
    author = meta.get("author", "Unknown")
    book_slug = slugify(title)

    book = epub.EpubBook()
    book.set_identifier(book_slug)
    book.set_title(title)
    book.set_language("en")
    book.add_author(author)
    description = meta.get("description")
    cover_path = meta.get("cover_path")
    if description:
        book.add_metadata("DC", "description", description)
    cover_page = None
    if cover_path and os.path.exists(cover_path):
        with open(cover_path, "rb") as f:
            book.set_cover("cover.jpg", f.read(), create_page=False)
        cover_page = build_cover_page()
        book.add_item(cover_page)

    info_page = build_info_page(meta)
    book.add_item(info_page)

    chapters = load_chapter_files(folder)
    epub_chapters = []

    for data in chapters:
        chapter_index = data.get("index", 0)
        chapter_title = data.get("title") or f"Chapter {chapter_index}"
        chapter_html = (data.get("html") or "").strip()
        chapter_text = (data.get("text") or "").strip()

        if not chapter_html:
            if chapter_text:
                paragraphs = "".join(
                    f"<p>{escape(paragraph.strip())}</p>"
                    for paragraph in chapter_text.split("\n\n")
                    if paragraph.strip()
                )
                chapter_html = paragraphs or "<p>No content available.</p>"
            else:
                chapter_html = "<p>No content available.</p>"

        chapter_file_name = f"chapter-{chapter_index:04d}.xhtml"

        chapter = epub.EpubHtml(
            title=escape(chapter_title), file_name=chapter_file_name, lang="en"
        )

        chapter.content = f"""
        <html>
          <head><title>{escape(chapter_title)}</title></head>
          <body>
            <h1>{escape(chapter_title)}</h1>
            {chapter_html}
          </body>
        </html>
        """
        book.add_item(chapter)
        epub_chapters.append(chapter)

    toc_items = []
    if cover_page is not None:
        toc_items.append(epub.Link("cover.xhtml", "Cover", "cover"))
    toc_items.append(epub.Link("book-info.xhtml", "Book Information", "book-info"))
    book.toc = toc_items + epub_chapters

    if cover_page is not None:
        book.spine = [cover_page, info_page, "nav"] + epub_chapters
    else:
        book.spine = [info_page, "nav"] + epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub_path = os.path.join(folder, f"{book_slug}.epub")
    epub.write_epub(epub_path, book)

    return epub_path


def convert_epub_to_azw3(epub_path: str) -> str:
    """
    Convert a generated EPUB file into AZW3 format using Calibre's ebook-convert tool.
    Used after EPUB creation so the book can be read on Kindle devices.
    """
    azw3_path = epub_path.rsplit(".", 1)[0] + ".azw3"

    result = subprocess.run(
        ["ebook-convert", epub_path, azw3_path], capture_output=True, text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"AZW3 conversion failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    return azw3_path
