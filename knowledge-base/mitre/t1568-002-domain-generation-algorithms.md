---
title: "MITRE ATT&CK T1568.002 - Dynamic Resolution: Domain Generation Algorithms"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1568/002/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1568.002
---

# MITRE ATT&CK T1568.002 - Dynamic Resolution: Domain Generation Algorithms

**Tactic:** Command and Control (sub-technique of T1568, Dynamic Resolution)

Adversaries use an algorithm to periodically generate a large number of domain names as rendezvous
points for malware command-and-control, rather than hard-coding a fixed domain that defenders
could simply block. Only a small subset of the generated domains are actually registered and
active at any time; the rest exist only as unresolvable possibilities, which is itself a
defensive burden (blocking one algorithmically-generated domain does nothing to stop the next).

## Why algorithmically-generated domains look the way they do

Because they are produced by an algorithm rather than chosen for brand recognition, DGA domains
typically look like meaningless, high-entropy strings of characters - unlike a phishing domain,
which usually incorporates a real brand name specifically to look familiar. High string entropy
in a hostname is therefore a useful, if narrow, structural signal: legitimate services almost
always choose memorable, brandable domain names, while both DGA-based malware infrastructure and
certain automated/throwaway phishing kits produce or reuse randomised subdomains and domains.

## Distinguishing this from ordinary phishing infrastructure

Most phishing domains are chosen *for* their resemblance to a trusted brand, which is the
opposite goal of a DGA domain. High-entropy hostnames are more often associated with malware
C2, automatically generated hosting-platform subdomains, or throwaway infrastructure than with
brand-impersonation phishing specifically - useful context when weighing an entropy-based
indicator alongside brand-lookalike and keyword-based indicators.
