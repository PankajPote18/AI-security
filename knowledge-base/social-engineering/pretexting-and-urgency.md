---
title: Pretexting and urgency language
source_name: Original content (this project)
source_url: https://www.cisa.gov/topics/cyber-threats-and-advisories/social-engineering
license: Original content (this project)
topic: social-engineering
mitre_techniques:
  - T1598
---

# Pretexting and urgency language

A pretext is the fabricated story an attacker builds to make an unusual request seem normal - a
fake invoice, a fake password-expiry notice, a fake package delivery problem, a fake HR policy
update. A good pretext answers, in advance, the questions a suspicious target might ask: why is
this happening, why now, and why me.

## Why urgency is nearly universal in phishing

Urgency exists to short-circuit verification. A target who is told "your account will be locked
in one hour" is far less likely to open a new browser tab and navigate to the real site directly,
or to call the sender to confirm, than one who has time to think. Common urgency framings include
account suspension, unusual sign-in activity, payment failure, expiring access, and legal or
compliance deadlines.

## Pretexting as reconnaissance

Sophisticated pretexts are sometimes built from real information gathered about the target
beforehand - a real vendor name, a real project name, a real recent event at the target's
company. MITRE ATT&CK tracks this reconnaissance activity as T1598 (Phishing for Information):
messages sent specifically to elicit information (rather than to deliver a payload directly),
which is then used to make a later, more convincing attack.

## Why this is hard to detect from a URL alone

Pretexting and urgency live in the message text, not the URL - which is exactly why this
project treats the ML/structural/infrastructure analysis of the URL as necessary evidence rather
than sufficient evidence on its own, and why an AI-generated explanation should describe what
the URL evidence shows without claiming to have read or verified the surrounding message.
