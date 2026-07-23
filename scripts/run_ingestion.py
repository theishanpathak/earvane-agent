from earvane.ingestion import spotify, youtube, genius, deezer
from earvane.storage.queries import get_or_create_artist, insert_signal
from earvane.storage.embed import insert_embedding
from earvane.formatting import format_spotify_chunk, format_youtube_chunk, format_genius_chunk

def run_spotify_stage(year: int = 2026, max_results: int = 30) -> list[dict]:
    """Discover artists via Spotify search and store catalog grounding chunks.
    Returns the raw catalog signals so downstream stages can derive a real
    artist list."""

    print("=" * 60)
    print("STAGE 1: Spotify — artist discovery + catalog grounding")
    print("=" * 60)

    token = spotify.get_access_token()
    tracks = spotify.search_recent_tracks(token, year=year, max_results=max_results)
    signals = spotify.extract_catalog_signals(tracks)
    print(f"Found {len(tracks)} tracks -> {len(signals)} catalog signals\n")

    for s in signals:
        artist_id = get_or_create_artist(s['artist_name'], spotify_id=s['artist_id'])
        content = format_spotify_chunk(s)
        insert_embedding(artist_id, "spotify", content)
        print(f"  [spotify] {s['artist_name']} (artist_id={artist_id}) — embedded catalog chunk")

    print(f"\nStage 1 complete: {len(signals)} artists discovered/updated\n")
    return signals



def run_youtube_stage(artist_names: list[str], videos_per_artist: int = 3) -> None:
    """For each artist, match their real YouTube channel, pull recent uploads,
    and store view/subscriber signals plus a grounding chunk per video."""

    print("=" * 60)
    print("STAGE 2: YouTube — view/subscriber velocity signals")
    print("=" * 60)

    signals = youtube.collect_artist_signals(artist_names, videos_per_artist=videos_per_artist)
    print(f"Collected {len(signals)} video signals\n")

    for s in signals:
        
        if s['view_count'] == "n/a" or s['subscriber_count'] == "n/a":
            print(f"  [youtube] SKIPPED {s['artist_name']} — {s['video_title'][:40]} (missing stats)")
            continue

        artist_id = get_or_create_artist(s['artist_name'], youtube_channel_id=s['channel_id'])
        insert_signal(artist_id, "youtube", "view_count", s['view_count'], source_ref=s['video_id'])
        insert_signal(artist_id, "youtube", "subscriber_count", s['subscriber_count'], source_ref=s['channel_id'])
        content = format_youtube_chunk(s)
        insert_embedding(artist_id, "youtube", content)
        print(f"  [youtube] {s['artist_name']} — {s['video_title'][:40]}... "
              f"(views={s['view_count']}, subs={s['subscriber_count']})")

    print(f"\nStage 2 complete: {len(signals)} video signals ingested\n")


def run_deezer_stage(artist_names: list[str]) -> None:
    """For each artist, look up their Deezer fan count and store it as a signal."""

    print("=" * 60)
    print("STAGE 3: Deezer — fan count signal")
    print("=" * 60)

    signals = deezer.collect_fan_signals(artist_names)
    print(f"Collected {len(signals)} fan signals\n")

    for s in signals:
        artist_id = get_or_create_artist(s['artist_name'], deezer_id=s['deezer_id'])
        insert_signal(artist_id, "deezer", "nb_fan", s['nb_fan'], source_ref=s['deezer_url'])
        print(f"  [deezer] {s['artist_name']} — {s['nb_fan']:,} fans")

    print(f"\nStage 3 complete: {len(signals)} fan signals ingested\n")


def run_genius_stage(artist_track_pairs: list[tuple[str, str]]) -> None:
    """For each (artist, track) pair, look up song metadata on Genius and
    store a grounding chunk — no numeric signal, Genius is text-only here."""

    print("=" * 60)
    print("STAGE 4: Genius — song metadata + grounding text")
    print("=" * 60)

    signals = genius.collect_artist_metadata(artist_track_pairs)
    print(f"Collected {len(signals)} metadata signals\n")

    for s in signals:
        artist_id = get_or_create_artist(s['artist_name'], genius_id=s['genius_artist_id'])
        content = format_genius_chunk(s)
        insert_embedding(artist_id, "genius", content)
        print(f"  [genius] {s['artist_name']} — {s['song_title']}")

    print(f"\nStage 4 complete: {len(signals)} metadata signals ingested\n")


def run_full_pipeline() -> None:
    """Run all four ingestion sources in dependency order: Spotify first
    (artist discovery), then YouTube/Deezer/Genius (enrichment), using
    Spotify's real output as the artist list for every downstream stage."""

    print("\n" + "#" * 60)
    print("# EARVANE INGESTION PIPELINE — starting run")
    print("#" * 60 + "\n")

    catalog_signals = run_spotify_stage(max_results=15) # kept small — quota conscious

    artist_names = list({s['artist_name'] for s in catalog_signals})
    artist_track_pairs = [(s['artist_name'], s['track_name']) for s in catalog_signals]

    print(f"Real artist list derived from Spotify ({len(artist_names)} unique): {artist_names}\n")

    run_youtube_stage(artist_names, videos_per_artist=2)  # kept small — quota conscious
    run_deezer_stage(artist_names)
    run_genius_stage(artist_track_pairs)

    print("#" * 60)
    print("# PIPELINE COMPLETE")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    run_full_pipeline()

