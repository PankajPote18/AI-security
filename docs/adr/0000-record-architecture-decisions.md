# ADR-0000: Record architecture decisions

- Status: accepted
- Date: 2026-09-20

## Context

This project makes many choices that are easy to forget and hard to justify later (model
selection, vector store, where an LLM may and may not decide things). Chat history and commit
messages are not a durable place for that reasoning.

## Decision

Significant decisions are recorded as short numbered ADRs in `docs/adr/`, one file per decision,
written when the decision is made (not retrofitted). Each ADR uses this shape:

- **Status** — proposed, accepted, superseded by ADR-NNNN
- **Context** — the forces at play and the options considered
- **Decision** — what we chose, in one or two sentences
- **Consequences** — what becomes easier, harder, or is explicitly out of scope

An ADR is only written for choices that are costly to reverse or that a reviewer would question.
Routine implementation details are not ADRs.

## Consequences

Small overhead per decision; in exchange the "why" survives alongside the code. Superseded ADRs
stay in the repository, marked as superseded, so the history of the thinking is preserved.
