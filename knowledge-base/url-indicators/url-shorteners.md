---
title: URL shorteners as a phishing evasion technique
source_name: Original content (this project)
source_url: https://developer.mozilla.org/en-US/docs/Web/URI
license: Original content (this project)
topic: url-indicators
mitre_techniques:
  - T1027
---

# URL shorteners as a phishing evasion technique

URL shorteners (bit.ly, tinyurl.com, and similar services) map a short, opaque URL to an
arbitrary long destination. They have entirely legitimate, widespread uses: character-limited
platforms, cleaner-looking links in print material, and click analytics.

## Why they are relevant to phishing analysis

A shortened link tells a visitor nothing about the actual destination domain until it is
followed - which is precisely what makes it useful to an attacker wanting to hide a suspicious
destination domain behind a neutral, widely-trusted short domain. This is not evidence the
destination *is* malicious, only that the URL's structure is deliberately non-transparent about
where it leads, which is why a known-shortener host is treated as a low-severity indicator on its
own, to be weighed together with other evidence (and, where safe redirect-following is available,
resolved to the real destination before that destination is evaluated in turn).

## Relationship to open redirects

A URL shortener and an open redirect on a trusted domain achieve the same functional goal -
decoupling the visible URL from the actual destination - through different mechanisms; see the
open-redirects document for the trusted-domain variant of this pattern.
