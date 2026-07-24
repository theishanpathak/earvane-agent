from openai import OpenAI
from pydantic import BaseModel

from earvane.config import settings
from earvane.agent.state import ArtistState

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class RankedChunk(BaseModel):
    chunk_index: int
    relevance_score: float

class RerankResult(BaseModel):
    rankings: list[RankedChunk]


def rerank_chunks(artist_name: str, chunks: list[str]) -> list[str]:
    """Re-score retrieved chunks by actual relevance to the artist's current
    activity, using an LLM instead of raw cosine distance. Returns chunks
    sorted most-to-least relevant."""

    if len(chunks) <= 1:
        return chunks  # nothing to rerank

    numbered = "\n".join(f"{i}: {c}" for i, c in enumerate(chunks))
    prompt = f"""Rate how relevant each numbered chunk below is to describing
{artist_name}'s current notable activity, on a 0.0-1.0 scale.

Chunks:
{numbered}

Return a relevance_score for every chunk_index listed."""

    completion = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=RerankResult,
        temperature=0,
    )

    rankings = completion.choices[0].message.parsed.rankings
    sorted_rankings = sorted(rankings, key=lambda r: r.relevance_score, reverse=True)

    return [chunks[r.chunk_index] for r in sorted_rankings if r.chunk_index < len(chunks)]

def reranker_node(state: ArtistState) -> dict:
    """Rerank the RAG Retriever's chunks by actual relevance, sharpening
    the shortlist before the Synthesizer writes from it."""
    reranked = rerank_chunks(state.artist_name, state.retrieved_chunks)
    return {"retrieved_chunks": reranked}