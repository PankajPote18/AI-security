---
title: Open redirects and URL parameter abuse
source_name: Original content (this project), concepts from OWASP Unvalidated Redirects and Forwards Cheat Sheet
source_url: https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html
license: Original content (this project), concepts from OWASP (CC BY-SA 4.0)
topic: owasp
mitre_techniques:
  - T1027
---

# Open redirects and URL parameter abuse

An open redirect is a web application endpoint that redirects a visitor to a URL supplied in a
query parameter without validating that the target is safe or expected - for example,
`https://real-brand.example/redirect?url=<anything>`. This is an OWASP-catalogued web
application weakness in its own right, and phishing campaigns abuse it specifically because the
*visible, clickable domain* in the link is the real, trusted brand's own domain.

## Why attackers use them

A link that starts with a well-known, trusted domain passes casual visual inspection, and can
bypass simplistic link-reputation checks that only look at the domain, not the full URL. The
victim clicks a link to a domain they recognise and trust, and is transparently forwarded to the
attacker's actual phishing page.

## Relationship to URL shorteners

URL shorteners serve a similar evasive purpose from the opposite direction: instead of hiding the
real destination behind a *trusted* domain's redirect, they hide it behind a *neutral*,
purpose-built short domain. Both techniques share the same underlying goal - decouple the URL a
victim sees from the page they actually land on - which is why "redirect analysis" (following a
URL's redirect chain, where it is safe to do so) is a useful defensive technique, distinct from
looking at the initial URL's domain alone.

## Obfuscation more generally

MITRE ATT&CK technique T1027 (Obfuscated Files or Information) covers the broader pattern of an
adversary deliberately disguising an artifact - a URL, a file, a script - to evade detection or
casual inspection. Open redirects, URL shorteners, punycode homograph domains, and
percent-encoded path segments are all URL-specific instances of this same general idea: make the
malicious content harder to recognise at a glance without changing what it actually does.
