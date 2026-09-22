---
title: Domain age, registrars and RDAP
source_name: Original content (this project), concepts from RFC 9083 (RDAP)
source_url: https://www.icann.org/rdap
license: Original content (this project)
topic: dns
mitre_techniques:
  - T1583.001
---

# Domain age, registrars and RDAP

RDAP (Registration Data Access Protocol) is the modern, structured successor to WHOIS: a
standard way to query a domain's registrar, registration date, last-updated date, and status
codes from the registry that manages its top-level domain (RFC 9083). It is the primary source
for one of the most useful single signals in phishing analysis: **domain age**.

## Why domain age matters

Registering a domain takes minutes and costs very little. Phishing campaigns are frequently
built on domains registered hours to days before the campaign starts - registering infrastructure
long in advance both costs more and risks the domain being flagged before it is used. A domain
that is only days or weeks old, especially one that also carries phishing-style structural
indicators (a brand name plus "secure" or "verify" in the hostname, for example), is materially
more likely to be malicious than an identical-looking domain that has existed for a decade.
MITRE ATT&CK tracks the underlying activity as T1583.001 (Acquire Infrastructure: Domains).

## What age alone cannot tell you

Domain age is not proof either way:

- A brand-new domain can be entirely legitimate (a new product launch, a new small business).
- An old domain can be malicious - either because it was **compromised** (a legitimate,
  long-registered site had a phishing page planted on it) or because attackers deliberately
  "age" a domain, registering it early and leaving it dormant before use specifically to defeat
  age-based detection.

## Registrar and status signals

RDAP also exposes the registrar and status codes such as `clientTransferProhibited` (normal, most
registrars set this by default) or, less commonly, status codes associated with disputes or
suspensions. A registrar known for being cheap, fast, and loosely verified is more commonly seen
in abuse infrastructure than one with stricter registration requirements - though this is a weak
signal on its own, since the same registrars serve millions of entirely legitimate domains too.
