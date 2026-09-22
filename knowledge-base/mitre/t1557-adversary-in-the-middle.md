---
title: "MITRE ATT&CK T1557 - Adversary-in-the-Middle"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1557/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1557
---

# MITRE ATT&CK T1557 - Adversary-in-the-Middle

**Tactic:** Credential Access, Collection

An adversary positions themselves between two communicating parties to intercept, log, or
manipulate the traffic between them. In the context of phishing, this describes a
reverse-proxy credential-harvesting kit: the victim's browser talks to the attacker's server,
which in turn talks to the real service on the victim's behalf, relaying every request and
response (including a real, successfully completed multi-factor authentication challenge) while
capturing the resulting authenticated session.

This is a materially more dangerous variant than a simple static clone of a login page, because
it defeats standard one-time-code MFA - see the authentication-fundamentals document for why
phishing-resistant methods (hardware keys, passkeys) are the effective defence, and the
credential-harvesting document for how these kits are typically built.

## Relationship to T1539

A successful AiTM phishing attack's payoff is usually the session token it captures, tracked
separately as T1539 (Steal Web Session Cookie) - T1557 describes the interception mechanism,
T1539 describes what is stolen through it.
