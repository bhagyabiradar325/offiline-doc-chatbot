from vector_store import OfflineVectorStore, SearchResult


def _shorten(text: str, limit: int = 700) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _unique_pages(results: list[SearchResult], limit: int = 5) -> list[int]:
    pages = []
    for result in results:
        if result.score <= 0:
            continue
        if result.page not in pages:
            pages.append(result.page)
        if len(pages) == limit:
            break
    return pages


def _source_payload(page: int, kind: str, content: str, extra: dict, score: float = 0.0) -> dict:
    return {
        "page": page,
        "kind": kind,
        "snippet": _shorten(content, 260),
        "content": content,
        "extra": extra,
        "score": score,
    }


def _result_payload(result: SearchResult) -> dict:
    return _source_payload(
        result.page,
        result.kind,
        result.content,
        result.extra,
        result.score,
    )


def _document_payload(document: dict) -> dict:
    return _source_payload(
        int(document["page"]),
        str(document["kind"]),
        str(document["content"]),
        dict(document.get("extra", {})),
    )


def _build_answer(text_results: list[SearchResult], pages: list[int]) -> str:
    if not text_results:
        return "I could not find matching text in the uploaded PDF."

    best_texts = []
    seen = set()
    for result in text_results:
        if result.score <= 0:
            continue
        normalized = " ".join(result.content.split())
        if normalized[:120] in seen:
            continue
        seen.add(normalized[:120])
        best_texts.append(f"Page {result.page}: {_shorten(result.content)}")
        if len(best_texts) == 3:
            break

    if not best_texts:
        return "I could not find matching text in the uploaded PDF."

    page_text = ", ".join(str(page) for page in pages)
    return "\n\n".join(best_texts) + f"\n\nSource page(s): {page_text}. Click a page number below to open that exact PDF page."


def answer_question(query: str, vector_db: OfflineVectorStore) -> dict:
    text_results = vector_db.search(query, k=8, kinds={"text"})
    table_results = vector_db.search(query, k=5, kinds={"table"})
    pages = _unique_pages(text_results, limit=5)

    if not pages:
        pages = _unique_pages(table_results, limit=5)

    sources = []
    seen = set()

    for result in text_results[:5]:
        if result.score <= 0:
            continue
        key = (result.page, result.kind, result.content[:100])
        if key not in seen:
            seen.add(key)
            sources.append(_result_payload(result))

    for result in table_results:
        if result.score <= 0:
            continue
        if result.page not in pages:
            pages.append(result.page)
        key = (result.page, result.kind, result.content[:100])
        if key not in seen:
            seen.add(key)
            sources.append(_result_payload(result))

    for document in vector_db.page_items(pages, kinds={"table", "image"}):
        key = (document["page"], document["kind"], document["content"][:100])
        if key in seen:
            continue
        seen.add(key)
        sources.append(_document_payload(document))

    return {
        "question": query,
        "answer": _build_answer(text_results, pages),
        "sources": sources,
    }
