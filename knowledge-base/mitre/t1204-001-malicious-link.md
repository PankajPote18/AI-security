---
title: "MITRE ATT&CK T1204.001 - User Execution: Malicious Link"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1204/001/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1204.001
---

# MITRE ATT&CK T1204.001 - User Execution: Malicious Link

**Tactic:** Execution (sub-technique of T1204, User Execution)

An adversary relies on a user clicking a malicious link. This technique is closely related to,
but distinct from, T1566.002 (Spearphishing Link): T1566.002 describes *delivering* the link,
while T1204.001 describes the *user taking the bait* and clicking it - the step where the attack
actually succeeds from the adversary's point of view.

## Why this framing matters for URL analysis

T1204.001 is a reminder that URL-based phishing is fundamentally a human-in-the-loop attack: all
of the technical evidence a URL-analysis pipeline gathers (domain age, DNS, structural
indicators, ML classification) exists to help a person decide *not* to complete this step,
before or immediately after clicking, rather than to detect an attack that has already fully
executed without any user action.

## Classic URL tricks that specifically target this moment of decision

The `@`-symbol userinfo trick (everything before an `@` in a URL's authority is discarded by the
browser as login credentials, letting an attacker put a trusted-looking string there while the
real host follows the `@`) and visually similar internationalised domains (see the punycode
document) both exist specifically to survive a user's last glance at the URL before clicking.
