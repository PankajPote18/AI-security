"""Render the human-readable data card from a DatasetSummary."""

from __future__ import annotations

from datetime import date

from copilot_ml.data.audit import COMPOSITE_NAME
from copilot_ml.data.summary import DatasetSummary


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def _source_section(summary: DatasetSummary) -> str:
    source = summary.source
    rows = [
        ["Dataset", f"{source.title} ([page]({source.homepage}))"],
        ["License", source.license],
        ["Citation", source.citation],
        ["Archive SHA-256", f"`{summary.archive_sha256}`"],
        ["Archive size", f"{summary.archive_bytes / 1e6:.1f} MB"],
        ["Columns used", f"`{source.url_column}` (URL text) and `{source.label_column}` only"],
    ]
    note = (
        "The source also ships ~50 precomputed columns derived from page content (HTML, "
        "favicon, similarity indices). They are **deliberately ignored**: the product analyses "
        "a URL before any page is fetched, so features must come from the URL alone."
    )
    return f"## 1. Source\n\n{_table(['Field', 'Value'], rows)}\n\n{note}"


def _label_section(summary: DatasetSummary) -> str:
    source, check = summary.source, summary.polarity
    return (
        "## 2. Label convention\n\n"
        f"Raw `{source.label_column}` = {source.phishing_label} means **phishing** "
        "(inverted vs. the usual convention; confirmed on the dataset page). "
        "Everything downstream uses `label = 1` for phishing.\n\n"
        f"Empirical check: {_pct(check.marker_rate_phishing)} of phishing-labelled URLs contain a "
        f"classic phishing marker (credential-lure keyword, raw IP host, `@`) versus "
        f"{_pct(check.marker_rate_legitimate)} of legitimate-labelled URLs "
        f"(**{check.ratio:.0f}x** higher) — polarity check **passed**."
    )


def _cleaning_section(summary: DatasetSummary) -> str:
    c = summary.cleaning
    rows = [
        ["Rows in source", f"{c.rows_in:,}"],
        ["Dropped: missing/empty URL", f"{c.dropped_missing:,}"],
        ["Dropped: unparseable URL", f"{c.dropped_unparseable:,}"],
        ["Dropped: not http(s) or no host", f"{c.dropped_scheme_or_host:,}"],
        ["Dropped: same URL with conflicting labels", f"{c.dropped_conflicting_labels:,}"],
        ["Dropped: exact duplicates", f"{c.dropped_duplicates:,}"],
        ["**Rows kept**", f"**{c.rows_out:,}**"],
    ]
    return f"## 3. Cleaning\n\n{_table(['Step', 'Rows'], rows)}"


def _split_section(summary: DatasetSummary) -> str:
    folds = summary.split_folds
    split_rows = [
        [
            name,
            f"{part.rows:,}",
            f"{part.phishing:,}",
            f"{part.legitimate:,}",
            _pct(part.phishing_rate),
            f"{part.sites:,}",
        ]
        for name, part in summary.splits.items()
    ]
    overlap_rows = [[pair, str(count)] for pair, count in summary.site_overlap.items()]
    top_rows = [[site, f"{count:,}"] for site, count in summary.largest_sites]
    total = sum(part.rows for part in summary.splits.values())
    phishing = sum(part.phishing for part in summary.splits.values())
    return (
        "## 4. Class balance and splits\n\n"
        f"Method: greedy class-aware group assignment (largest sites first) into "
        f"{summary.n_folds} folds, seed={summary.seed}; folds mapped "
        f"{folds['train']}/{folds['val']}/{folds['test']} to train/val/test. "
        "The group is the **site** (registered domain; hosting-platform suffixes such as "
        "`web.app` count as public suffixes so each tenant is its own site; raw IPs fall back "
        "to the hostname). No site can appear in two splits.\n\n"
        + _table(["Split", "Rows", "Phishing", "Legitimate", "Phishing rate", "Sites"], split_rows)
        + "\n\nSites shared between splits (must all be 0):\n\n"
        + _table(["Split pair", "Shared sites"], overlap_rows)
        + "\n\nLargest sites (rows):\n\n"
        + _table(["Site", "Rows"], top_rows)
        + f"\n\nPhishing prevalence here is **{_pct(phishing / total)}**, far above what real "
        "traffic looks like (well under 5%). Precision measured on this data is therefore "
        "optimistic; evaluation re-bases precision to realistic prevalence (M1.5)."
    )


def _shortcut_section(summary: DatasetSummary) -> str:
    rows = [
        [
            f"`{ind.name}`",
            ind.description,
            _pct(ind.rate_phishing),
            _pct(ind.rate_legitimate),
            _pct(ind.rule_accuracy),
            "**CLASS-EXCLUSIVE**" if ind.class_exclusive else "",
        ]
        for ind in summary.indicators
    ]
    total = sum(part.rows for part in summary.splits.values())
    phishing = sum(part.phishing for part in summary.splits.values())
    majority_accuracy = max(phishing, total - phishing) / total
    composite = next(ind for ind in summary.indicators if ind.name == COMPOSITE_NAME)
    flagged = [ind for ind in summary.indicators if ind.class_exclusive]

    text = (
        "## 5. Shortcut audit\n\n"
        "How differently do the classes behave on trivial URL-shape indicators, and how good "
        'is the one-line rule "indicator present => phishing"?\n\n'
        + _table(["Indicator", "Meaning", "Phishing", "Legitimate", "Rule accuracy", "Flag"], rows)
        + f"\n\nMajority-class baseline accuracy: **{_pct(majority_accuracy)}**. "
        f"The single rule `{COMPOSITE_NAME}` alone reaches **{_pct(composite.rule_accuracy)}**."
    )
    if flagged:
        names = ", ".join(f"`{ind.name}`" for ind in flagged)
        text += (
            f"\n\n> **WARNING — shortcut learning risk.** Class-exclusive indicators: {names}. "
            "Each is (almost) never present in one class while common in the other. The "
            "legitimate class appears to be built from a different population than the "
            "phishing class, so a model can score highly by recognising *how the URLs were "
            "sourced* rather than *what phishing looks like*. Headline accuracy on this data "
            "must not be trusted on its own."
        )
    return text


def _implications_section(summary: DatasetSummary) -> str:
    if not any(ind.class_exclusive for ind in summary.indicators):
        return ""
    return (
        "\n\n## 6. Consequences for modelling\n\n"
        "- Feature engineering (M1.2) must be able to produce a **host-only view** of a URL "
        "(scheme, path, query removed) so models can be trained and compared without the "
        "sourcing artefacts above.\n"
        "- Model comparison (M1.4) must include a **path/scheme ablation** and report both "
        "views side by side.\n"
        "- Because legitimate URLs with paths are absent, generalisation to real user URLs "
        "cannot be measured on this data alone; an **external validation set** containing "
        "legitimate URLs with paths is needed before any claim about real-world performance."
    )


def render_data_card(summary: DatasetSummary, built_on: date) -> str:
    sections = [
        f"# Data Card — {summary.source.title}",
        f"_Generated by `copilot-ml data build` on {built_on.isoformat()}. "
        "Do not edit by hand; rebuild instead._",
        _source_section(summary),
        _label_section(summary),
        _cleaning_section(summary),
        _split_section(summary),
        _shortcut_section(summary),
    ]
    return "\n\n".join(sections) + _implications_section(summary) + "\n"
