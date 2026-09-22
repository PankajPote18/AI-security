---
title: Typosquatting and brand-lookalike domains
source_name: Original content (this project)
source_url: https://attack.mitre.org/techniques/T1583/001/
license: Original content (this project)
topic: url-indicators
mitre_techniques:
  - T1583.001
---

# Typosquatting and brand-lookalike domains

Typosquatting registers a domain one small edit away from a real brand's domain - a swapped,
dropped, doubled, or visually similar character (`paypa1.com`, `gooogle.com`, `micr0soft.com`).
Combosquatting instead combines the real brand name with an unrelated word, usually one that
plays into a plausible pretext (`paypal-secure-login.com`, `apple-id-verify.com`).

## Where the brand name shows up matters

A brand name appearing as the **registered domain itself** (`paypal-secure.com`) is a direct
domain-level lookalike. A brand name appearing only in a **subdomain of an unrelated registered
domain** (`paypal.account-verify.example.net` - where `example.net` is the actual registered
domain, and `paypal` is just a subdomain label the domain's owner can set to anything) is an even
cheaper trick: the attacker does not need to register anything brand-specific at all, only add a
subdomain to infrastructure they already control. Both are meaningfully different from the brand's
real domain simply containing its own name as a subdomain of *itself*
(`mail.paypal.com` - here the registered domain, `paypal.com`, genuinely is the brand's).

## Why this needs the registered-domain boundary, not string matching alone

Correctly distinguishing these cases requires knowing where the actual registered domain
boundary falls - including handling registrable suffixes correctly for hosting platforms
(`tenant.web.app`, where `web.app` itself functions as the effective registration boundary,
rather than a plain top-level domain) - not just checking whether a brand name appears anywhere
in the hostname string.
