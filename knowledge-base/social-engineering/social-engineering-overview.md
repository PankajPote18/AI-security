---
title: Social engineering fundamentals
source_name: Original content (this project)
source_url: https://www.cisa.gov/topics/cyber-threats-and-advisories/social-engineering
license: Original content (this project)
topic: social-engineering
mitre_techniques:
  - T1566
---

# Social engineering fundamentals

Social engineering is the use of psychological manipulation to get a person to break normal
security procedure - hand over a password, approve a payment, disable a control, or grant
physical or system access - without any technical exploit being needed. Phishing is the most
common delivery mechanism for social engineering at scale, because email and messaging give an
attacker a cheap, repeatable way to reach a large number of targets.

## Core manipulation levers

- **Authority.** Impersonating a boss, IT department, law enforcement, or a well-known brand so
  the target complies without question.
- **Urgency and scarcity.** A deadline, a security "incident," or a limited-time offer that
  discourages the target from pausing to verify.
- **Social proof.** "Everyone on the team has already done this" or a message that appears to be
  part of an ongoing, legitimate thread.
- **Reciprocity and helpfulness.** Posing as someone who needs help (a "new employee" asking for
  a password reset, a "delivery driver" needing a gate code).
- **Fear.** Threats of account suspension, legal action, or financial loss.

## Common vectors beyond email

- **Vishing** (voice phishing): a phone call impersonating a bank, IT support, or executive.
- **Smishing** (SMS phishing): a text message with a malicious link, often abusing the smaller
  screen and shortened URLs to hide the real destination.
- **Quishing** (QR-code phishing): a QR code that leads to a phishing page, bypassing email link
  scanners because the URL is never rendered as text in the message.
- **Pretexting**: a fabricated scenario (a fake support ticket, fake job offer, fake vendor
  onboarding) built to justify an unusual request.

## Why this matters for URL analysis

Regardless of the delivery vector, the destination is very often a URL, and the same phishing
infrastructure (domain, hosting, page kit) is frequently reused across email, SMS, and QR-code
campaigns. Structural and infrastructure analysis of that URL is therefore useful evidence no
matter how the link reached the victim.
