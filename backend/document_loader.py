from pathlib import Path
from typing import Any

import fitz


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\x00", " ").split())


def _extract_tables(page: fitz.Page) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []

    if not hasattr(page, "find_tables"):
        return tables

    try:
        found_tables = page.find_tables()
    except Exception:
        return tables

    for table_number, table in enumerate(found_tables, start=1):
        rows = table.extract()
        formatted_rows = []
        for row in rows:
            cleaned_cells = [_clean_text(str(cell or "")) for cell in row]
            if any(cleaned_cells):
                formatted_rows.append(" | ".join(cleaned_cells))

        if formatted_rows:
            tables.append(
                {
                    "content": f"Table {table_number}: " + "\n".join(formatted_rows),
                    "rows": formatted_rows,
                    "table_number": table_number,
                }
            )

    return tables


def _extract_images(
    document: fitz.Document,
    page: fitz.Page,
    page_number: int,
    image_output_dir: Path,
    doc_id: str,
) -> list[dict[str, Any]]:
    images = []
    image_output_dir.mkdir(parents=True, exist_ok=True)

    for image_number, image in enumerate(page.get_images(full=True), start=1):
        xref = image[0]
        width = image[2]
        height = image[3]
        colorspace = image[5] or "unknown"

        try:
            image_data = document.extract_image(xref)
        except Exception:
            image_data = None

        image_url = None
        if image_data:
            extension = image_data.get("ext", "png")
            image_name = f"page_{page_number}_image_{image_number}.{extension}"
            image_path = image_output_dir / image_name
            image_path.write_bytes(image_data["image"])
            image_url = f"/assets/{doc_id}/{image_name}"

        content = (
            f"Image {image_number} on page {page_number}: "
            f"{width}x{height}, colorspace {colorspace}."
        )
        images.append(
            {
                "content": content,
                "image_url": image_url,
                "image_number": image_number,
                "width": width,
                "height": height,
            }
        )

    return images


def _make_chunk(
    content: str,
    page_number: int,
    kind: str,
    chunk_number: int,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "content": content,
        "page": page_number,
        "kind": kind,
        "chunk_number": chunk_number,
        "extra": extra or {},
    }


def _split_text(text: str, max_words: int = 180, overlap: int = 35) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max_words - overlap
    for start in range(0, len(words), step):
        chunk_words = words[start : start + max_words]
        if chunk_words:
            chunks.append(" ".join(chunk_words))

    return chunks


def load_pdf(
    file_path: str | Path,
    image_output_dir: str | Path | None = None,
    doc_id: str = "current",
) -> list[dict[str, Any]]:
    pdf_path = Path(file_path)
    image_dir = Path(image_output_dir) if image_output_dir else pdf_path.parent / "assets" / doc_id
    pages_data: list[dict[str, Any]] = []

    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            chunk_number = 1
            page_text = _clean_text(page.get_text("text"))

            for text_chunk in _split_text(page_text):
                pages_data.append(_make_chunk(text_chunk, page_index, "text", chunk_number))
                chunk_number += 1

            for table in _extract_tables(page):
                pages_data.append(
                    _make_chunk(
                        table["content"],
                        page_index,
                        "table",
                        chunk_number,
                        {"rows": table["rows"], "table_number": table["table_number"]},
                    )
                )
                chunk_number += 1

            for image in _extract_images(document, page, page_index, image_dir, doc_id):
                pages_data.append(
                    _make_chunk(
                        image["content"],
                        page_index,
                        "image",
                        chunk_number,
                        {
                            "image_url": image["image_url"],
                            "image_number": image["image_number"],
                            "width": image["width"],
                            "height": image["height"],
                        },
                    )
                )
                chunk_number += 1

            if chunk_number == 1:
                pages_data.append(
                    _make_chunk(
                        "This page has no extractable text. It may be scanned or image-only.",
                        page_index,
                        "page-note",
                        chunk_number,
                    )
                )

    return pages_data
