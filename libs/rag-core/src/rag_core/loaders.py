"""Load `knowledge-base/*.md` files (YAML frontmatter + markdown body) into `KnowledgeDocument`s.

Every document must declare its provenance (`source_name`, `source_url`, `license`) - the whole
point of this knowledge base is that its claims are attributable, not model-generated trivia.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_FRONTMATTER_DELIMITER = "---"
_REQUIRED_FIELDS = ("title", "source_name", "source_url", "license", "topic")

# Documentation-about-the-knowledge-base files, not knowledge-base content themselves; they live
# alongside the content (so they are easy to find) but must not be parsed as a KnowledgeDocument.
NON_CONTENT_FILENAMES = frozenset({"SOURCES.md", "README.md"})


class FrontmatterError(ValueError):
    """A knowledge-base file is missing or has malformed YAML frontmatter."""


@dataclass(frozen=True)
class KnowledgeDocument:
    doc_id: str  # stable id, the file's path relative to the knowledge base, without extension
    title: str
    source_name: str
    source_url: str
    license: str
    topic: str
    mitre_techniques: tuple[str, ...]
    content: str  # markdown body, frontmatter stripped
    path: Path


def _parse_frontmatter(text: str, path: Path) -> tuple[dict[str, object], str]:
    if not text.startswith(_FRONTMATTER_DELIMITER):
        raise FrontmatterError(f"{path}: missing YAML frontmatter (file must start with '---')")
    _, _, rest = text.partition(_FRONTMATTER_DELIMITER + "\n")
    frontmatter_text, closed, body = rest.partition("\n" + _FRONTMATTER_DELIMITER)
    if not closed:
        raise FrontmatterError(f"{path}: frontmatter block is not closed with a second '---'")

    try:
        metadata = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as error:
        raise FrontmatterError(f"{path}: invalid YAML frontmatter: {error}") from error
    if not isinstance(metadata, dict):
        raise FrontmatterError(f"{path}: frontmatter must be a YAML mapping")

    missing = [field for field in _REQUIRED_FIELDS if not metadata.get(field)]
    if missing:
        raise FrontmatterError(f"{path}: frontmatter missing required field(s): {missing}")

    return metadata, body.lstrip("\n")


def load_document(path: Path, base_dir: Path) -> KnowledgeDocument:
    text = path.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text, path)
    doc_id = path.relative_to(base_dir).with_suffix("").as_posix()

    mitre = metadata.get("mitre_techniques") or []
    if not isinstance(mitre, list):
        raise FrontmatterError(f"{path}: 'mitre_techniques' must be a YAML list")

    return KnowledgeDocument(
        doc_id=doc_id,
        title=str(metadata["title"]),
        source_name=str(metadata["source_name"]),
        source_url=str(metadata["source_url"]),
        license=str(metadata["license"]),
        topic=str(metadata["topic"]),
        mitre_techniques=tuple(str(t) for t in mitre),
        content=body,
        path=path,
    )


def load_documents(base_dir: Path) -> list[KnowledgeDocument]:
    paths = sorted(p for p in base_dir.rglob("*.md") if p.name not in NON_CONTENT_FILENAMES)
    return [load_document(p, base_dir) for p in paths]
