---
title: "MITRE ATT&CK T1598 - Phishing for Information"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1598/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1598
---

# MITRE ATT&CK T1598 - Phishing for Information

**Tactic:** Reconnaissance

Adversaries send messages designed to elicit sensitive information, rather than to deliver a
payload or credential-harvesting link directly. The goal is gathering information - confirming a
valid email address, learning an internal project name, identifying who handles finance or IT -
that is then used to make a *later* attack (often a spearphishing link, T1566.002, or a business
email compromise attempt) more convincing.

This distinguishes T1598 from T1566: T1598 is about the adversary learning something from the
target, while T1566 is about the adversary getting the target to take an action (click, open,
enter credentials). The two are frequently used together across a single campaign - a
reconnaissance message first, a targeted follow-up second.
