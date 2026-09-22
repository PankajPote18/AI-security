---
title: HTTP security headers
source_name: Original content (this project), concepts from OWASP Secure Headers Project
source_url: https://owasp.org/www-project-secure-headers/
license: Original content (this project), concepts from OWASP (CC BY-SA 4.0)
topic: http
---

# HTTP security headers

HTTP response headers can instruct the browser to enable additional protections beyond what TLS
alone provides. Their presence and correctness is a useful (though not definitive) signal about
how mature a site's engineering practices are.

## Headers most relevant to phishing-adjacent risk

- **Strict-Transport-Security (HSTS)**: tells the browser to only ever connect to this domain
  over HTTPS, for a specified duration, even if the user types `http://`. Widely deployed by
  established sites; commonly absent on quickly-assembled phishing infrastructure, which has no
  incentive to configure it.
- **Content-Security-Policy (CSP)**: restricts which sources a page may load scripts, styles, and
  other resources from, reducing the impact of injected content. A credential-harvesting clone
  copied wholesale from a real site sometimes carries over a CSP header that does not quite match
  the cloned page's actual (different) resource origins, which is a subtle but sometimes usable
  signal.
- **X-Frame-Options / frame-ancestors (via CSP)**: prevents a page from being embedded in an
  iframe on another site, defending against clickjacking. Its absence is not evidence of
  phishing on its own - it is a general web-hardening header many small, legitimate sites also
  omit.

## Why this is supporting, not primary, evidence

Security-header hygiene correlates with general engineering maturity, not directly with
malicious intent - a large fraction of entirely legitimate small businesses and personal sites
also omit these headers. They are most useful as one additional data point alongside domain age,
DNS, and structural URL indicators, never as a standalone verdict.
