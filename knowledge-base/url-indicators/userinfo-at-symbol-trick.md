---
title: The '@' userinfo trick in URLs
source_name: Original content (this project), concepts from RFC 3986
source_url: https://www.rfc-editor.org/rfc/rfc3986
license: Original content (this project)
topic: url-indicators
mitre_techniques:
  - T1204.001
---

# The '@' userinfo trick in URLs

Per the URL specification (RFC 3986), the authority component of a URL can include userinfo -
login credentials - before the host, separated by `@`: `https://user:password@host/path`. This
was designed for embedding credentials directly in a URL (now discouraged for other reasons);
browsers still parse it correctly but simply discard the userinfo and connect to whatever host
follows the `@`.

## How it is abused

An attacker constructs a URL where a trusted-looking string sits *before* the `@`, and their own
domain sits *after* it: `https://paypal.com@evil-attacker.net/login`. To someone skimming the
URL, especially on a small mobile screen where the string might be truncated, `paypal.com` reads
as the destination. It is not - it is discarded userinfo, and the browser genuinely connects to
`evil-attacker.net`.

## Why this is a strong, low-noise signal

Legitimate URLs essentially never include a userinfo component in ordinary web browsing (it is
occasionally used in tooling and API contexts, never in a consumer-facing link a person is
expected to click). Any `@` appearing in a URL's authority section before the actual host,
outside of a narrow set of technical contexts, is a strong indicator worth flagging - a direct
instance of MITRE ATT&CK T1204.001 (User Execution: Malicious Link)'s underlying goal of
surviving a user's last glance at the address before clicking.
