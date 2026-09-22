---
title: String entropy as a phishing signal
source_name: Original content (this project)
source_url: https://attack.mitre.org/techniques/T1568/002/
license: Original content (this project)
topic: url-indicators
mitre_techniques:
  - T1568.002
---

# String entropy as a phishing signal

Shannon entropy measures how unpredictable a string's characters are - a repetitive or
dictionary-word-like string has low entropy; a string that looks close to random has high
entropy. Applied to a hostname, this gives a rough, automatable proxy for "does this look like a
word or brand a human chose, or like something generated"?

## Why it correlates, loosely, with risk

Legitimate domains are almost always chosen to be memorable and brandable - low entropy by
construction, because the whole point is that a human can read, recall, and trust them.
High-entropy hostnames show up in a few different (not mutually exclusive) contexts: malware
command-and-control infrastructure using domain generation algorithms (MITRE ATT&CK T1568.002),
automatically generated tenant subdomains on hosting platforms, and some throwaway phishing
kits that do not bother with a brand-lookalike domain at all and instead rely purely on the page
content to deceive.

## Why it is one of the weaker individual signals

Entropy alone cannot distinguish "randomly generated malware C2 domain" from "randomly generated
but entirely benign CDN or hosting-platform subdomain," both of which are extremely common on the
legitimate web. It is most useful as a small corroborating signal alongside stronger, more
specific indicators (IP hosting, credential keywords, brand lookalikes, domain age), never as a
standalone reason to treat a URL as suspicious.
