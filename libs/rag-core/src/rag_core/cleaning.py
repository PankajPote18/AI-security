"""Normalise markdown text before chunking: consistent line endings, no trailing whitespace, no
runs of more than one blank line. Headers and body content are otherwise untouched - chunking
depends on the header structure staying intact.
"""

from __future__ import annotations

import re

_TRAILING_WHITESPACE = re.compile(r"[ \t]+\n")
_MULTIPLE_BLANK_LINES = re.compile(r"\n{3,}")


def clean_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING_WHITESPACE.sub("\n", text)
    text = _MULTIPLE_BLANK_LINES.sub("\n\n", text)
    return text.strip() + "\n"
