import asyncio

from google import genai
from google.genai import types

from app.core.config import settings


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class GeminiEmbeddingService:
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise EmbeddingError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_EMBEDDING_MODEL
        self.dimensions = settings.GEMINI_EMBEDDING_DIMENSIONS
        self.batch_size = settings.GEMINI_EMBEDDING_BATCH_SIZE

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        # FIX for gemini-embedding-2: 
        # Prevent it from combining all chunks into 1 embedding by wrapping each chunk in a nested list.
        batched_contents = [[text] for text in texts]

        response = self.client.models.embed_content(
            model=self.model,
            contents=batched_contents,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.dimensions,
            ),
        )

        if not response.embeddings:
            raise EmbeddingError("Gemini returned no embeddings.")

        vectors = [
            embedding.values
            for embedding in response.embeddings
        ]

        if len(vectors) != len(texts):
            raise EmbeddingError("Gemini returned an unexpected embedding count.")

        for vector in vectors:
            if len(vector) != self.dimensions:
                raise EmbeddingError("Gemini returned an unexpected vector dimension.")

        return vectors

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        sanitized_texts = [text if text.strip() else " " for text in texts]

        results: list[list[float]] = []

        try:
            for start in range(0, len(sanitized_texts), self.batch_size):
                batch = sanitized_texts[start : start + self.batch_size]

                vectors = await asyncio.to_thread(
                    self._embed_batch,
                    batch,
                )

                results.extend(vectors)

            return results

        except Exception as exc:
            raise EmbeddingError("Failed to generate document embeddings.") from exc