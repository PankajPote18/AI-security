"""Metrics, threshold selection, calibration and model comparison/selection.

Only ever reads model predictions; it does not know how a model was trained (`training`) or
how it is served (`inference`). The test split is touched exactly once, at the very end of
`copilot-ml evaluate`, by convention enforced in the CLI, not in this package.
"""
