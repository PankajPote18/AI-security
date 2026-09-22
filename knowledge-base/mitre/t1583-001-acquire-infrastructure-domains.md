---
title: "MITRE ATT&CK T1583.001 - Acquire Infrastructure: Domains"
source_name: MITRE ATT&CK
source_url: https://attack.mitre.org/techniques/T1583/001/
license: MITRE ATT&CK Terms of Use (content reuse permitted with attribution)
topic: mitre
mitre_techniques:
  - T1583.001
---

# MITRE ATT&CK T1583.001 - Acquire Infrastructure: Domains

**Tactic:** Resource Development (sub-technique of T1583, Acquire Infrastructure)

Adversaries register or otherwise acquire domains to be used during later stages of an attack -
most relevantly for phishing, as the host for a credential-harvesting page or a look-alike of a
trusted brand's login flow. Domains may be purchased new, or an expired domain with residual
reputation/backlinks may be re-registered specifically to inherit that reputation.

## Patterns commonly seen in phishing domain acquisition

- **Typosquatting**: a domain one character away from the target brand (`paypa1.com`,
  `micros0ft.com`).
- **Combosquatting**: the brand name combined with an unrelated word (`paypal-secure-login.com`).
- **Homograph domains**: visually similar Unicode characters encoded as punycode (see the
  dedicated punycode/homograph document).
- **Free or low-cost hosting subdomains**: rather than registering a domain at all, using a
  free tenant subdomain on a legitimate hosting platform, which inherits that platform's own
  (usually good) domain reputation.
- **Raw IP addresses**: skipping domain registration entirely and hosting the phishing page
  directly on an IP address, the fastest and cheapest option, and one of the strongest single
  structural indicators available since legitimate services essentially never do this for a
  public-facing login page.

## Why domain age is the natural evidence for this technique

Because acquiring infrastructure is typically the *last* step before a campaign launches (to
minimise the time a domain sits idle and visible to defenders before use), the domain's
registration date is one of the most direct available signals of T1583.001 activity - see the
domain-age-and-rdap document for detail and its limits.
