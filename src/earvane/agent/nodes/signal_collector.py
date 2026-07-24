from earvane.agent.state import SignalRecord, ArtistState
from earvane.storage.queries import get_recent_signals, get_recent_embeddings_text

def signal_collector_node(state: ArtistState) -> dict:
    """Load this artist's recent raw signals and grounding text from Postgres
    into state. Pure retrieval — no computation, no writes."""
    raw_signals = get_recent_signals(state.artist_id)
    grounding = get_recent_embeddings_text(state.artist_id)

    return {
        "signals": [SignalRecord(**s) for s in raw_signals],
        "grounding_text": grounding,
    }
