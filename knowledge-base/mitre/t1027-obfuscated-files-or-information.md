---
title: "MITRE ATT&CK T1027 - Obfuscated Files or Information"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1027/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1027
---

# MITRE ATT&CK T1027 - Obfuscated Files or Information

**Tactic:** Defense Evasion

An adversary deliberately makes content (a file, a script, a URL, an artifact) harder for a
person or an automated tool to inspect and recognise as malicious, without changing what it
actually does. The goal is evading detection and casual review, not adding new capability.

## URL-specific instances of this technique

- **URL shorteners**: hide the true destination behind an opaque, unrelated short domain.
- **Open redirects**: hide the true destination behind a trusted domain's own redirect endpoint
  (see the open-redirects document).
- **Percent-encoding**: encoding characters in a path or query string (`%2E%2E%2F` instead of
  `../`) to slip past naive string-matching filters while browsers and servers still decode and
  act on the underlying value.
- **Punycode / homograph domains**: encoding a visually deceptive internationalised domain name
  in ASCII-compatible punycode (see the dedicated document).
- **Decimal, octal or hexadecimal IP encoding**: writing a raw IP address host in a form that
  does not visually look like a dotted-decimal IP address (`http://3232235521/` instead of
  `http://192.168.1.1/`), while browsers and servers still resolve it as one.

## Why this matters for automated URL analysis

A tool that only pattern-matches on the *literal* text of a URL can be defeated by any of the
above tricks unless it specifically normalises and decodes the URL before evaluating it - which
is why this project's feature extraction and indicator logic explicitly parses and classifies
IP-host encodings, percent-encoding, and punycode rather than relying on surface-level string
matching alone.
