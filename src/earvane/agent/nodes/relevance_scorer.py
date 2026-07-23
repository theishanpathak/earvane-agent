from collections import defaultdict
from earvane.config import settings
from earvane.agent.state import ArtistState, SignalRecord
from openai import OpenAI
from pydantic import BaseModel


client = OpenAI(api_key=settings.OPENAI_API_KEY)

class NoveltyJudgment(BaseModel):
    score: float
    reasoning: str


def group_by_metric(signals: list[SignalRecord]) -> dict[str, list[SignalRecord]]:
    """Group raw signal records by metric_name, so velocity can be computed
    separately per metric (view_count, nb_fan, subscriber_count, etc.)."""

    grouped = defaultdict(list)
    for s in signals:
        grouped[s.metric_name].append(s)
    return grouped


def compute_velocity(signals: list[SignalRecord]) -> dict[str, float]:
    """Compute percent change between the two most recent snapshots, per metric.
    Returns an empty dict if there isn't enough history yet."""

    grouped = group_by_metric(signals)
    velocity = {}
    for metric_name, records in grouped.items():
        sorted_records = sorted(records, key=lambda r: r.collected_at, reverse=True)
        if len(sorted_records) < 2:
            continue

        newest, previous = sorted_records[0], sorted_records[1]
        if previous.value == 0:
            continue

        pct_change = (newest.value - previous.value) / previous.value
        velocity[metric_name] = pct_change

    return velocity

def build_novelty_prompt(state: ArtistState) -> str:
    context = "\n".join(state.grounding_text) if state.grounding_text else "No grounding text available."
    velocity_lines = "\n".join(f"{k}: {v:+.2%}" for k, v in state.velocity.items()) or "No velocity data yet (insufficient history)."

    return f"""You are evaluating whether an artist's recent activity is genuinely novel or noteworthy.

Grounding context (recent releases, videos, metadata):
{context}

Recent growth signals:
{velocity_lines}

Rate novelty from 0.0 (nothing notable) to 1.0 (genuinely striking/new), and briefly explain why in one sentence.
Respond in this exact format:
SCORE: <number>
REASON: <one sentence>"""

def score_novelty(state: ArtistState) -> tuple[float, str]:
    """Call the LLM to judge novelty from grounding text + velocity context,
    using structured output so the response is guaranteed to match the schema."""

    prompt = build_novelty_prompt(state)

    try:
        completion = client.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format=NoveltyJudgment,
            temperature=0,
        )
    except Exception as e:
        print(f"Novelty scoring failed for {state.artist_name}: {e}")
        return 0.0, "Scoring unavailable due to an API error."
    
    result = completion.choices[0].message.parsed
    return result.score, result.reasoning


def relevance_scorer_node(state: ArtistState) -> dict:
    """Compute per-metric velocity from state.signals, then get an LLM
    novelty judgment informed by both the grounding text and velocity."""
    velocity = compute_velocity(state.signals)

     # temporarily merge velocity into state so the prompt builder can see it
    state_with_velocity = state.model_copy(update={"velocity": velocity})
    novelty_score, novelty_reasoning = score_novelty(state_with_velocity)

    return {
        "velocity": velocity,
        "novelty_score": novelty_score,
        "novelty_reasoning": novelty_reasoning,
    }

