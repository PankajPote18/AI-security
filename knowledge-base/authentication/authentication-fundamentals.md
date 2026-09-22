---
title: Authentication fundamentals
source_name: Original content (this project), concepts from OWASP Authentication Cheat Sheet
source_url: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
license: Original content (this project), concepts from OWASP (CC BY-SA 4.0)
topic: authentication
---

# Authentication fundamentals

Authentication is the process of proving identity to a system, almost always the first thing a
credential-harvesting phishing page attempts to imitate, because a convincing fake login form
is the single most valuable page an attacker can clone.

## Factors of authentication

- **Something you know**: a password or PIN - the factor phishing targets most directly, since
  it can be typed into a fake form and is immediately reusable by the attacker.
- **Something you have**: a phone, hardware key, or authenticator app generating a one-time code
  - the basis of most multi-factor authentication (MFA).
- **Something you are**: biometrics (fingerprint, face) - rarely phishable directly, since the
  data does not leave the device, but the *result* (a successful local unlock) can still be
  chained into a session an attacker intercepts downstream.

## Why MFA helps, but is not phishing-proof

Standard one-time-code MFA (SMS or authenticator app) stops an attacker who has only a stolen
password, but not an attacker running a real-time reverse-proxy kit (see the credential-
harvesting document) that relays the victim's live session, including a correctly entered MFA
code, straight through to the real service. **Phishing-resistant** authentication - hardware
security keys and passkeys using the WebAuthn/FIDO2 standard - defeats this class of attack
because the cryptographic proof of authentication is bound to the real site's exact domain and
cannot be replayed by an intermediary domain, even one with a valid TLS certificate.

## Session management

After successful authentication, a session token (often a cookie) stands in for repeated
password entry. Because that token is what the AiTM/session-theft techniques described elsewhere
in this knowledge base actually steal, session tokens should be treated with the same sensitivity
as a password: short lifetimes, secure/HttpOnly cookie flags, and invalidation on suspicious
activity all reduce the value of a stolen session to an attacker.
