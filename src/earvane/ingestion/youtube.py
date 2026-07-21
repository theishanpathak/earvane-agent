import httpx

from earvane.config import settings

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"


def search_artist_videos(artist_name: str, max_results: int = 5) -> list[dict]:
    """Search for an artist's recent videos on their own official content.
    Costs 100 quota units per call — one call per artist, so keep artist
    lists reasonably sized per run (quota budget, not a code limit)."""
    params = {
        "key": settings.YOUTUBE_API_KEY,
        "q": artist_name,
        "part": "snippet",
        "type": "video",
        "order": "date",
        "maxResults": min(max_results, 50),
    }
    response = httpx.get(SEARCH_URL, params=params)
    response.raise_for_status()
    return response.json()["items"]



def get_video_stats(video_ids: list[str]) -> list[dict]:
    """Batch-fetch view counts for up to 50 videos in a single call."""

    if not video_ids:
        return []
    
    params = {
        "key": settings.YOUTUBE_API_KEY,
        "id": ",".join(video_ids[:50]),  # API hard cap per call
        "part": "statistics",
    }

    response = httpx.get(VIDEOS_URL, params=params)
    response.raise_for_status()
    return response.json()["items"]


def get_channel_stats(channel_ids: list[str]) -> list[dict]:
    """Batch-fetch subscriber counts for up to 50 channels in a single call."""

    if not channel_ids:
        return []
    
    params = {
        "key": settings.YOUTUBE_API_KEY,
        "id": ",".join(set(channel_ids[:50])),  # dedupe + cap
        "part": "statistics",
    }
    response = httpx.get(CHANNELS_URL, params=params)
    response.raise_for_status()
    return response.json()["items"]


def collect_artist_signals(artist_names: list[str], videos_per_artist: int = 5) -> list[dict]:
    """Given a list of artist names (e.g. from Spotify catalog data), search each
    one individually and return per-video signal rows with view/subscriber counts."""
    all_videos = []
    artist_by_video_id = {}

    for artist_name in artist_names:
        videos = search_artist_videos(artist_name, max_results=videos_per_artist)
        for v in videos:
            video_id = v["id"]["videoId"]
            artist_by_video_id[video_id] = artist_name
            all_videos.append(v)

    video_ids = [v["id"]["videoId"] for v in all_videos]
    channel_ids = [v["snippet"]["channelId"] for v in all_videos]

    video_stats = get_video_stats(video_ids)
    channel_stats = get_channel_stats(channel_ids)

    # index stats by id so we can look them up regardless of response order
    view_counts = {s["id"]: s["statistics"].get("viewCount", "n/a") for s in video_stats}
    sub_counts = {s["id"]: s["statistics"].get("subscriberCount", "n/a") for s in channel_stats}

    signals = []
    for v in all_videos:
        video_id = v["id"]["videoId"]
        channel_id = v["snippet"]["channelId"]
        signals.append({
            "artist_name": artist_by_video_id[video_id],
            "video_title": v["snippet"]["title"],
            "video_id": video_id,
            "channel_id": channel_id,
            "view_count": view_counts.get(video_id, "n/a"),
            "subscriber_count": sub_counts.get(channel_id, "n/a"),
            "published_at": v["snippet"]["publishedAt"],
        })

    return signals



if __name__ == "__main__":
    # test seed list — Phase 2+ will wire this to real Spotify catalog output
    test_artists = ["Ariana Grande", "Ella Langley", "STELLA LEFTY"]

    signals = collect_artist_signals(test_artists, videos_per_artist=3)
    print(f"Collected {len(signals)} signals\n")

    for s in signals:
        print(f"[{s['artist_name']}] {s['video_title']}")
        print(f"    views: {s['view_count']}, subscribers: {s['subscriber_count']}\n")