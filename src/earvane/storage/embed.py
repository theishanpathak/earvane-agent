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



def content_already_embedded(artist_id: int, source: str, content: str) -> bool:
    """Check if this exact chunk was already embedded for this artist,
    to avoid paying for and storing duplicate embeddings."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM embeddings
                WHERE artist_id = %s AND source = %s AND content = %s
                LIMIT 1
                """,
                (artist_id, source, content),
            )
            return cur.fetchone() is not None

        

def insert_embedding(artist_id: int, source: str, content: str) -> None:
    """Embed a piece of grounding text and store it, linked to an artist.
    Skips if this exact content was already embedded — avoids duplicate
    rows and wasted OpenAI calls on repeat ingestion runs."""
    if content_already_embedded(artist_id, source, content):
        print(f"  [embed] Skipping duplicate content for artist_id={artist_id}")
        return
    
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

def search_similar_for_artist(artist_id: int, query: str, limit: int = 5) -> list[dict]:
    """Like search_similar, but scoped to one artist's chunks only —
    used by the RAG Retriever node during a graph run."""
    query_vector = embed_text(query)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source, content, embedding <=> %s::vector AS distance
                FROM embeddings
                WHERE artist_id = %s
                ORDER BY distance
                LIMIT %s
                """,
                (query_vector, artist_id, limit),
            )
            rows = cur.fetchall()
    return [{"source": r[0], "content": r[1], "distance": r[2]} for r in rows]
