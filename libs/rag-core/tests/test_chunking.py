from rag_core.chunking import CHUNK_SIZE, chunk_text

_DOC = """# Phishing

Phishing is a social engineering attack.

## Common techniques

Attackers impersonate trusted brands to steal credentials.

## Detection

Look for lookalike domains and urgency language.
"""


def test_chunks_carry_their_heading_path() -> None:
    chunks = chunk_text("phishing-overview", _DOC)
    paths = {c.heading_path for c in chunks}
    assert "Phishing" in paths
    assert "Phishing > Common techniques" in paths
    assert "Phishing > Detection" in paths


def test_chunk_ids_are_stable_for_identical_input() -> None:
    first = chunk_text("doc-a", _DOC)
    second = chunk_text("doc-a", _DOC)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]


def test_chunk_ids_differ_by_doc_id() -> None:
    a = chunk_text("doc-a", _DOC)
    b = chunk_text("doc-b", _DOC)
    assert {c.chunk_id for c in a}.isdisjoint({c.chunk_id for c in b})


def test_changing_a_chunks_text_changes_only_its_own_id() -> None:
    original = chunk_text("doc-a", _DOC)
    edited_doc = _DOC.replace("Look for lookalike domains", "Look for suspicious lookalike domains")
    edited = chunk_text("doc-a", edited_doc)

    original_ids = [c.chunk_id for c in original]
    edited_ids = [c.chunk_id for c in edited]
    # Exactly the last (edited) chunk's id changes; earlier, untouched chunks keep their id.
    assert original_ids[:-1] == edited_ids[:-1]
    assert original_ids[-1] != edited_ids[-1]


def test_no_chunk_exceeds_chunk_size_by_much() -> None:
    long_doc = "# Big\n\n" + ("word " * 1000)
    chunks = chunk_text("big-doc", long_doc)
    assert len(chunks) > 1
    # header text plus overlap means chunks can exceed CHUNK_SIZE slightly, but not by much
    assert all(len(c.text) <= CHUNK_SIZE * 1.5 for c in chunks)


def test_empty_sections_are_dropped() -> None:
    doc = "# A\n\n## B\n\n## C\n\nSome text.\n"  # B has no body text
    chunks = chunk_text("doc", doc)
    assert all(c.text.strip() for c in chunks)


def test_chunk_index_increments_within_a_document() -> None:
    chunks = chunk_text("doc-a", _DOC)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
