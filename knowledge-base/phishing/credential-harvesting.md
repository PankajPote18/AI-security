---
title: Credential harvesting pages
source_name: Original content (this project)
source_url: https://www.cisa.gov/topics/cyber-threats-and-advisories/phishing
license: Original content (this project)
topic: phishing
mitre_techniques:
  - T1566.002
  - T1539
---

# Credential harvesting pages

A credential-harvesting page is a web page built to look identical to a real login form - for a
bank, email provider, cloud service, or internal company portal - so that when a victim enters
their username and password, the attacker captures them directly instead of the real service
ever seeing them.

## How the page gets built

Most credential-harvesting kits are near-pixel-perfect clones of the real site's login page:
copied HTML/CSS, the real brand's logo, and sometimes even a working "forgot password" link that
redirects to the real site (to avoid suspicion). The one thing that cannot be cloned is the
domain - a look-alike domain, a compromised legitimate site hosting the fake page in a
subdirectory, or a free hosting platform (a page builder, static site host, or developer
sandbox) is used instead, because the attacker does not control the real brand's DNS.

## What happens to stolen credentials

Captured credentials are typically sent immediately to the attacker (by a background HTTP
request or email), often before the victim is redirected to the real site to complete a
"successful" login and avoid raising suspicion. Stolen credentials are then reused directly
(if the victim reused the same password elsewhere), sold, or used to pivot into the victim's
real account for further attacks such as session-cookie theft, mailbox rule abuse, or
business email compromise.

## Session and MFA-aware variants

More advanced kits act as a **reverse proxy** between the victim and the real site: the victim
is really interacting with the genuine login flow, including a real multi-factor authentication
prompt, while the attacker's proxy captures the resulting session cookie in real time. This
defeats simple MFA (though not phishing-resistant methods like hardware security keys / WebAuthn)
because the attacker ends up with a live, already-authenticated session rather than just a
password. This class of attack is tracked as MITRE ATT&CK technique T1539 (Steal Web Session
Cookie) and is often delivered via a spearphishing link (T1566.002).

## Detection-relevant signals

- The domain does not match the brand being impersonated, even if the page content does.
- The domain is very new (see the domain-age document) or hosted on a generic platform.
- The page is served over plain HTTP, or has a certificate that does not match the brand.
- The URL contains login/verify/account/security-style keywords in the *domain itself*, not just
  the path - a pattern real brands rarely use for their primary login domain.
