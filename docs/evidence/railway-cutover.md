# Railway cutover record

All checks run on 2026-10-26 (PDT) from my laptop with Claude Code, unless a line says otherwise. **Clock note:** the laptop clock was found to be about 7 minutes slow that night (compared with a web server's `Date` header). Laptop-based times below, including Git's push times, may read about 7 minutes early. Certificate dates and Railway/Zoho timestamps come from the servers. Commands are shown with their actual results. Written up the same evening, after the work. The plan these steps follow, written beforehand: [2026-10-07-railway-migration.md](../superpowers/plans/2026-10-07-railway-migration.md).

## Before the cutover: domain restored

The site and mail had been down since about Oct 16, because Namecheap suspended the domain for an unverified registrant email (see [ex06.md](ex06.md#failed-check-domain-dns-suspended)).

```text
$ nslookup -type=NS kenwinsor.xyz 8.8.8.8          # before verifying
kenwinsor.xyz  nameserver = verify-contact-details.namecheap.com
kenwinsor.xyz  nameserver = failed-whois-verification.namecheap.com
$ nslookup kenwinsor.xyz 8.8.8.8
Address:  198.54.117.242                            # Namecheap parking IP, not the VM
```

After I verified the contact email in Namecheap, the `.xyz` registry (RDAP at `rdap.centralnic.com`) listed `brit.ns.cloudflare.com` and `rocco.ns.cloudflare.com` again. Once caches expired, Google (`8.8.8.8`) and Cloudflare (`1.1.1.1`) DNS returned `20.88.59.204`, the VM.

## Deploying the target before moving the domain

1. **Rebased the migration branch onto `main`.** `main` had gained the redesign, privacy page, and consent banner since the plan was written, so the plan's fast-forward no longer applied. Rebased cleanly; full suite `51 passed`.
2. **Railway Postgres from the laptop: not possible.** The plan's Task 4 (migrate and ingest through Railway's public proxy, then compare) failed with `FATAL: password authentication failed for user "postgres"` at `iriguchi.proxy.rlwy.net:26007`, both with the old password and the current one. Instead, Railway ran the migration and ingest itself on deploy (`scripts/dev.sh`), and I compared the rendered pages.
3. **Railway before the push** (`career-platform-production-54b9.up.railway.app`, running an older `main`):
   ```text
   $ curl -s $H/health                       → {"status":"ok"}
   $ curl -s $H/ | grep -o "Ada Example"     → 5 matches (the placeholder)
   $ curl -s $H/ | grep -o '<link rel="stylesheet"[^>]*>'
   <link rel="stylesheet" href="http://career-platform-production-54b9.up.railway.app/static/styles.css">   # http:// → mixed content
   ```
4. **Pushed** `railway-migration` to `main` at 12:38 PDT (`b2a00ed..000bc92`). Railway served the new version about 45 seconds later.
5. **Railway after the push:**
   ```text
   $ curl -s $H/health                       → {"status":"ok"}
   $ grep -c "Kenneth Winsor"                → 5;  "Ada Example" → 0
   <link rel="stylesheet" href="https://career-platform-production-54b9.up.railway.app/static/styles.css">
   $ curl -s -o /dev/null -w "%{http_code} %{content_type}" $H/static/styles.css   → 200 text/css; charset=utf-8
   $ curl -s -o /dev/null -w "%{http_code}" $H/privacy                             → 200
   ```

## Source vs target comparison

I stripped the HTML tags from both pages and compared the text line by line (`diff vm.txt railway.txt`). The VM was reached directly with `curl --resolve kenwinsor.xyz:443:20.88.59.204`.

| Difference | Why | Resolved |
|---|---|---|
| JSON-LD `"url"`: `https://kenwinsor.xyz/` vs `https://career-platform-production-54b9.up.railway.app/` | The app builds it from the host it's served on | Yes, after the domain moved |
| Cookie banner missing on Railway | `GA_MEASUREMENT_ID` wasn't set on Railway | Yes. Set to `G-RDD033RLK7` (the VM's ID), clicked **Deploy**; the banner and ID appeared about 20 seconds later |

No other line differed: the name, headline, summary, experience, education, all 8 skills, and the contact link matched the VM.

**Not done:** a row-level comparison of the VM's SQLite tables with Railway's Postgres tables, because the laptop can't reach Railway Postgres (step 2). The real-data change is commit [f6b65fa](https://github.com/kwinsor1lmu/career-platform/commit/f6b65fa): it replaced the repo's placeholder with my real resume, which until then existed only in the VM's database. A placeholder restored to Railway would have shown "Ada Example", and the comparison above would have caught it.

## Cutover

1. **Railway custom domain.** Added `kenwinsor.xyz` (Railway's trial allows one). Railway gave `CNAME @ → 0z13fs8z.up.railway.app` and `TXT _railway-verify → railway-verify=b43f…3b88`.
2. **Cloudflare.** Deleted `A @ 20.88.59.204` (the rollback value) and added the CNAME (DNS only) and the TXT record. Changed `www` to a proxied `A 192.0.2.1` and added a Redirect Rule: `www.kenwinsor.xyz` → 301 to `https://kenwinsor.xyz` plus the path, keeping the query string. Partway through, I removed and re-added the zone in Cloudflare. It got the same `brit`/`rocco` nameservers and kept its records, so no change was needed at Namecheap.
3. **Certificate stalled.** DNS checked out:
   ```text
   $ nslookup kenwinsor.xyz brit.ns.cloudflare.com        → 69.46.46.115 (= 0z13fs8z.up.railway.app)
   $ nslookup -type=TXT _railway-verify.kenwinsor.xyz 8.8.8.8 / 1.1.1.1 / 9.9.9.9   → "railway-verify=b43f…3b88"
   CAA, AAAA (dns.google/resolve)                            → none
   ```
   But for over an hour, `openssl s_client` still showed `subject=CN=*.up.railway.app`, so browsers refused the site. Railway's Networking tab showed a yellow warning on the TXT record.
4. **Temporary workaround.** I set the apex CNAME to **Proxied** and Cloudflare SSL to **Full**. Cloudflare's certificate then worked, but Railway answered `{"status":"error","code":404,"message":"Application not found"}`, even when reached directly at `69.46.46.115`. Railway wasn't routing the domain to the app at all.
5. **Fix.** Deleted and re-added the custom domain in Railway. Both records showed green checks. The site returned 200 through Cloudflare, and Railway issued its own certificate within about 20 seconds (`notBefore=Oct 26 23:55:12 2026 GMT`).
6. **Back to DNS only.** Set the apex CNAME back to **DNS only**, as the course requires. `www` stays proxied for the redirect.

## Post-cutover checks

### HTTPS at the new destination

```text
$ echo | openssl s_client -connect kenwinsor.xyz:443 -servername kenwinsor.xyz 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
subject=CN=kenwinsor.xyz
issuer=C=US, O=Let's Encrypt, CN=YE1
notBefore=Oct 26 23:55:12 2026 GMT
notAfter=Jan 24 23:55:11 2027 GMT
X509v3 Subject Alternative Name:
    DNS:kenwinsor.xyz
$ curl -sI https://kenwinsor.xyz/ | grep -i ^server
server: railway-hikari
```

Railway renews this certificate itself. The VM's certificate (valid until Jan 4, 2027) stays on the VM for the rollback.

### Site and redirects

```text
$ curl -s https://kenwinsor.xyz/health                         → {"status":"ok"}
$ curl -s https://kenwinsor.xyz/ | grep -o '<link rel="stylesheet"[^>]*>'
<link rel="stylesheet" href="https://kenwinsor.xyz/static/styles.css">
$ curl -s https://kenwinsor.xyz/ | grep -c "Kenneth Winsor"     → 5
$ curl -s https://kenwinsor.xyz/ | grep -c "G-RDD033RLK7"       → 1   (consent banner present)
$ curl -s -o /dev/null -w "%{http_code}" https://kenwinsor.xyz/privacy   → 200
$ curl -s -D - -o /dev/null http://www.kenwinsor.xyz/  | grep -i ^location   → Location: https://kenwinsor.xyz/
$ curl -s -D - -o /dev/null https://www.kenwinsor.xyz/ | grep -i ^location   → Location: https://kenwinsor.xyz/
$ curl -s -D - -o /dev/null "https://www.kenwinsor.xyz/privacy?x=1"          → 301 to https://kenwinsor.xyz/privacy?x=1
```

Zoho's MX, SPF, DKIM (`zmail._domainkey`), and DMARC records were still served by Cloudflare after every DNS change.

## Rollback

Not needed. If it is: in Cloudflare, replace the `kenwinsor.xyz` CNAME with `A @ 20.88.59.204`, DNS only. The VM never stopped serving, with its own certificate. The site has no visitor writes, and its data comes from `content/resume.json`, so nothing written after the cutover can be lost by rolling back. The full procedure, including code and schema, is in the [README](../../README.md#roll-back-a-bad-change).

## Verified website update

The reviewed change for requirement 5: **projects read from the database, with a 503 when it's down** ([bdd262c](https://github.com/kwinsor1lmu/career-platform/commit/bdd262c)).

1. **Tests written first, and watched fail:** `tests/routes/test_projects.py`, `tests/integration/test_projects_recovery.py`, and `tests/repositories/test_public_projects.py` failed on import (`cannot import name 'get_public_projects'`).
2. **Implemented**, then checked locally:
   - The new tests: `10 passed`.
   - The full suite: `58 passed in 142.56s`.
   - On a fresh SQLite database: `alembic upgrade head` (`0001 → 0002`), ingest (`… 1 contact links, and 1 projects.`), `downgrade 0001`, `upgrade head`.
   - `validate_content.py`: `… 1 contact link, and 1 project records.`
3. **Reviewed** with `git diff --stat` before committing: 16 files changed, no secrets, no unrelated files.
4. **Before the push** (04:57:12 UTC): `curl -s https://kenwinsor.xyz/ | grep -c 'id="projects"'` → `0`.
5. **Pushed** at 21:57:16 PDT (`000bc92..bdd262c`). Railway deployed from GitHub. I didn't read the deploy log, so I'm inferring the migration and ingest from the result in step 6.
6. **Live at 04:57:55 UTC**, about 40 seconds after the push:
   ```text
   $ curl -s -o /dev/null -w "%{http_code}" https://kenwinsor.xyz/   → 200
   $ curl -s https://kenwinsor.xyz/ | grep -o 'kenwinsor.xyz — this resume site\|In progress\|href="https://github.com/kwinsor1lmu/career-platform"'
   kenwinsor.xyz — this resume site
   In progress
   href="https://github.com/kwinsor1lmu/career-platform"
   ```
   The project only exists in Postgres after the 0002 migration and the ingest, so seeing it live shows the deploy migrated and loaded Railway Postgres.

**Kenneth, to add:** a screenshot of Railway → Deployments showing commit `bdd262c` as Active. **Unverified** until it's added.

**Recovery:** see [Roll back a bad change](../../README.md#roll-back-a-bad-change). For this change: redeploy the `000bc92` deployment in Railway. The extra `projects` table doesn't affect the older code.
