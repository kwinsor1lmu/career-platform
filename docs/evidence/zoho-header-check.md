# Zoho header check

Checks whether mail sent from `ken@kenwinsor.xyz` passes SPF, DKIM, and DMARC at the receiving end. Private message contents and full addresses are redacted.

**Status: Unverified. Kenneth, fill in the blanks below.** Template created 2026-10-26.

## How to get the headers

1. From Zoho webmail, send a new message from `ken@kenwinsor.xyz` to your outside mailbox (your school account).
2. In the outside mailbox, open the message and choose **Show original** (Gmail) or **View message source** (Outlook).
3. Copy only these header lines into the block below: `Authentication-Results`, `DKIM-Signature` (the `d=` and `s=` parts are enough), `Return-Path`, and `From`. Redact your outside address.

## Message tested

| | |
|---|---|
| Sent | `____-__-__ __:__ PDT` |
| From | `ken@kenwinsor.xyz` |
| To | outside mailbox (redacted) |
| Subject | `____` |

## Header excerpt

```text
(paste the redacted header lines here)
```

## Results

| Check | Result | What it means |
|---|---|---|
| SPF | `spf=____` | Whether Zoho's sending server is allowed by `v=spf1 include:zohomail.com ~all` |
| DKIM | `dkim=____` (`d=kenwinsor.xyz`, `s=zmail`) | Whether the signature matches the key at `zmail._domainkey.kenwinsor.xyz` |
| DMARC | `dmarc=____` | Whether SPF or DKIM passed *and* matched the From domain `kenwinsor.xyz` (policy `p=none`) |

Shown as the sender in the outside mailbox: `____` (should be `ken@kenwinsor.xyz`).

## If a check didn't pass

Explain what you saw, what you checked (for example `nslookup -type=TXT zmail._domainkey.kenwinsor.xyz`), and what's still unresolved.
