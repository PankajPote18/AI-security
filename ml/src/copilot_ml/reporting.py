"""Tiny markdown-rendering helpers shared by every generated report (`data.card`,
`evaluation.model_card`), so both produce tables in the same format."""

from __future__ import annotations


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def render_table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)
