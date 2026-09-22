# Knowledge base sources and licensing

28 documents, organised by topic folder. Every document's YAML frontmatter carries its own
`source_name`, `source_url`, and `license` field, which is what `rag-core`'s loader validates and
what the backend surfaces as a citation alongside any AI-generated explanation - this file is a
human-readable index of the same information, not a separate source of truth.

## Provenance categories

- **MITRE ATT&CK** (`knowledge-base/mitre/`): concise, original summaries of specific ATT&CK
  techniques (tactic, description, and why it matters for URL analysis), attributed to
  [attack.mitre.org](https://attack.mitre.org/) under MITRE ATT&CK's Terms of Use, which permit
  reuse with attribution. Not verbatim copies of MITRE's text.
- **OWASP-informed** (`knowledge-base/owasp/`, parts of `http/` and `authentication/`): original
  writing built on concepts from OWASP Cheat Sheets (CC BY-SA 4.0) and the OWASP Secure Headers
  Project, attributed by URL in each document's frontmatter. Not verbatim copies.
- **Public standards and guidance** (`knowledge-base/dns/`, `http/https-tls-overview.md`):
  original writing built on publicly documented concepts from IETF RFCs (3986, 3492, 6376, 7208,
  7489, 9083), MDN Web Docs, and CISA public phishing guidance.
- **Original explainers** (`knowledge-base/phishing/`, `social-engineering/`,
  `url-indicators/`): written for this project. Where a document draws on a specific public
  source (e.g. CISA's phishing advisories), that source is credited in the frontmatter.

## Why summaries rather than verbatim excerpts

Every document here is original writing, not a copy-paste of source material, even where the
license of the underlying source (e.g. OWASP's CC BY-SA 4.0) would permit verbatim reuse. This
keeps licensing unambiguous across the whole knowledge base, keeps the chunking/retrieval unit
(a paragraph written for exactly this purpose) more useful than an arbitrary excerpt of a much
longer external document, and keeps the tone and depth consistent for what an LLM will
synthesise from during report generation.

## Maintaining this knowledge base

Adding a document: create a `.md` file anywhere under `knowledge-base/`, with YAML frontmatter
carrying `title`, `source_name`, `source_url`, `license`, `topic`, and optionally
`mitre_techniques` (a list of ATT&CK technique IDs the document is relevant to - these are what
let `security_core.indicators`' `mitre_technique` field on a fired indicator retrieve the right
canonical explanation). Then run `uv run rag-core ingest` to index it - see
`docs/local-development.md`.
