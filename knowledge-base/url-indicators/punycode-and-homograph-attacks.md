---
title: Punycode and homograph (IDN) attacks
source_name: Original content (this project), concepts from RFC 3492 and Unicode Technical Standard 39
source_url: https://www.unicode.org/reports/tr39/
license: Original content (this project)
topic: url-indicators
mitre_techniques:
  - T1583.001
  - T1027
---

# Punycode and homograph (IDN) attacks

Internationalised Domain Names (IDNs) let domains contain non-ASCII characters (accented Latin
letters, Cyrillic, Greek, and more), encoded for the DNS system as ASCII strings prefixed
`xn--` - a scheme called punycode. This is a legitimate, necessary feature that lets people
register domains in their own language and script.

## How it is abused

Many characters from different scripts look identical or nearly identical to Latin letters used
in well-known brand names - Cyrillic "а" versus Latin "a" is the canonical example. An attacker
registers a domain using look-alike characters from another script (`аpple.com` using a Cyrillic
"а"), which browsers, when they choose to render it, may display as visually indistinguishable
from the real brand's domain. The underlying punycode-encoded form (`xn--pple-43d.com`) is what
actually gets requested and is what a URL-analysis pipeline sees.

## Why any punycode-encoded host is worth flagging

Legitimate use of IDN domains for security-sensitive contexts (banking, major SaaS logins) is
rare, since it introduces exactly this attack surface; browsers themselves apply increasingly
strict rules about when they will render an IDN in its decoded (non-ASCII) form rather than show
the raw `xn--` punycode, specifically to blunt this attack. A domain starting with `xn--`
appearing where a well-known Latin-script brand is expected is a meaningful structural signal,
even though non-`xn--` legitimate internationalised sites do exist and are not inherently
suspicious in their own right.
