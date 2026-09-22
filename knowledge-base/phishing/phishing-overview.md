---
title: What phishing is and why it works
source_name: Original content (this project), concepts drawn from CISA and NIST public guidance
source_url: https://www.cisa.gov/topics/cyber-threats-and-advisories/phishing
license: Original content (this project)
topic: phishing
mitre_techniques:
  - T1566
---

# What phishing is and why it works

Phishing is a social engineering attack in which someone impersonates a trusted person,
brand, or system to trick a target into taking an action that benefits the attacker -
typically entering credentials, opening a malicious attachment, approving a fraudulent
payment, or installing malware. It is one of the most common initial-access techniques used
in real-world breaches because it attacks human trust and habit rather than a technical
vulnerability, and it scales cheaply: a single email template can be sent to thousands of
targets.

## Why it works

Phishing succeeds by combining three things:

1. **A plausible pretext.** The message looks like it comes from a bank, employer, delivery
   service, or colleague the target already has a relationship with.
2. **Urgency or fear.** "Your account will be suspended," "unusual sign-in detected," or "invoice
   overdue" push the target to act quickly instead of verifying.
3. **A low-friction path to the payoff.** A single click on a link, or opening one attachment, is
   all that is asked of the target - the attacker does the rest.

## The role of the URL

Most phishing that reaches a security tool for analysis arrives as a URL: a link in an email,
message, or search result that leads to a page designed to look like the real thing. The URL
itself often carries structural evidence of the deception even before the page loads - a domain
that is not the real brand's domain, an unusual top-level domain, a raw IP address instead of a
hostname, or a credential-related word stitched into a domain that has nothing to do with the
real service. See the URL-indicators and MITRE ATT&CK documents in this knowledge base for the
specific patterns.

## What phishing is not

Not every suspicious-looking URL is phishing, and not every phishing attempt is technically
sophisticated. A URL shortener, a long marketing tracking link, or an unusual but legitimate
country-code domain can all look "suspicious" by a naive rule while being entirely benign. This
is why a single structural indicator should be treated as evidence to weigh, not a verdict on
its own - the same principle this project's scoring policy is built around.
