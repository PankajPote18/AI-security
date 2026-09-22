---
title: Credential-related keywords in a domain name
source_name: Original content (this project)
source_url: https://www.cisa.gov/topics/cyber-threats-and-advisories/phishing
license: Original content (this project)
topic: url-indicators
mitre_techniques:
  - T1566.002
---

# Credential-related keywords in a domain name

Words like "login," "signin," "verify," "secure," "account," "update," or "confirm" appearing
inside a **domain name itself** (not just the page's path or content) are a recurring pattern in
phishing infrastructure, because the domain is often the only piece of branding an attacker fully
controls and wants to make load-bearing: `secure-login-verify.example.net` is designed to read as
reassuring even though it names nothing a real brand actually owns.

## Why the domain, not the path, is the meaningful location

Legitimate services put exactly these words in **paths** constantly -
`https://accounts.google.com/signin`, `https://example.com/account/verify` - because a path
segment is just routing within a domain the organisation already controls and has established
trust in. The same words appearing as part of the **registered domain or a subdomain of an
unrelated domain** is different: it is an attempt to manufacture trust through wording alone,
on infrastructure with no other connection to the brand or concept it names.

## A weak signal on its own

Plenty of legitimate small services and internal tools do use words like "secure" or "portal" in
a domain they genuinely own. This indicator is meaningful mainly in combination with other
evidence - domain age, lack of a real brand match, IP hosting, or a low ML confidence in
legitimacy - not as a standalone verdict.
