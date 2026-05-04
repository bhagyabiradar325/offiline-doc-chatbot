from collections import defaultdict

from vector_store import OfflineVectorStore, SearchResult


def _shorten(text: str, limit: int = 380) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _build_answer(query: str, results: list[SearchResult]) -> str:
    if not results:
        return "I could not find this information in the uploaded PDF."

    pages = sorted({result.page for result in results})
    grouped_by_page = defaultdict(list)
    for result in results:
        grouped_by_page[result.page].append(result)

    page_text = ", ".join(str(page) for page in pages)
    lines = [
        f"Based on the uploaded PDF, the most relevant information is on page(s) {page_text}.",
        "",
    ]

    for page in pages:
        lines.append(f"Page {page}:")
        for result in grouped_by_page[page][:2]:
            label = result.kind.capitalize()
            lines.append(f"- {label}: {_shorten(result.content)}")
        lines.append("")

    lines.append(
        "Note: this app is fully offline and uses retrieval from the PDF. For scanned images, use OCR before upload if you need exact text inside images."
    )
    return "\n".join(lines).strip()


def answer_question(query: str, vector_db: OfflineVectorStore) -> dict:
    results = vector_db.search(query, k=5)

    return {
        "question": query,
        "answer": _build_answer(query, results),
        "sources": [
            {
                "page": result.page,
                "kind": result.kind,
                "snippet": _shorten(result.content, 260),
                "content": result.content,
                "extra": result.extra,
                "score": result.score,
            }
            for result in results
        ],
    }
