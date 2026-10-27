# Zoho header check

Checks whether mail sent from `ken@kenwinsor.xyz` passes SPF, DKIM, and DMARC at the receiving end.

Run 2026-10-26 by Claude Code at my request, through the Zoho Mail API (MCP) in my account. The receiver was Port25's public authentication verifier, `check-auth@verifier.port25.com`, which replies with the results it saw when the message arrived. A school-inbox check wasn't used because the agent can't read that mailbox.

## Message tested

| | |
|---|---|
| Sent | Mon, 26 Oct 2026 22:41:34 -0700 (PDT), from Zoho webmail's API |
| From | `ken@kenwinsor.xyz` |
| To | `check-auth@verifier.port25.com` |
| Subject | `SPF DKIM DMARC check for kenwinsor.xyz` |
| Sending server | `sender6-of-o55.zoho.com` (165.173.180.55) |
| Received by Port25 | Tue, 27 Oct 2026 05:41:39 +0000 |

## Header excerpt (from Port25's "Authentication Report", which quotes the message as received)

```text
Return-Path: <ken@kenwinsor.xyz>
Received: from sender6-of-o55.zoho.com (165.173.180.55) by verifier.port25.com id hs0sp63bka8g
  for <check-auth@verifier.port25.com>; Tue, 27 Oct 2026 05:41:39 +0000 (envelope-from <ken@kenwinsor.xyz>)
Authentication-Results: verifier.port25.com; spf=pass smtp.mailfrom=ken@kenwinsor.xyz;
  iprev=pass (matches sender6-of-o55.zoho.com) policy.iprev=165.173.180.55;
  dkim=pass (matches From: ken@kenwinsor.xyz) header.i=ken@kenwinsor.xyz
ARC-Authentication-Results: i=1; mx.zohomail.com;
  dkim=pass header.i=kenwinsor.xyz;
  spf=pass smtp.mailfrom=ken@kenwinsor.xyz;
  dmarc=pass header.from=<ken@kenwinsor.xyz>
DKIM-Signature: v=1; a=rsa-sha256; q=dns/txt; c=relaxed/relaxed; t=1793079696;
  s=zmail; d=kenwinsor.xyz; i=ken@kenwinsor.xyz; …
From: ken@kenwinsor.xyz
```

DNS records the verifier looked up:

```text
kenwinsor.xyz. 300 IN TXT "v=spf1 include:zohomail.com ~all"
zohomail.com. IN TXT "v=spf1 include:spf.zohomail.com -all"
spf.zohomail.com. IN TXT "v=spf1 … ip4:165.173.180.0/24 … -all"
zmail._domainkey.kenwinsor.xyz. 300 IN TXT "v=DKIM1; k=rsa; p=MIGfMA0GCSq…"   (1024-bit key)
55.180.173.165.in-addr.arpa. PTR sender6-of-o55.zoho.com.
```

## Results

| Check | Result | What it means |
|---|---|---|
| SPF | `spf=pass` | The sending IP 165.173.180.55 is in Zoho's range `165.173.180.0/24`, which my SPF record includes through `include:zohomail.com` |
| DKIM | `dkim=pass`, `d=kenwinsor.xyz`, `s=zmail` | Zoho signed the message with my domain's key, and the signature matched the public key at `zmail._domainkey.kenwinsor.xyz` |
| DMARC | `dmarc=pass` (from Zoho's `ARC-Authentication-Results`) | The From domain is `kenwinsor.xyz`, and both SPF (mail-from `ken@kenwinsor.xyz`) and DKIM (`d=kenwinsor.xyz`) passed for that same domain, so DMARC alignment holds. My policy is `p=none`, so a failure would only be reported, not rejected |
| iprev | `pass` | The sending IP's reverse DNS (`sender6-of-o55.zoho.com`) points back to the same IP |

Port25 itself doesn't evaluate DMARC. The `dmarc=pass` line is the evaluation recorded by Zoho's mail servers in the ARC header. Alignment follows from the SPF and DKIM results above.

The sender the receiver saw: `From: ken@kenwinsor.xyz`.
