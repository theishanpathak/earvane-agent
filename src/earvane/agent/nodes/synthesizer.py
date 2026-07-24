from openai import OpenAI
from pydantic import BaseModel

from earvane.config import settings
from earvane.agent.state import ArtistState

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class SynthesizedBrief(BaseModel):
    headline: str
    brief: str
    citations: list[int]       # indices into retrieved_chunks actually used as evidence
    sufficient_evidence: bool  # false if chunks didn't support a real brief

def build_synthesis_prompt(state: ArtistState) -> str:
    if not state.retrieved_chunks:
        chunks_text = "No grounding chunks were retrieved."
    else:
        chunks_text = "\n".join(f"{i}: {c}" for i, c in enumerate(state.retrieved_chunks))

    velocity_text = "\n".join(f"{k}: {v:+.2%}" for k, v in state.velocity.items()) or "No velocity data available."

    return f"""You are writing a short trend brief about {state.artist_name} for a music trend website.

STRICT RULES:
- Use ONLY the numbered chunks below as your source of factual claims. Do not use outside knowledge.
- Every factual claim in the brief must be traceable to at least one chunk. List the indices of chunks you actually used in "citations".
- If the chunks do not contain enough real, specific information to support a genuine trend brief, set sufficient_evidence to false. In that case, the headline must also reflect the lack of evidence (e.g. "Not enough data to report on {state.artist_name}") — do not write a confident or trend-implying headline when sufficient_evidence is false.
- Do not invent details to fill gaps, in either the headline or the brief.

Numbered chunks:
{chunks_text}

Velocity signals:
{velocity_text}

Novelty score: {state.novelty_score} — {state.novelty_reasoning or 'no reasoning available'}

Write a headline and a 2-3 sentence brief."""


def synthesize_brief(state: ArtistState) -> SynthesizedBrief:
    prompt = build_synthesis_prompt(state)

    completion = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=SynthesizedBrief,
        temperature=0,
    )
    return completion.choices[0].message.parsed

def synthesizer_node(state: ArtistState) -> dict:
    """Write a grounded, cited trend brief from retrieved chunks + velocity/novelty.
    Must explicitly flag when evidence is insufficient rather than fabricate."""
    result = synthesize_brief(state)
    return {
        "brief_headline": result.headline,
        "brief_content": result.brief,
        "citations": result.citations,
        "sufficient_evidence": result.sufficient_evidence,
    }