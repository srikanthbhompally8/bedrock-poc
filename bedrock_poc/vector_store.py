"""In-memory vector store for RAG with semantic search."""

from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100


class Document:
    """A text chunk with its metadata and embedding."""

    def __init__(self, text: str, chunk_id: int, source: str = ""):
        self.text = text
        self.chunk_id = chunk_id
        self.source = source
        self.embedding: Optional[list[float]] = None

    def __repr__(self):
        return f"Document(chunk_id={self.chunk_id}, len={len(self.text)}, has_embedding={self.embedding is not None})"


class DocumentStore:
    """In-memory vector store with semantic search via cosine similarity."""

    def __init__(self):
        self.documents: list[Document] = []
        self._embedding_cache: dict[int, list[float]] = {}

    def add_documents(self, text: str, source: str = "document") -> int:
        """Chunk a document and add it to the store.

        Args:
            text: The full document text.
            source: Optional source identifier (e.g., filename).

        Returns:
            Number of chunks created.
        """
        if not text or not text.strip():
            return 0

        chunks = self._chunk_text(text)
        log.info("Adding %d chunks from source '%s'", len(chunks), source)

        for i, chunk_text in enumerate(chunks):
            doc = Document(chunk_text, chunk_id=len(self.documents), source=source)
            self.documents.append(doc)

        return len(chunks)

    def set_embeddings(self, embeddings: list[list[float]]) -> None:
        """Set embeddings for all documents in order.

        Args:
            embeddings: List of embedding vectors, one per document.
        """
        if len(embeddings) != len(self.documents):
            raise ValueError(
                f"Expected {len(self.documents)} embeddings, got {len(embeddings)}"
            )

        for doc, embedding in zip(self.documents, embeddings):
            doc.embedding = embedding
            self._embedding_cache[doc.chunk_id] = embedding

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[Document]:
        """Find the most similar documents using cosine similarity.

        Args:
            query_embedding: The embedding vector for the query.
            top_k: Number of top results to return.

        Returns:
            List of Document objects, ranked by similarity (highest first).
        """
        if not self.documents:
            return []

        # Verify all documents have embeddings
        if any(doc.embedding is None for doc in self.documents):
            log.warning("Not all documents have embeddings; search may be incomplete")

        # Compute cosine similarity with each document
        scores = []
        for doc in self.documents:
            if doc.embedding is None:
                scores.append(0.0)
            else:
                sim = self._cosine_similarity(query_embedding, doc.embedding)
                scores.append(sim)

        # Sort by score descending, take top_k
        ranked = sorted(
            zip(self.documents, scores), key=lambda x: x[1], reverse=True
        )
        return [doc for doc, _ in ranked[:top_k]]

    def get_all_chunks_for_embedding(self) -> list[str]:
        """Get all document chunks as a list, for batch embedding.

        Returns:
            List of document texts.
        """
        return [doc.text for doc in self.documents]

    def clear(self) -> None:
        """Clear all documents from the store."""
        self.documents.clear()
        self._embedding_cache.clear()

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        """Split text into overlapping chunks.

        Args:
            text: The text to chunk.
            chunk_size: Target size of each chunk in characters.
            overlap: Number of overlapping characters between chunks.

        Returns:
            List of text chunks.
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Calculate end position
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])

            # If we've reached the end, we're done
            if end >= len(text):
                break

            # Calculate next start position with overlap
            next_start = end - overlap

            # Ensure we make progress (avoid infinite loop)
            if next_start <= start:
                next_start = start + max(1, chunk_size // 2)

            start = next_start

        return chunks if chunks else [text]

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Cosine similarity score between -1 and 1.
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)
