---
title: "MITRE ATT&CK T1566.002 - Phishing: Spearphishing Link"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1566/002/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1566.002
---

# MITRE ATT&CK T1566.002 - Phishing: Spearphishing Link

**Tactic:** Initial Access (sub-technique of T1566, Phishing)

Adversaries send messages containing a malicious link to gain access to victim systems. The link
usually leads to a credential-harvesting page disguised as a legitimate login, a page that
prompts a malicious download, or an OAuth-consent-style page that requests overly broad
permissions to the victim's account.

Unlike a malicious attachment, a spearphishing link often relies on infrastructure entirely
outside the target's own environment - a domain and hosting the attacker controls - which is
exactly the infrastructure a URL-analysis pipeline (domain age, DNS, structural indicators,
threat intelligence) is positioned to evaluate, even without ever needing to open the page
itself.

## Common delivery contexts

- Email, the most common vector historically.
- SMS ("smishing") and messaging apps, where shortened or obscured URLs are especially effective
  because of limited screen space.
- QR codes ("quishing"), which route around email link-scanning entirely since the URL is never
  rendered as clickable text until the code is scanned.
