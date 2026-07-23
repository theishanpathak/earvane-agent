import httpx

from earvane.formatting import format_genius_chunk
from earvane.config import settings
from earvane.storage.queries import get_or_create_artist
from earvane.storage.embed import insert_embedding

SEARCH_URL = "https://api.genius.com/search"


def search_song(query: str) -> list[dict]:
    """Search Genius for songs matching a query (typically 'artist track').
    Returns metadata only — title, artist, release info — never lyrics.
    Returns an empty list if nothing matches."""

    headers = {"Authorization": f"Bearer {settings.GENIUS_ACCESS_TOKEN}"}
    params = {"q": query}

    response = httpx.get(SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()

    hits = response.json()["response"]["hits"]
    return hits


def extract_song_metadata(hits: list[dict], expected_artist: str) -> list[dict]:
    """Flatten raw Genius search hits into metadata fields, filtering out
    results whose primary_artist doesn't actually match who we searched for —
    Genius's search isn't strictly scoped to the query artist and can return
    unrelated editorial/literary content."""
    signals = []
    expected_lower = expected_artist.strip().lower()

    for hit in hits:
        result = hit["result"]
        actual_artist = result["primary_artist"]["name"].strip().lower()

        if expected_lower not in actual_artist and actual_artist not in expected_lower:
            continue  # not actually a match, skip silently

        signals.append({
            "song_title": result["title"],
            "artist_name": result["primary_artist"]["name"],
            "genius_artist_id": result["primary_artist"]["id"],
            "release_date": result.get("release_date_for_display", "unknown"),
            "genius_url": result["url"],
        })
    return signals


def collect_artist_metadata(artist_track_pairs: list[tuple[str, str]]) -> list[dict]:
    """Given (artist_name, track_name) pairs, search Genius for each and
    return flattened, artist-verified metadata rows."""
    all_signals = []
    for artist_name, track_name in artist_track_pairs:
        query = f"{artist_name} {track_name}"
        hits = search_song(query)
        if not hits:
            continue
        signals = extract_song_metadata(hits[:3], expected_artist=artist_name)  # check top 3, not just 1
        all_signals.extend(signals[:1])  # keep only the first verified match
    return all_signals


if __name__ == "__main__":
    test_pairs = [
        ("Ariana Grande", "kiss me like you know this is goodbye"),
        ("Ella Langley", "Choosin' Texas"),
        ("STELLA LEFTY", "Good At Leaving"),
    ]

    signals = collect_artist_metadata(test_pairs)
    print(f"Collected {len(signals)} metadata signals\n")

    for s in signals:
        artist_id = get_or_create_artist(s['artist_name'], genius_id=s['genius_artist_id'])
        print(f"{s['artist_name']} — artist_id: {artist_id}, genius_id: {s['genius_artist_id']}")
        content = format_genius_chunk(s)
        insert_embedding(artist_id, "genius", content)
        print(f"Succesfullly inserted the emedding for {content}")