import base64
import httpx

from earvane.config import settings

TOKEN_URL="https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"
ARTIST_URL = "https://api.spotify.com/v1/artists/{artist_id}"


def get_access_token() -> str:
    """Fetch a Client Credentials token from Spotify."""
    credentials = f"{settings.SPOTIFY_CLIENT_ID}: {settings.SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64decode(credentials.encode()).decode()

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


if __name__ == "__main__":
    token = get_access_token()
    print(token)