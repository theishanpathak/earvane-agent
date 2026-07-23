import base64
import httpx
import time

from earvane.config import settings
from earvane.storage.queries import get_or_create_artist

TOKEN_URL="https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"


def get_access_token() -> str:
    """Fetch a Client Credentials token from Spotify."""
    credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    response = httpx.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
    )

    response.raise_for_status()
    return response.json()["access_token"]

def _get_with_retry(url: str, headers: dict, params: dict | None = None) -> httpx.Response:
    """GET a url, transparently retrying once on a 429."""
    response = httpx.get(url, headers=headers, params=params)

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 1))
        print(f"Rate limited, waiting {retry_after}s...")
        time.sleep(retry_after)
        response = httpx.get(url, headers=headers, params=params)
    
    response.raise_for_status()
    return response



def search_recent_tracks(token: str, year: int, max_results: int = 30) -> list[dict]:
    """Search for tracks tagged with the given release year, paginating via offset."""
    headers = {"Authorization": f"Bearer {token}"}
    tracks = []
    offset = 0
    page_size = 10

    while len(tracks) < max_results:
        params = {
            "q": f"year:{year}",
            "type": "track",
            "limit": page_size,
            "offset": offset,
        }

        response = _get_with_retry(SEARCH_URL, headers, params)
        items = response.json()["tracks"]["items"]

        if not items:
            break

        tracks.extend(items)
        offset+=page_size

    return tracks[:max_results]



def extract_catalog_signals(tracks: list[dict]) -> list[dict]:
    """Flatten raw Spotify track results into the minimal catalog fields."""
    signals = []
    for track in tracks:
        for artist in track["artists"]:
            signals.append({
                "artist_id": artist["id"],
                "artist_name": artist["name"],
                "track_name": track["name"],
                "album_name": track["album"]["name"],
                "release_date": track["album"]["release_date"],
            })
    return signals




if __name__ == "__main__":
    token = get_access_token()
    tracks = search_recent_tracks(token, year=2026, max_results=30)
    signals = extract_catalog_signals(tracks)

    print(f"Found {len(tracks)} tracks, {len(signals)} artist-track catalog signals\n")
    for s in signals:
        # print(f"{s['artist_name']} — {s['track_name']} ({s['release_date']})")
        artist_id = get_or_create_artist(s['artist_name'], spotify_id=s['artist_id'])
        print(f"{s['artist_name']} — artist_id: {artist_id}")