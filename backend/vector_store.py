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

    def search(self, query: str, k: int = 5) -> list[SearchResult]:
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        ranked_indexes = scores.argsort()[::-1][:k]

        results = []
        for index in ranked_indexes:
            document = self.documents[int(index)]
            results.append(
                SearchResult(
                    content=document["content"],
                    page=int(document["page"]),
                    kind=str(document["kind"]),
                    score=float(scores[index]),
                    extra=dict(document.get("extra", {})),
                )
            )

        return results


def create_vector_store(pages: list[dict[str, Any]]) -> OfflineVectorStore:
    if not pages:
        raise ValueError("No readable PDF content was found.")

    return OfflineVectorStore(pages)
