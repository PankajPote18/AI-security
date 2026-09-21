"""SHAP-based explanations for a fitted pipeline: global feature importance and per-URL
contributions, both computed on the pipeline's *transformed* feature space (after scaling and
TLD-frequency encoding) so reported values always match what the model actually saw."""
