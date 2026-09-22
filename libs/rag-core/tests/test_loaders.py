from pathlib import Path

import pytest

from rag_core.loaders import FrontmatterError, load_document, load_documents

_VALID = """---
title: Example Doc
source_name: Example Source
source_url: https://example.com/doc
license: CC BY 4.0
topic: phishing
mitre_techniques:
  - T1566.002
---

# Example Doc

Some content here.
"""


def test_loads_a_valid_document(tmp_path: Path) -> None:
    path = tmp_path / "kb" / "phishing" / "example.md"
    path.parent.mkdir(parents=True)
    path.write_text(_VALID, encoding="utf-8")

    doc = load_document(path, tmp_path / "kb")

    assert doc.doc_id == "phishing/example"
    assert doc.title == "Example Doc"
    assert doc.source_url == "https://example.com/doc"
    assert doc.mitre_techniques == ("T1566.002",)
    assert "Some content here." in doc.content
    assert not doc.content.startswith("---")


def test_missing_frontmatter_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "no_frontmatter.md"
    path.write_text("# Just a heading\n\nbody", encoding="utf-8")
    with pytest.raises(FrontmatterError, match="missing YAML frontmatter"):
        load_document(path, tmp_path)


def test_unclosed_frontmatter_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "unclosed.md"
    path.write_text("---\ntitle: x\n\nbody with no closing delimiter", encoding="utf-8")
    with pytest.raises(FrontmatterError, match="not closed"):
        load_document(path, tmp_path)


@pytest.mark.parametrize(
    "missing_field", ["title", "source_name", "source_url", "license", "topic"]
)
def test_missing_required_field_is_rejected(tmp_path: Path, missing_field: str) -> None:
    fields = {
        "title": "T",
        "source_name": "S",
        "source_url": "https://example.com",
        "license": "CC BY 4.0",
        "topic": "phishing",
    }
    del fields[missing_field]
    frontmatter = "\n".join(f"{k}: {v}" for k, v in fields.items())
    path = tmp_path / "incomplete.md"
    path.write_text(f"---\n{frontmatter}\n---\n\nbody", encoding="utf-8")
    with pytest.raises(FrontmatterError, match="missing required field"):
        load_document(path, tmp_path)


def test_mitre_techniques_defaults_to_empty_tuple(tmp_path: Path) -> None:
    path = tmp_path / "no_mitre.md"
    frontmatter = "title: T\nsource_name: S\nsource_url: https://x\nlicense: CC0\ntopic: dns"
    path.write_text(f"---\n{frontmatter}\n---\n\nbody", encoding="utf-8")
    doc = load_document(path, tmp_path)
    assert doc.mitre_techniques == ()


def test_load_documents_skips_sources_and_readme(tmp_path: Path) -> None:
    # Regression: SOURCES.md documents the knowledge base but is not itself a knowledge
    # document, and has no frontmatter - it must not be swept up by the *.md glob.
    (tmp_path / "SOURCES.md").write_text("# Sources\n\nNo frontmatter here.", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Readme\n\nAlso no frontmatter.", encoding="utf-8")
    doc_path = tmp_path / "real-doc.md"
    doc_path.write_text(_VALID, encoding="utf-8")

    docs = load_documents(tmp_path)

    assert [d.doc_id for d in docs] == ["real-doc"]


def test_load_documents_finds_every_markdown_file_recursively(tmp_path: Path) -> None:
    for name in ("a.md", "sub/b.md", "sub/deeper/c.md"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_VALID, encoding="utf-8")

    docs = load_documents(tmp_path)
    assert {d.doc_id for d in docs} == {"a", "sub/b", "sub/deeper/c"}
