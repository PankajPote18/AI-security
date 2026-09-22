"""`rag-ingest`: build/update the knowledge-base index. `rag-search`: query it from the CLI."""

from __future__ import annotations

from pathlib import Path

import typer

from rag_core.ingest import ingest_directory
from rag_core.retriever import retrieve
from rag_core.vector_store import open_client

app = typer.Typer(no_args_is_help=True, help="Cybersecurity knowledge base RAG pipeline.")

_DEFAULT_KB_DIR = Path(__file__).resolve().parents[4] / "knowledge-base"


@app.command("ingest")
def ingest(directory: Path = _DEFAULT_KB_DIR) -> None:
    """Load, chunk, embed and index every knowledge-base document."""
    client = open_client()
    result = ingest_directory(client, directory)
    typer.echo(
        f"documents={result.documents} chunks={result.chunks} "
        f"embedded_chunks={result.embedded_chunks} "
        f"deleted_stale_chunks={result.deleted_stale_chunks}"
    )


@app.command("search")
def search(query: str, top_k: int = 5) -> None:
    """Run a hybrid search against the indexed knowledge base."""
    client = open_client()
    result = retrieve(client, query, top_k=top_k)
    for chunk in result.chunks:
        typer.echo(f"[{chunk.score:.4f}] {chunk.metadata.get('title')} ({chunk.chunk_id})")
        typer.echo(f"  {chunk.text[:200]}")
