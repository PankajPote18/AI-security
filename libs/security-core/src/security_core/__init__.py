"""Shared security primitives used by the backend, the MCP server (Stage 4) and `copilot-ml`.

`ip_host`, `entropy` and `hostnames` are the low-level, dependency-light URL/host detectors:
canonical home for logic that must behave identically wherever a URL is examined, so
`copilot_ml.features` depends on this package rather than re-implementing them.
"""
