"""Production inference: load a checksummed model artifact and score a URL.

Nothing here imports `copilot_ml.training` (enforced by a test) - inference only needs an
already-exported artifact plus `features` (shared, pure feature extraction) and `explain`
(shared SHAP wrapper), never the training code that produced the artifact.
"""
