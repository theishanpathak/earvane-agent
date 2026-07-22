from earvane.storage.db import get_connection

def get_or_create_artist(
    canonical_name: str,
    spotify_id: str | None = None,
    deezer_id: str | None = None,
    genius_id: str | None = None,
) -> int:
    """Return the artist's id, inserting them if they don't already exist.
    Matches on canonical_name via the unique constraint."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO artists (canonical_name, spotify_id, deezer_id, genius_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (canonical_name) DO UPDATE
                    SET canonical_name = EXCLUDED.canonical_name
                RETURNING id
                """,
                (canonical_name, spotify_id, deezer_id, genius_id),
            )
            artist_id = cur.fetchone()[0]
            conn.commit()
            return artist_id

def insert_signal(artist_id: int, source: str, metric_name: str, value: float) -> None:
    """Insert one raw signal snapshot. Always a fresh row — never overwrites,
    since repeated snapshots over time are what let us compute velocity later."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO signals (artist_id, source, metric_name, value)
                VALUES (%s, %s, %s, %s)
                """,
                (artist_id, source, metric_name, value),
            )
            conn.commit()

