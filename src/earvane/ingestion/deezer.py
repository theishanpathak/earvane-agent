import httpx

SEARCH_URL = "https://api.deezer.com/search/artist"

def search_artist(artist_name: str) -> dict | None:
    """Search Deezer for an artist by name. No auth required.
    Returns the highest-fan-count match to avoid picking duplicate/impersonator
    profiles, or None if no results found."""
    params = {"q": artist_name}
    response = httpx.get(SEARCH_URL, params=params)
    response.raise_for_status()

    results = response.json()["data"]
    if not results:
        return None

    return max(results, key=lambda artist: artist["nb_fan"])


def extract_fan_signal(artist_name: str) -> dict | None:
    """Return a flattened fan-count signal for a given artist, or None if not found."""
    artist = search_artist(artist_name)
    if artist is None:
        return None

    return {
        "artist_name": artist["name"],
        "deezer_id": artist["id"],
        "nb_fan": artist["nb_fan"],
        "deezer_url": artist["link"],
    }



def collect_fan_signals(artist_names: list[str]) -> list[dict]:
    """Given a list of artist names, return fan-count signals for each match found."""
    signals = []
    for artist_name in artist_names:
        signal = extract_fan_signal(artist_name)
        if signal is None:
            print(f"No Deezer match for {artist_name}, skipping")
            continue
        signals.append(signal)
    return signals


if __name__ == "__main__":
    test_artists = ["Ariana Grande", "Ella Langley", "STELLA LEFTY"]

    signals = collect_fan_signals(test_artists)
    print(f"Collected {len(signals)} fan signals\n")

    for s in signals:
        print(f"{s['artist_name']} — {s['nb_fan']:,} fans")