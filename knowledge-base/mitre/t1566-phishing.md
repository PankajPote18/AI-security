---
title: "MITRE ATT&CK T1566 - Phishing"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1566/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1566
---

# MITRE ATT&CK T1566 - Phishing

**Tactic:** Initial Access

Adversaries send phishing messages to gain access to victim systems. Phishing may be targeted
(spearphishing) or untargeted, and may be delivered via email, other messaging services, or
third-party services. All forms involve some type of social engineering, where the message is
designed to entice or pressure the recipient into performing an action, such as opening a
malicious file (T1566.001), clicking a malicious link (T1566.002), or providing sensitive
information via a fraudulent form (T1566.003, Spearphishing via Service).

Phishing is one of the most common ways adversaries gain an initial foothold in a target
environment, because it requires no technical vulnerability in the target's systems - only a
successful deception of one person.

## Sub-techniques most relevant to URL analysis

- **T1566.002 - Spearphishing Link**: the message contains a malicious link rather than an
  attachment.
- **T1566.001 - Spearphishing Attachment**: the message contains a malicious file (out of scope
  for a URL-focused analysis tool, but often paired with a link in the same campaign).
- **T1566.003 - Spearphishing via Service**: delivery through a third-party service (social
  media, a messaging platform) rather than email.
