def format_spotify_chunk(s: dict) -> str:
    return f"{s['artist_name']} released the track '{s['track_name']}' on the album '{s['album_name']}', released {s['release_date']}."


def format_youtube_chunk(s: dict) -> str:
    return f"{s['artist_name']} posted the video '{s['video_title']}' on YouTube, published {s['published_at']}."


def format_genius_chunk(s: dict) -> str:
    return f"{s['artist_name']}'s song '{s['song_title']}' was released {s['release_date']}, documented on Genius."