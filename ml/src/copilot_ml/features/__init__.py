"""URL feature extraction, shared verbatim by training and inference.

`extraction.extract_features` is the single source of truth for turning a URL string into a
feature dict; `schema` defines the feature names, their groups (host-only vs full) and the
schema version that is pinned into every exported model artifact.
"""
