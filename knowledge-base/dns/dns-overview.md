---
title: DNS fundamentals
source_name: Original content (this project), concepts from RFC 1035 and MDN
source_url: https://developer.mozilla.org/en-US/docs/Glossary/DNS
license: Original content (this project)
topic: dns
---

# DNS fundamentals

The Domain Name System (DNS) translates human-readable domain names (`example.com`) into the
numeric IP addresses computers use to route traffic. A domain's DNS records are one of the few
pieces of hard evidence available about a URL's infrastructure without visiting the page itself.

## Record types relevant to security analysis

- **A / AAAA records** map a hostname to an IPv4 / IPv6 address. Multiple A records (round-robin)
  are normal for large, established sites; a single, very recently allocated IP is more typical
  of throwaway phishing infrastructure.
- **MX records** specify which mail servers accept email for the domain. A domain with no MX
  records is unusual for an organisation claiming to be a bank or major service, though entirely
  normal for a domain that only hosts a web page.
- **NS records** specify the domain's authoritative name servers. Free or bulk registrar default
  name servers are common for both legitimate small sites and phishing infrastructure, so this
  alone is weak evidence; a match against a known bulletproof-hosting or abuse-associated name
  server range is stronger evidence.
- **TXT records** hold arbitrary text, commonly used for domain-ownership verification (see the
  DNS-authentication document for SPF/DKIM/DMARC, which are TXT-record-based).

## What a missing or failing DNS lookup means

A domain that returns NXDOMAIN (does not exist) or times out consistently is not currently
resolvable - which can mean a taken-down phishing domain, a typo, or simply a domain that was
never registered. A resolvable domain with only an A record and nothing else is common for
single-purpose phishing pages, which typically need nothing beyond serving one web page.

## Limits of DNS evidence alone

DNS records describe infrastructure, not intent - a domain can have perfectly normal-looking DNS
and still host a phishing page, especially if it is a compromised legitimate site rather than
attacker-registered infrastructure. DNS evidence is most useful combined with domain age (RDAP)
and the URL's own structural indicators.
