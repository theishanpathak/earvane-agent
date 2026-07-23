import httpx

from earvane.config import settings
from earvane.formatting import format_youtube_chunk
from earvane.storage.queries import insert_signal, get_or_create_artist
from earvane.storage.embed import insert_embedding

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"


FAN_CHANNEL_KEYWORDS = ["fan", "fans", "lover", "edits", "tribute", "cover"]


def find_artist_channel(artist_name: str) -> str | None:
    """Search for the artist's channel among top candidates. Filters out
    obvious fan/tribute channels by name, then picks the highest-subscriber
    match among what's left — falling back to a '- Topic' auto-generated
    channel if that's the only legitimate option."""
    params = {
        "key": settings.YOUTUBE_API_KEY,
        "q": artist_name,
        "part": "snippet",
        "type": "channel",
        "maxResults": 5,
    }
    response = httpx.get(SEARCH_URL, params=params)
    response.raise_for_status()
    candidates = response.json()["items"]

    if not candidates:
        return None

    # filter out obvious fan/tribute channels by title
    legit_candidates = [
        c for c in candidates
        if not any(kw in c["snippet"]["title"].lower() for kw in FAN_CHANNEL_KEYWORDS)
    ]

    if not legit_candidates:
        return None  # nothing legitimate found at all

    candidate_ids = [c["snippet"]["channelId"] for c in legit_candidates]
    stats = get_channel_stats(candidate_ids)

    if not stats:
        return candidate_ids[0]

    best = max(stats, key=lambda s: int(s["statistics"].get("subscriberCount", 0)))
    return best["id"]

def get_channel_uploads(channel_id: str, max_results: int = 5) -> list[dict]:
    """Search within a specific channel's own uploads, preferring the Music
    category filter but falling back to unfiltered if that returns nothing —
    some smaller/indie channels don't have uploads categorized as Music."""
    base_params = {
        "key": settings.YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "type": "video",
        "order": "date",
        "maxResults": min(max_results, 50),
    }

    params_with_category = {**base_params, "videoCategoryId": "10"}
    response = httpx.get(SEARCH_URL, params=params_with_category)
    response.raise_for_status()
    items = response.json()["items"]

    if items:
        return items

    # fallback: no Music-categorized results, try without the category filter
    response = httpx.get(SEARCH_URL, params=base_params)
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
    """For each artist, find their real channel, then pull only that channel's
    own uploads — avoids blind-keyword spam entirely. Costs 200 quota units
    per artist (channel lookup + upload lookup)"""
    all_videos = []
    artist_by_video_id = {}

    for artist_name in artist_names:
        channel_id = find_artist_channel(artist_name)
        if channel_id is None:
            print(f"No channel found for {artist_name}, skipping")
            continue

        uploads = get_channel_uploads(channel_id, max_results=videos_per_artist)
        for v in uploads:
            video_id = v["id"]["videoId"]
            artist_by_video_id[video_id] = artist_name
            all_videos.append(v)

    video_ids = [v["id"]["videoId"] for v in all_videos]
    channel_ids = [v["snippet"]["channelId"] for v in all_videos]

    video_stats = get_video_stats(video_ids)
    channel_stats = get_channel_stats(channel_ids)

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
    test_artists = ["Ariana Grande", "Ella Langley", "STELLA LEFTY"]

    signals = collect_artist_signals(test_artists, videos_per_artist=3)
    print(f"Collected {len(signals)} signals\n")

    for s in signals:
        artist_id = get_or_create_artist(canonical_name=s['artist_name'], youtube_channel_id=s['channel_id'])
        insert_signal(artist_id, "youtube", "view_count", s['view_count'], source_ref=s['video_id'])
        insert_signal(artist_id, "youtube", "subscriber_count", s['subscriber_count'], source_ref=s['channel_id'])
        content = format_youtube_chunk(s)
        insert_embedding(artist_id, "youtube", content)
        print(f"Succesfullly inserted the emedding for {content}")
