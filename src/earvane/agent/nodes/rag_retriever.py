from earvane.agent.state import ArtistState
from earvane.storage.embed import search_similar_for_artist

def rag_retriever_node(state: ArtistState) -> dict:
    """Retrieve this artist's most relevant grounding chunks via cosine
    similarity, replacing the raw dump of all embeddings with a focused,
    ranked shortlist for the Synthesizer to work from."""
    query = f"Recent notable activity and releases from {state.artist_name}"
    results = search_similar_for_artist(state.artist_id, query, limit=5)

    return {"retrieved_chunks": [r["content"] for r in results]}
