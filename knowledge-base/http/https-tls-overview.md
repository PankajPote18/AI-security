---
title: HTTP, HTTPS and TLS fundamentals
source_name: Original content (this project), concepts from MDN Web Docs
source_url: https://developer.mozilla.org/en-US/docs/Web/Security/Transport_Layer_Security
license: Original content (this project)
topic: http
mitre_techniques:
  - T1557
---

# HTTP, HTTPS and TLS fundamentals

HTTP is the protocol browsers use to request and receive web pages. HTTPS is HTTP carried over
TLS (Transport Layer Security), which encrypts the connection between browser and server and lets
the browser cryptographically verify it is talking to the server it thinks it is talking to, via
a certificate issued for that specific domain.

## What HTTPS does and does not prove

HTTPS proves the connection is encrypted and that the certificate presented was issued for the
domain in the address bar - **it does not prove the domain is trustworthy, owned by a legitimate
brand, or safe**. Free, automated certificate issuance (widely available since the mid-2010s) has
made valid HTTPS certificates trivial for anyone to obtain for any domain they control, including
a phishing domain. A padlock icon means "this connection to *this domain* is encrypted," nothing
more.

## Why plain HTTP is still a useful signal

Despite the above, a URL still using plain HTTP rather than HTTPS is a meaningful signal in 2026:
HTTPS has been the overwhelming default for legitimate sites, browsers, and login forms for
years, and browsers actively warn users about non-HTTPS forms. A login or account-related page
served over plain HTTP is unusual enough, for a real brand, to be treated as a structural
indicator worth weighing - not because HTTP is inherently malicious, but because its absence
where it would normally be expected is informative.

## Adversary-in-the-middle (AiTM)

MITRE ATT&CK technique T1557 covers an attacker positioning themselves between a victim and a
legitimate service to intercept or manipulate traffic - the technical basis for the
reverse-proxy credential-and-session-harvesting kits described in the credential-harvesting
document. TLS protects against passive eavesdropping on the wire, but does nothing to stop a
victim being routed, by social engineering, straight to an attacker-controlled endpoint that
itself uses valid TLS.
