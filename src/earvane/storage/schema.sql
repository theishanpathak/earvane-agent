CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS artists (
    id SERIAL PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    name_key TEXT NOT NULL,
    spotify_id TEXT,
    deezer_id TEXT,
    genius_id TEXT,
    youtube_channel_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE artists ADD CONSTRAINT unique_name_key UNIQUE (name_key);

CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    artist_id INT NOT NULL REFERENCES artists(id),
    source TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value NUMERIC NOT NULL,
    source_ref TEXT,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    artist_id INT NOT NULL REFERENCES artists(id),
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE embeddings ADD CONSTRAINT unique_embedding_content UNIQUE (artist_id, source, content);

CREATE TABLE IF NOT EXISTS briefs (
    id SERIAL PRIMARY KEY,
    artist_id INT NOT NULL REFERENCES artists(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    faithfulness_score NUMERIC,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_signals_artist_metric_time
    ON signals (artist_id, source, metric_name, collected_at DESC);

CREATE INDEX IF NOT EXISTS idx_embeddings_artist
    ON embeddings (artist_id);