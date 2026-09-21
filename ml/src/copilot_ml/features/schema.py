"""Feature names, their view membership (host-only vs full) and the schema version.

`extraction.extract_features` must produce exactly these keys (checked by a test). Bumping
`FEATURE_SCHEMA_VERSION` is required whenever a feature is added, removed or redefined, because
it is pinned into every exported model's `metadata.json` and into every `predictions` row
(Stage 2), so a served model can be matched back to the feature code that trained it.
"""

from __future__ import annotations

from typing import Literal

FEATURE_SCHEMA_VERSION = "v2"  # v2: moved scheme_is_https out of the host view (see below)

FeatureView = Literal["host", "full"]

# Derivable from the host alone (no scheme, path, query or fragment). This is the view that
# avoids the shortcut identified in the M1.1 data card: in the training data, scheme/path/query
# features are almost perfectly class-exclusive because of how the dataset was sourced (every
# legitimate URL is bare `https://host`; 51% of phishing URLs are plain `http`), not because of
# anything inherent to phishing. `scheme_is_https` is deliberately excluded from this view for
# exactly that reason, even though scheme is textually part of the URL's start, not the path.
HOST_FEATURES: tuple[str, ...] = (
    "host_length",
    "host_num_dots",
    "host_num_hyphens",
    "host_num_digits",
    "host_digit_ratio",
    "host_subdomain_depth",
    "host_is_ip",
    "host_ip_obfuscated",
    "host_has_userinfo",
    "host_has_port",
    "host_port_nonstandard",
    "host_is_punycode",
    "host_is_shortener",
    "host_keyword_hits",
    "host_brand_lookalike",
    "host_entropy",
    "host_longest_token_len",
    "host_registered_domain_length",
    "host_tld",  # categorical; frequency-encoded by a pipeline step fit on train only
)

# Only meaningful once scheme/path/query/fragment are considered. Excluded from the "host" view.
FULL_ONLY_FEATURES: tuple[str, ...] = (
    "scheme_is_https",
    "url_length",
    "url_num_special_chars",
    "url_digit_ratio",
    "url_has_at_symbol",
    "path_length",
    "path_depth",
    "path_has_double_slash",
    "path_num_percent_encoded",
    "path_num_dot_segments",
    "has_query",
    "num_query_params",
    "has_fragment",
    "url_keyword_hits",
    "url_entropy",
    "url_longest_token_len",
    "url_num_slashes",
)

ALL_FEATURES: tuple[str, ...] = HOST_FEATURES + FULL_ONLY_FEATURES
CATEGORICAL_FEATURES: tuple[str, ...] = ("host_tld",)


def feature_names(view: FeatureView) -> tuple[str, ...]:
    return HOST_FEATURES if view == "host" else ALL_FEATURES
