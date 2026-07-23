from pydantic import BaseModel

class SignalRecord(BaseModel):
    """One raw signal row, loaded from Postgres into graph state."""
    source: str          # 'youtube' | 'deezer' | etc.
    metric_name: str     # 'view_count' | 'nb_fan' | 'subscriber_count'
    value: float
    collected_at: str    # ISO timestamp string

class ArtistState(BaseModel):
    """The full state passed between nodes for one artist's graph run."""
    artist_id: int
    artist_name: str

    signals: list[SignalRecord] = []       # filled by Signal Collector
    grounding_text: list[str] = []         # filled by Signal Collector

    velocity: dict[str, float] = {}        # filled by Relevance Scorer — one entry per metric
    novelty_score: float | None = None     # filled by Relevance Scorer — LLM judgment
    novelty_reasoning: str | None = None   # filled by Relevance Scorer — LLM's explanation