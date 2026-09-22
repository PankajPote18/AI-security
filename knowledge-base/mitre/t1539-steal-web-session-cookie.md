---
title: "MITRE ATT&CK T1539 - Steal Web Session Cookie"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1539/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1539
---

# MITRE ATT&CK T1539 - Steal Web Session Cookie

**Tactic:** Credential Access

An adversary steals a web application or service session cookie and uses it to gain access as
the already-authenticated user, without needing that user's actual password or MFA code. Because
the session is already fully authenticated, this bypasses MFA entirely - the theft happens
*after* the legitimate authentication has already succeeded.

## How the cookie is typically stolen in a phishing context

Most commonly via an adversary-in-the-middle phishing kit (T1557): the victim authenticates
through what looks like the real login flow (because, from a network standpoint, it substantially
is - the attacker's proxy relays it), and the attacker's proxy captures the session cookie issued
at the end of that flow. The victim may never notice anything wrong, since they typically end up
logged into the real service.

## Why this makes phishing detection time-sensitive

Once a session cookie is stolen this way, blocking the original phishing domain does not revoke
the already-stolen session - the value of catching this class of attack is highest *before* a
victim completes the flow, which is exactly the point at which URL and infrastructure analysis
(before the page is trusted enough to submit credentials into) is most useful.
