"""Shared host-name decomposition, used by both dataset grouping (`data/grouping.py`) and
feature extraction (`features/extraction.py`) so they draw the same registered-domain boundary
from a single place (hosting-platform suffixes such as `web.app` count as public suffixes, so
each tenant is its own registered domain). Bundled suffix list: no network access at runtime.
"""

from __future__ import annotations

from tldextract import TLDExtract

extractor = TLDExtract(suffix_list_urls=(), cache_dir=None, include_psl_private_domains=True)

# ICANN suffixes only, for the "TLD" *category* feature (com/ru/tk/xyz/...). The private-aware
# `extractor` above answers "who controls this host"; this one answers "what registry sold the
# suffix", which is what TLD-prevalence signals are usually about.
public_suffix_extractor = TLDExtract(
    suffix_list_urls=(), cache_dir=None, include_psl_private_domains=False
)
