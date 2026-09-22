---
title: Business email compromise (BEC)
source_name: Original content (this project)
source_url: https://www.ic3.gov/PSA/2023/PSA230609
license: Original content (this project)
topic: phishing
mitre_techniques:
  - T1566.002
  - T1598
---

# Business email compromise (BEC)

Business email compromise is a targeted variant of phishing aimed at initiating a fraudulent
wire transfer, payroll change, or vendor payment by impersonating an executive, finance
contact, or trusted vendor - either from a look-alike domain or from a genuinely compromised
mailbox. Unlike bulk phishing, BEC is usually low-volume and highly researched: the attacker
studies the target organisation's real vendors, executives, and email conventions first (a
reconnaissance step MITRE ATT&CK tracks as T1598, Phishing for Information), then sends one
carefully written message rather than a mass campaign.

## Typical pattern

1. A message arrives that appears to be from a real executive or vendor, often with urgency
   ("I need this processed before end of day, I'm in meetings").
2. It asks for a wire transfer, a change of bank details on an existing invoice, or purchase of
   gift cards.
3. The sending domain is a close look-alike of the real one (a single added/swapped character,
   or a different top-level domain), or the reply-to address differs from the visible sender name.

## Why URL/domain analysis still matters for BEC

Even though BEC often relies on a convincing email body rather than a malicious link, any link
included (an "updated invoice" portal, a "verify new bank details" form) is analysed the same
way as any other phishing URL: domain age, registrar, DNS records, and structural indicators are
all still meaningful evidence, because the attacker's infrastructure is usually assembled
quickly and cheaply for the specific campaign.
