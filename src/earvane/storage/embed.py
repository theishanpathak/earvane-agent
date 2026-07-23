import httpx

from earvane.config import settings
from earvane.storage.db import get_connection

EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"

def embed_text(text: str) -> list[float]:
    """Get a 1536-dim embedding vector for a piece of text via OpenAI."""
    response = httpx.post(
        EMBEDDINGS_URL,
        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
        json={"model": "text-embedding-3-small", "input": text},
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def insert_embedding(artist_id: int, source: str, content: str) -> None:
    """Embed a piece of grounding text and store it, linked to an artist."""
    vector = embed_text(content)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO embeddings (artist_id, source, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (artist_id, source, content, vector),
            )
            conn.commit()

def search_similar(query: str, limit: int = 5) -> list[dict]:
    """Embed a query and find the most semantically similar stored chunks."""
    query_vector = embed_text(query)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT artist_id, source, content, embedding <=> %s::vector AS distance
                FROM embeddings
                ORDER BY distance
                LIMIT %s
                """,
                (query_vector, limit),
            )
            rows = cur.fetchall()
    return [
        {"artist_id": r[0], "source": r[1], "content": r[2], "distance": r[3]}
        for r in rows
    ]
