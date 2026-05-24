from dataclasses import dataclass
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class SearchResult:
    content: str
    page: int
    kind: str
    score: float
    extra: dict[str, Any]


class OfflineVectorStore:
    def __init__(self, documents: list[dict[str, Any]]):
        self.documents = documents
        self.texts = [document["content"] for document in documents]
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=50000,
        )
        self.matrix = self.vectorizer.fit_transform(self.texts)

    def search(
        self,
        query: str,
        k: int = 5,
        kinds: set[str] | None = None,
    ) -> list[SearchResult]:
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        adjusted_scores = scores.copy()
        query_text = query.lower().strip()

        for index, text in enumerate(self.texts):
            document = self.documents[index]
            text_lower = text.lower()
            if kinds and document["kind"] not in kinds:
                adjusted_scores[index] = -1.0
                continue
            if query_text and query_text in text_lower:
                adjusted_scores[index] += 0.35
            if "table of contents" in text_lower:
                adjusted_scores[index] *= 0.2

        ranked_indexes = adjusted_scores.argsort()[::-1][:k]

        results = []
        for index in ranked_indexes:
            document = self.documents[int(index)]
            results.append(
                SearchResult(
                    content=document["content"],
                    page=int(document["page"]),
                    kind=str(document["kind"]),
                    score=float(adjusted_scores[index]),
                    extra=dict(document.get("extra", {})),
                )
            )

        return results

    def page_items(self, pages: list[int], kinds: set[str] | None = None) -> list[dict[str, Any]]:
        page_set = set(pages)
        return [
            document
            for document in self.documents
            if int(document["page"]) in page_set and (kinds is None or document["kind"] in kinds)
        ]


def create_vector_store(pages: list[dict[str, Any]]) -> OfflineVectorStore:
    if not pages:
        raise ValueError("No readable PDF content was found.")

    return OfflineVectorStore(pages)
