---
title: SPF, DKIM and DMARC (email authentication)
source_name: Original content (this project), concepts from RFC 7208, RFC 6376, RFC 7489
source_url: https://developer.mozilla.org/en-US/docs/Web/Security
license: Original content (this project)
topic: dns
---

# SPF, DKIM and DMARC (email authentication)

These three DNS-published mechanisms let a receiving mail server check whether an email claiming
to be "from" a domain was actually authorised by that domain - the primary technical defence
against domain spoofing in phishing email.

## SPF (Sender Policy Framework)

A TXT record listing which mail servers/IP ranges are allowed to send email for a domain. A
receiving server checks the sending IP against the domain's SPF record; a mismatch suggests the
message did not originate from an authorised source. SPF alone is weak because it only checks the
"envelope from" address, not the visible "from" header a user actually sees, and it breaks when
mail is forwarded.

## DKIM (DomainKeys Identified Mail)

A cryptographic signature added to outgoing mail, verifiable against a public key published in
the domain's DNS. DKIM proves the message was not altered in transit and was signed by a party
holding the domain's private key - stronger than SPF, but it says nothing about the visible
"from" address either.

## DMARC (Domain-based Message Authentication, Reporting and Conformance)

A policy, also published as a DNS TXT record, that tells receiving servers what to do when a
message fails SPF and/or DKIM alignment with the visible "from" domain - and ties both checks to
that visible domain, closing the gap SPF and DKIM leave individually. A domain with a strict
DMARC policy (`p=reject`) is telling the world that any message claiming to be from it, that
fails these checks, should be rejected outright.

## Relevance to URL/domain analysis

A legitimate organisation's *primary* domain having strong SPF/DKIM/DMARC does not mean a
look-alike domain used in a phishing campaign does - attackers rarely bother configuring email
authentication for throwaway infrastructure, since they are not trying to send authenticated
mail from it. This project focuses on URL and web infrastructure evidence rather than inspecting
email headers directly, but the same underlying idea applies: authentic, established
infrastructure tends to be more fully configured than infrastructure assembled quickly for a
single campaign.
