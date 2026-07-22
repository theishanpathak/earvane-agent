# Earvane

Earvane is an autonomous agent that scouts emerging music trends from public API signals (Spotify, YouTube, Reddit), grounds its findings in retrieved evidence via a RAG pipeline, and publishes cited trend briefs to a public website.

## What it does

Every 6 hours, Earvane:
1. Collects public catalog and engagement signals from Spotify, YouTube, and Reddit's read-only APIs
2. Computes artist growth velocity from raw counter snapshots stored over time
3. Uses a LangGraph agent to decide which artists warrant a deeper look, retrieves grounded context via pgvector similarity search, and synthesizes a cited trend brief
4. Publishes results to a public Next.js frontend

## Reddit API usage

Earvane makes read-only requests to Reddit's Data API to collect public post metadata (title, score, comment count) from a small, fixed list of public music subreddits. It does not post, comment, vote, or take any write action on Reddit — it is a passive research/analytics client only.

## Stack

Python, uv, LangGraph, Postgres + pgvector, Langfuse, Next.js

## Status

Actively in development — currently building out the ingestion layer (Phase 1 of 10).
