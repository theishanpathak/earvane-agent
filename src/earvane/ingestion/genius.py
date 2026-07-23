import httpx

from earvane.config import settings
from earvane.storage.queries import get_or_create_artist

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

def extract_song_metadata(hits: list[dict]) -> list[dict]:
    """Flatten raw Genius search hits into the minimal metadata fields Earvane needs."""
    signals = []
    for hit in hits:
        result = hit["result"]
        signals.append({
            "song_title": result["title"],
            "artist_name": result["primary_artist"]["name"],
            "genius_artist_id": result["primary_artist"]["id"],
            "release_date": result.get("release_date_for_display", "unknown"),
            "genius_url": result["url"],
        })
    return signals

def collect_artist_metadata(artist_track_pairs: list[tuple[str, str]]) -> list[dict]:
    """Given (artist_name, track_name) pairs — typically sourced from Spotify's
    catalog output — search Genius for each and return flattened metadata rows."""
    all_signals = []
    for artist_name, track_name in artist_track_pairs:
        query = f"{artist_name} {track_name}"
        hits = search_song(query)
        if not hits:
            continue  # no match found, skip silently — not every track is on Genius
        signals = extract_song_metadata(hits[:1])  # top match only, avoid noisy duplicates
        all_signals.extend(signals)
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
        