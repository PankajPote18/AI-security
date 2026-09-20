"""Everything the dataset build learned about the data, in one immutable record.

The pipeline fills it in; the manifest (machine-readable) and the data card (human-readable)
are both rendered from it so they can never disagree.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from copilot_ml.data.audit import ShortcutIndicator
from copilot_ml.data.cleaning import CleaningReport
from copilot_ml.data.labels import PolarityCheck
from copilot_ml.data.sources import DatasetSource
from copilot_ml.data.splitting import SplitSummary


@dataclass(frozen=True)
class DatasetSummary:
    source: DatasetSource
    archive_sha256: str
    archive_bytes: int
    cleaning: CleaningReport
    polarity: PolarityCheck
    seed: int
    n_folds: int
    split_folds: dict[str, int]
    splits: dict[str, SplitSummary]
    site_overlap: dict[str, int]
    largest_sites: list[tuple[str, int]]
    indicators: list[ShortcutIndicator]

    def manifest(self) -> dict[str, Any]:
        """Deterministic (timestamp-free) machine-readable record of the split."""
        return {
            "source": {
                "key": self.source.key,
                "license": self.source.license,
                "archive_sha256": self.archive_sha256,
            },
            "seed": self.seed,
            "n_folds": self.n_folds,
            "split_folds": self.split_folds,
            "cleaning": self.cleaning.as_dict(),
            "label_polarity_check": asdict(self.polarity),
            "splits": {name: part.as_dict() for name, part in self.splits.items()},
            "site_overlap": self.site_overlap,
        }
