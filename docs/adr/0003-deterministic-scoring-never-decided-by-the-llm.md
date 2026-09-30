# ADR-0003: Risk score and classification are deterministic; the LLM only explains

- Status: accepted
- Date: 2026-09-22

## Context

The brief's example ("example.com/login scores 92") sets an expectation: a submitted URL gets a
numeric risk score and a classification. There are two ways to produce that number: ask an LLM to
read the evidence and decide, or compute it with a fixed formula and let the LLM only explain a
number it did not choose.

An LLM-decided score is not reproducible (the same URL can score differently run to run, even at
temperature 0, across model/provider updates), not defensible (there is no formula a reviewer can
audit), and vulnerable to prompt injection - a page's own content or a poisoned retrieved document
could talk the model into a different verdict.

## Decision

`security_core.scoring.score(ml_probability, indicators)` is a small, pure, unit-tested function:
calibrated ML probability × 0.8 (weight) + indicator-severity points (capped), thresholded into
low/medium/high and likely_legitimate/suspicious/likely_phishing. It is the **only** place a score
is computed, in standard mode (`analysis_service`) and in deep mode (the MCP `analyze_url` tool,
which the Stage 4 agent must call first - see ADR-0005). Every LLM output schema in this project
(`SecurityReportLLMOutput`) has no field capable of expressing a score or classification - not "a
field we tell the model not to fill in," a schema that structurally cannot carry one. The system
prompts additionally state the given score/level/classification are FINAL FACTS the model must
never contradict, as defense in depth on top of the schema constraint.

## Consequences

- A report can fail to generate (LLM down, out of quota, malformed output) without the analysis
  itself failing - the score already exists before the LLM is ever called.
- Adding a second LLM provider, or removing the LLM entirely, changes nothing about what a URL
  scores.
- The formula's weights (`_SEVERITY_POINTS`, `_ML_WEIGHT`, `_MAX_INDICATOR_POINTS` in
  `security_core/scoring.py`) are the actual tuning surface, not prompt engineering - and every
  change to them is a one-file diff with existing table-driven tests, not a prompt regression
  chase.
