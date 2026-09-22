"""Cybersecurity knowledge RAG pipeline: load -> clean -> chunk -> embed -> index -> retrieve.

Used by the backend's report generation (Stage 3) to ground the LLM's explanation in cited,
curated source material rather than the model's own unchecked claims.
"""
