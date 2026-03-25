import os
import json
from ebooklib import epub
from slugify import slugify
import subprocess
from html import escape


def load_meta(folder: str) -> dict:
    path = os.path.join(folder, "meta.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_chapter_files(folder: str) -> list[dict]:
    chapters_folder = os.path.join(folder, "chapters")
    files = sorted(
        f for f in os.listdir(chapters_folder)
        if f.endswith(".json")
    )

    chapters = []
    for filename in files:
        path = os.path.join(chapters_folder, filename)
        with open(path, "r", encoding="utf-8") as f:
            chapters.append(json.load(f))

    return chapters


def build_epub(folder: str) -> str:
    meta = load_meta(folder)
    chapters = load_chapter_files(folder)

    title = meta.get("title", "Untitled Novel")
    book_slug = slugify(title)

    book = epub.EpubBook()
    book.set_identifier(book_slug)
    book.set_title(title)
    book.set_language("en")

    author = meta.get("author") or "Unknown"
    book.add_author(author)

    description = meta.get("description")
    if description:
       book.add_metadata("DC", "description", description)

    epub_chapters = []

    for ch in chapters:
        index = ch["index"]
        chapter_title = ch.get("title") or f"Chapter {index}"
        chapter_html = ch.get("html", "")

        file_name = f"chap_{index:04d}.xhtml"
        epub_chapter = epub.EpubHtml(
            title=chapter_title,
            file_name=file_name,
            lang="en"
        )

        epub_chapter.content = f"""
        <html>
          <head><title>{chapter_title}</title></head>
          <body>
            <h1>{chapter_title}</h1>
            {chapter_html}
          </body>
        </html>
        """

        book.add_item(epub_chapter)
        epub_chapters.append(epub_chapter)

    book.toc = tuple(epub_chapters)
    book.spine = ["nav"] + epub_chapters

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output_path = os.path.join(folder, f"{book_slug}.epub")
    cover_path = meta.get("cover_path")
    if cover_path and os.path.exists(cover_path):
       with open(cover_path, "rb") as f:
           book.set_cover("cover.jpg", f.read())
    epub.write_epub(output_path, book)

    return output_path

def build_epub_from_json(folder: str) -> str:
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
    if cover_path and os.path.exists(cover_path):
        with open(cover_path, "rb") as f:
            book.set_cover("cover.jpg", f.read(), create_page=True)

    chapters_folder = os.path.join(folder, "chapters")
    chapter_files = sorted(
        f for f in os.listdir(chapters_folder)
        if f.endswith(".json")
    )

    epub_chapters = []

    for file in chapter_files:
        path = os.path.join(chapters_folder, file)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chapter_title = data.get("title") or file.replace(".json", "")
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

        chapter = epub.EpubHtml(
            title=escape(chapter_title),
            file_name=file.replace(".json", ".xhtml"),
            lang="en"
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

    book.toc = epub_chapters
    book.spine = ["cover", "nav"] + epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub_path = os.path.join(folder, f"{book_slug}.epub")
    epub.write_epub(epub_path, book)

    return epub_path

def convert_epub_to_azw3(epub_path: str) -> str:
    azw3_path = epub_path.rsplit(".", 1)[0] + ".azw3"

    result = subprocess.run(
        ["ebook-convert", epub_path, azw3_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"AZW3 conversion failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    return azw3_path