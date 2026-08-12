"""Deterministic managed-style and explicit-vector retrieval adapters."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
from typing import Iterable

from .domain import INTERNAL
from .domain import PUBLIC
from .domain import SourceDocument


TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "the",
    "to",
    "what",
}
TOKEN_ALIASES = {
    "returned": "return",
    "returns": "return",
}


@dataclass(frozen=True)
class Chunk:
    """Indexable unit with provenance retained beside its text."""

    chunk_id: str
    doc_id: str
    version: int
    title: str
    uri: str
    visibility: str
    text: str


@dataclass(frozen=True)
class RetrievalHit:
    """Normalized result shared by managed and explicit adapters."""

    chunk_id: str
    doc_id: str
    version: int
    title: str
    uri: str
    visibility: str
    text: str
    score: float

    def as_dict(self, *, include_provenance: bool = True) -> dict[str, object]:
        result: dict[str, object] = {"text": self.text}
        if include_provenance:
            result.update(
                {
                    "chunk_id": self.chunk_id,
                    "doc_id": self.doc_id,
                    "version": self.version,
                    "title": self.title,
                    "uri": self.uri,
                    "visibility": self.visibility,
                    "score": round(self.score, 6),
                }
            )
        return result


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(
        TOKEN_ALIASES.get(token, token)
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOPWORDS
    )


def sparse_embedding(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(token, 0) for token, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot / (left_norm * right_norm)


def chunk_document(
    document: SourceDocument,
    *,
    max_words: int,
    overlap_words: int,
) -> list[Chunk]:
    """Create deterministic word chunks and stable versioned IDs."""

    words = document.text.split()
    if max_words <= 0:
        raise ValueError("max_words must be positive")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be in [0, max_words)")

    step = max_words - overlap_words
    chunks: list[Chunk] = []
    for index, start in enumerate(range(0, len(words), step)):
        text = " ".join(words[start : start + max_words])
        if not text:
            continue
        chunks.append(
            Chunk(
                chunk_id=f"{document.doc_id}:v{document.version}:c{index}",
                doc_id=document.doc_id,
                version=document.version,
                title=document.title,
                uri=document.uri,
                visibility=document.visibility,
                text=text,
            )
        )
        if start + max_words >= len(words):
            break
    return chunks


def _visible(chunk: Chunk, principal_role: str) -> bool:
    return chunk.visibility == PUBLIC or principal_role == INTERNAL


def _rank(
    chunks: Iterable[Chunk],
    *,
    query: str,
    principal_role: str,
    top_k: int,
    enforce_acl: bool,
    minimum_score: float,
) -> list[RetrievalHit]:
    query_vector = sparse_embedding(query)
    query_terms = set(query_vector)
    hits: list[RetrievalHit] = []
    for chunk in chunks:
        if enforce_acl and not _visible(chunk, principal_role):
            continue
        chunk_vector = sparse_embedding(f"{chunk.title} {chunk.text}")
        if len(query_terms & set(chunk_vector)) < min(2, len(query_terms)):
            continue
        score = cosine_similarity(
            query_vector,
            chunk_vector,
        )
        if score < minimum_score:
            continue
        hits.append(
            RetrievalHit(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                version=chunk.version,
                title=chunk.title,
                uri=chunk.uri,
                visibility=chunk.visibility,
                text=chunk.text,
                score=score,
            )
        )
    hits.sort(
        key=lambda hit: (
            -hit.score,
            hit.doc_id,
            -hit.version,
            hit.chunk_id,
        )
    )
    return hits[:top_k]


class ManagedSearchSimulator:
    """Provider-side connector/index hidden behind native search config."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self.search_calls: list[dict[str, object]] = []

    def sync(self, documents: Iterable[SourceDocument]) -> None:
        latest: dict[str, SourceDocument] = {}
        for document in documents:
            if not document.active:
                continue
            current = latest.get(document.doc_id)
            if current is None or document.version > current.version:
                latest[document.doc_id] = document
        self._chunks = [
            chunk
            for document in sorted(latest.values(), key=lambda item: item.doc_id)
            for chunk in chunk_document(
                document,
                max_words=80,
                overlap_words=0,
            )
        ]

    def search(
        self,
        *,
        query: str,
        principal_role: str,
        top_k: int = 3,
        enforce_acl: bool = True,
    ) -> list[RetrievalHit]:
        self.search_calls.append(
            {
                "query": query,
                "principal_role": principal_role,
                "top_k": top_k,
                "enforce_acl": enforce_acl,
            }
        )
        return _rank(
            self._chunks,
            query=query,
            principal_role=principal_role,
            top_k=top_k,
            enforce_acl=enforce_acl,
            minimum_score=0.2,
        )


class ExplicitVectorIndex:
    """Caller-owned chunks, IDs, versions, ACL and deletion behavior."""

    def __init__(
        self,
        *,
        chunk_words: int = 80,
        overlap_words: int = 0,
    ) -> None:
        self.chunk_words = chunk_words
        self.overlap_words = overlap_words
        self._chunks: dict[str, Chunk] = {}
        self.search_calls: list[dict[str, object]] = []

    @property
    def chunks(self) -> tuple[Chunk, ...]:
        return tuple(
            self._chunks[key]
            for key in sorted(self._chunks)
        )

    def ingest(
        self,
        documents: Iterable[SourceDocument],
        *,
        replace_versions: bool = True,
        delete_missing: bool = True,
    ) -> None:
        incoming = [document for document in documents if document.active]
        incoming_ids = {document.doc_id for document in incoming}
        if delete_missing:
            self._chunks = {
                key: chunk
                for key, chunk in self._chunks.items()
                if chunk.doc_id in incoming_ids
            }

        for document in incoming:
            if replace_versions:
                self._chunks = {
                    key: chunk
                    for key, chunk in self._chunks.items()
                    if chunk.doc_id != document.doc_id
                }
            for chunk in chunk_document(
                document,
                max_words=self.chunk_words,
                overlap_words=self.overlap_words,
            ):
                self._chunks[chunk.chunk_id] = chunk

    def search(
        self,
        *,
        query: str,
        principal_role: str,
        top_k: int = 3,
        enforce_acl: bool = True,
    ) -> list[RetrievalHit]:
        self.search_calls.append(
            {
                "query": query,
                "principal_role": principal_role,
                "top_k": top_k,
                "enforce_acl": enforce_acl,
            }
        )
        return _rank(
            self._chunks.values(),
            query=query,
            principal_role=principal_role,
            top_k=top_k,
            enforce_acl=enforce_acl,
            minimum_score=0.2,
        )
