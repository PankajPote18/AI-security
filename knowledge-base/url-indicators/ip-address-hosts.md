---
title: Raw IP address hosts and obfuscated IP encodings
source_name: Original content (this project)
source_url: https://developer.mozilla.org/en-US/docs/Web/URI
license: Original content (this project)
topic: url-indicators
mitre_techniques:
  - T1583.001
  - T1027
---

# Raw IP address hosts and obfuscated IP encodings

A URL's host is normally a domain name (`example.com`); using a raw IP address instead
(`http://185.220.1.7/`) means there is no domain to check the age, registrar, or reputation of -
the infrastructure was likely assembled without ever registering a domain at all, one of the
cheapest and fastest ways to stand up a phishing page.

## Why legitimate services essentially never do this

Public-facing login pages, banking portals, and brand websites are built around a memorable
domain name for a reason: users need to recognise and trust it, and organisations need to
maintain a consistent brand presence, renew certificates for it, and configure DNS-based email
authentication (SPF/DKIM/DMARC) against it. None of that is possible against a bare IP address.
A raw IP host is one of the highest-confidence single structural indicators available, precisely
because it is a structural choice with essentially no legitimate use case for a consumer-facing
site.

## Obfuscated encodings

Attackers sometimes further encode the IP address so it does not *look* like an IP at a glance,
while the browser and server still resolve it correctly:

- **Decimal**: a full 32-bit IPv4 address written as one integer (`http://3232235521/` for
  `192.168.1.1`).
- **Hexadecimal**: each octet, or the whole address, written in hex (`http://0xC0.0xA8.0x01.0x01/`).
- **Octal**: each octet written with a leading zero (`http://0300.0250.0001.0001/`).

These are all valid per how browsers parse URLs, and exist specifically to survive a quick visual
check of the address bar - an instance of the general obfuscation pattern MITRE ATT&CK tracks as
T1027.
