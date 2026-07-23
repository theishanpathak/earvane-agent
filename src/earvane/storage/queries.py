from earvane.storage.db import get_connection

def get_or_create_artist(
    canonical_name: str,
    spotify_id: str | None = None,
    deezer_id: str | None = None,
    genius_id: str | None = None,
    youtube_channel_id: str | None = None,
) -> int:
    """Return the artist's id, inserting them if they don't already exist.
    Matches on canonical_name via the unique constraint."""
    name_key = canonical_name.strip().lower()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO artists (canonical_name, name_key, spotify_id, deezer_id, genius_id, youtube_channel_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name_key) DO UPDATE
                    SET spotify_id = COALESCE(EXCLUDED.spotify_id, artists.spotify_id),
                        deezer_id = COALESCE(EXCLUDED.deezer_id, artists.deezer_id),
                        genius_id = COALESCE(EXCLUDED.genius_id, artists.genius_id),
                        youtube_channel_id = COALESCE(EXCLUDED.youtube_channel_id, artists.youtube_channel_id)
                RETURNING id
                """,
                (canonical_name, name_key, spotify_id, deezer_id, genius_id, youtube_channel_id),
            )
            artist_id = cur.fetchone()[0]
            conn.commit()
            return artist_id

def insert_signal(artist_id: int, source: str, metric_name: str, value: float, source_ref: str | None = None) -> None:
    """Insert one raw signal snapshot. Always a fresh row — never overwrites,
    since repeated snapshots over time are what let us compute velocity later."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO signals (artist_id, source, metric_name, value, source_ref)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (artist_id, source, metric_name, value, source_ref),
            )
            conn.commit()

