# AWS migration notes

Running log for the Railway → AWS (EC2 + RDS) move. Deviations from the plan are marked **Deviation**.

## Section 2: Railway backup and restore test (2026-11-03)

**Route.** Railway's Postgres service has no public TCP proxy (`DATABASE_PUBLIC_URL` is not set), so instead of exposing it I ran `pg_dump` inside the Postgres container over `railway ssh` and base64-encoded the stream back to the laptop. The database was never given a public address.

- Temporary SSH key `railway-backup` (ed25519, `SHA256:pA0INPcFj2AKhGe8qFEv6BkkEZIawc8XFnkO4GojbsM`), registered for the dump, then removed from Railway and deleted locally the same day.
- `ssh.railway.com` host key, trusted on first use (Railway publishes no fingerprint): `ED25519 SHA256:+S1xg92FrnHz6pY3bpkmh1OGtWQGNANXilPzlxA7B1g`.

**Backup.**

| Item | Value |
| --- | --- |
| Taken | 2026-11-03 21:51:16 UTC (13:51 PST) |
| Source | Railway project `illustrious-eagerness`, environment `production`, service `Postgres`, database `railway`, PostgreSQL 18.6 |
| Tool | `pg_dump` 18.6, custom format, `--no-owner --no-privileges` |
| File | `C:\Users\kenne\Backups\career-platform\railway-20261103-135114.dump` (outside the repo) |
| Size / SHA-256 | 37,922 bytes / `2cd8a79cd8bc8333757a26f0f4249d29fe9ef99e1386322e89b6cb085d04fefa` |
| Dump time | 3 s |

**Restore test** into a new local database `career_restore_test` (PostgreSQL 18.6 on the laptop, listening on localhost only). Railway was not queried during the checks.

| Check | Result |
| --- | --- |
| Restore time | 0.37 s (`pg_restore --exit-on-error`, no errors) |
| Row counts | certifications 0, contact_links 1, educations 1, experiences 1, profiles 1, projects 1, skills 8, alembic_version 1 (`0002`), identical to Railway |
| Content | Per-table MD5 over every row's text form identical to Railway for all 8 tables (`railway-20261103-135114.hashes.txt` vs `restore-test.hashes.txt`, both with session TimeZone UTC) |
| Representative records | Profile "Kenneth Winsor", project "kenwinsor.xyz — this resume site" |
| Restored app | uvicorn against `career_restore_test` with the fallback file pointed at a missing path: `/health`, `/`, `/privacy`, `/static/styles.css` all 200, page shows the real resume |

Uploaded files: none. The app stores no uploads; `data/fallback.json` is regenerated from the database by the ingest.

Gotcha: the first hash comparison differed on every table with timestamps because the laptop's session TimeZone is America/Los_Angeles and Railway's is UTC. Comparing with `PGTZ=UTC` matched.

**Recovery targets** (proposed, to confirm):

- **RPO:** the database content is regenerated from `content/resume.json` in Git on every boot, so the effective data-loss window is zero for anything committed. The dump covers the gap if the database ever holds rows the JSON doesn't.
- **RTO:** 30 minutes to a working copy (restore is under a second; the time is provisioning and DNS).
- **Frequency:** a dump before each migration step that touches data, and a final dump right before cutover.
- **Retention:** keep every migration dump until a month after cutover; RDS keeps its own automated backups on top of that (1 day on the Free plan, see Task 2).

**Independent copy:** TODO, copy the `Backups\career-platform` folder to independent storage (OneDrive or USB).

## Section 6: plan and cost estimate (2026-11-03)

Plan: `docs/superpowers/plans/2026-11-03-aws-migration.md`, approved. Decisions from the interview: systemd + venv (uv, Python 3.12) instead of Docker; keep the boot-time ingest, with the section 10 test record as a temporary `resume.json` skill; a separate `career_app` database login, master credentials kept for admin.

**Cost estimate.** Prices from AWS's public price-list files for us-east-1 (EC2 published 2026-11-03, RDS 2026-10-29, VPC 2026-11-03), on-demand, 730 h/month. The IAM user is denied `pricing:GetProducts`, and the aws-mcp server wasn't loaded yet.

| Item | Rate | Month |
| --- | --- | --- |
| EC2 t3.micro Linux | $0.0104/h | $7.59 |
| EBS gp3 root, 20 GB | $0.08/GB-mo | $1.60 |
| Elastic IP / public IPv4 | $0.005/h | $3.65 |
| RDS db.t4g.micro Single-AZ PostgreSQL | $0.016/h | $11.68 |
| RDS gp3 storage, 20 GB | $0.115/GB-mo | $2.30 |
| RDS backups | free up to 20 GB (= provisioned storage) | $0.00 |
| Data out to internet, ~2 GB | free under 100 GB/mo, then $0.09/GB | $0.00 |
| Cross-AZ transfer | $0.01/GB, avoided by same AZ | $0.00 |
| CPU credits | EC2 standard mode can't bill; RDS t4g is unlimited, $0.075/vCPU-h only under sustained load | $0.00 |
| **Total** | | **$26.82/month (~$0.88/day)** |

Matches the guide's ~$26.

## Task 1: key pair and security groups (2026-11-03)

- Key pair `isba4775-aws` (`key-0c65aeabd0d27351c`), ed25519, imported from `~/.ssh/isba4775_aws.pub` (passphrase, loaded in the Windows ssh-agent). AWS fingerprint `0Nlnz0JVH4LHOv7mWsF9SPSVnCT+SVlvBt7gjzAETjI=` matches `ssh-keygen -lf`.
- `career-platform-web-sg` = `sg-06d2e3aeafb8bac6e`: inbound 22 from my school and home /32s (addresses kept out of the repo), 80 and 443 from 0.0.0.0/0. Outbound: default all.
- `career-platform-db-sg` = `sg-0be0ac673f298c5e3`: inbound 5432 only from `sg-06d2e3aeafb8bac6e`, no IP ranges. Outbound: default all (RDS doesn't initiate connections).
- **Deviation:** SSH allows two /32s (school and home), as on the Azure VM, instead of one "my IP".
- If my IP changes (check `curl -s https://checkip.amazonaws.com`):
  `aws ec2 revoke-security-group-ingress --group-id sg-06d2e3aeafb8bac6e --protocol tcp --port 22 --cidr <old>/32 --profile isba-4775`
  `aws ec2 authorize-security-group-ingress --group-id sg-06d2e3aeafb8bac6e --ip-permissions 'IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=<new>/32,Description=home}]' --profile isba-4775`

Hash script saved as `docs/aws-migration-table-hashes.sql`; re-run against `career_restore_test` still matches Railway.

## Task 2: RDS database (2026-11-03)

- Master password: 32 random alphanumerics in `C:\Users\kenne\Secrets\career-platform\rds-master-password.txt` (owner-only ACL), passed to AWS through a temporary `--cli-input-json` file that was deleted right after, never as a command argument or in output.
- First attempt failed with Windows Python not resolving `/c/...` paths; nothing was sent. Second attempt was refused with `FreeTierRestrictionError: The specified backup retention period exceeds the maximum available to free tier customers`.
- **Deviation:** automated backups are kept **1 day**, not 7. Seven requires upgrading the plan, which is out of scope. The independent `pg_dump` exports outside AWS (section 2) carry the longer retention instead; take one after the restore in Task 5 and before cutover.
- Created `career-platform-db` (2026-11-03 ~23:20 UTC): db.t4g.micro, Single-AZ us-east-1a, not publicly accessible, encrypted 20 GB gp3, PostgreSQL 18.6, deletion protection on, backup window 10:00–10:30 UTC, maintenance Sun 10:30–11:00 UTC.

## Task 3: EC2 instance and Elastic IP (2026-11-03)

- AMI `ami-0bfc5cae5711ffac8` from SSM: owner 099720109477 (Canonical), x86_64, `ubuntu-resolute-26.04-amd64-server-20261028`, UsageOperation `RunInstances` (no Pro/license charge).
- Instance `i-06aa9ef646aa0e11a` (`career-platform-web`): t3.micro, us-east-1a, `career-platform-web-sg`, key `isba4775-aws`, IMDSv2 required, CPU credits standard. Launched first try, no denials.
- Root volume `vol-066ef03b4573f84d3`: 20 GiB gp3, encrypted, delete on termination.
- Elastic IP `44.215.219.249` (`eipalloc-0e794ad24922bfcbb`, association `eipassoc-06c468fc425a81085`).
- SSH host key: console output (cloud-init, 23:21:53 UTC) lists ED25519 `SHA256:SomWCOdvfmqg0l2gpFuS0gMbHxxkp6jWmaKkVSSRBCE`; `ssh-keyscan` of the Elastic IP returned the same, so it was added to `known_hosts`. First SSH with `StrictHostKeyChecking=yes` succeeded: Ubuntu 26.04.1 LTS, x86_64, 908 MiB RAM, 19 GiB root. IMDS without a token returns 401 (IMDSv2 enforced).
- RDS endpoint: `career-platform-db.c6fg6waywlcg.us-east-1.rds.amazonaws.com`.

## Railway trial ended (found 2026-11-09)

`https://kenwinsor.xyz` returns Railway's fallback 404 (`x-railway-fallback: true`), and `railway service status --all` shows both `career-platform` and `Postgres` with NO DEPLOYMENT. The README had estimated the trial would end about 2026-11-07. **Deviation:** there is no Railway to keep serving during testing, and no final Railway dump is possible; the 2026-11-03 dump is the final backup. Data loss is nil in practice because all content comes from `content/resume.json` in Git, and the dump equals it. The site is down until cutover.

## Task 2 check (2026-11-09)

`describe-db-instances`: available, PubliclyAccessible false, MultiAZ false, us-east-1a, db.t4g.micro, 20 GB gp3 encrypted, MaxAllocatedStorage none (autoscaling off), BackupRetentionPeriod 1, DeletionProtection true, 18.6, only `sg-0be0ac673f298c5e3`.

## Task 4: server setup (2026-11-09)

- 1 GiB `/swapfile` in `/etc/fstab`; survived a reboot.
- `apt full-upgrade` pulled a new kernel; rebooted before setup (now `7.0.0-1017-aws`). `unattended-upgrades` enabled with daily lists and upgrades.
- Installed nginx 1.28.3, certbot 4.0.0, postgresql-client-18 (`pg_restore` 18.6), git 2.53.0.
- RDS CA bundle (114 certs) at `/etc/ssl/rds/global-bundle.pem`.
- uv 0.13.7; cloned the repo at `d594399` (the last `main` commit Railway served); `uv sync --frozen --no-dev --python 3.12` → Python 3.12.16, uvicorn 0.54.0, alembic 1.20.0. No swap used.

## Task 5: database login, restore, first start (2026-11-09)

- Master credentials in `/root/.pgpass` (600, piped over SSH). `psql` as `postgres_admin` with `sslmode=verify-full` → PostgreSQL 18.6, `ssl=true TLSv1.3 TLS_AES_256_GCM_SHA384`.
- `career_app` password generated on the server into `/root/career_app.pw` (600), never printed. First attempt stopped at a `pipefail`/SIGPIPE from `tr | head`; switched to Python `secrets`.
- **Deviation (RDS behaviour):** `CREATE DATABASE … OWNER career_app` failed with `must be able to SET ROLE "career_app"`, because the RDS master isn't a true superuser. Fixed with `GRANT career_app TO postgres_admin WITH SET TRUE, INHERIT FALSE`.
- `career_platform` owner `career_app`; `career_app` super=false, createdb=false, createrole=false; `CREATE DATABASE` as `career_app` → permission denied. `REVOKE ALL ON DATABASE career_platform FROM PUBLIC`.
- `/etc/career-platform.env` (root 600): production, `DATABASE_URL` with `sslmode=verify-full&sslrootcert=/etc/ssl/rds/global-bundle.pem`, HOST 127.0.0.1, PORT 8000, WEB_CONCURRENCY 2, `GA_MEASUREMENT_ID` empty during testing.
- Restore: dump SHA-256 on the server `2cd8a79c…85d04fefa` (matches); `pg_restore` as `career_app` took **0.26 s**; all 8 tables owned by `career_app`; **table hashes match Railway** for all 8 tables. Dump shredded from the server.
- systemd unit `career-platform.service` (User ubuntu, EnvironmentFile, `ExecStart=scripts/dev.sh`, `Restart=on-failure`), enabled. First start: alembic had nothing to apply, content validated, ingest published fallback, uvicorn 2 workers on 127.0.0.1:8000, `/health` ok. **Hashes still match Railway after the boot-time ingest.**
- Listening sockets: 127.0.0.1:8000 (uvicorn), 80 (nginx), 22 (sshd). Port 8000 from the internet: unreachable.

## Task 6: nginx and DNS (2026-11-09)

- nginx site `career-platform` for `aws.kenwinsor.xyz` → `127.0.0.1:8000` with Host/X-Forwarded-* headers; default site removed. `curl -H 'Host: aws.kenwinsor.xyz' http://44.215.219.249/health` → ok.
- DNS before the change: apex CNAME → `0z13fs8z.up.railway.app` (DNS only), `www` A 192.0.2.1 proxied (redirect rule), Zoho MX ×3, SPF, DKIM, DMARC, zoho-verification, `_railway-verify` TXT.

Cost note: $100 of credits covers about 3.7 months. Credits are applied before Budgets counts cost, so the zero-spend budget stays quiet until credits run out; watch the Credits page instead. Leftover risks: an idle Elastic IP still costs $3.65/month after the instance is gone, and a stopped RDS instance still bills storage and restarts after 7 days.

- 2026-11-10 07:08 UTC: created `aws` A 44.215.219.249, DNS only (grey cloud), TTL auto (user ran `cf dns records create`; Claude Code's permission check blocks agent-made changes to the live zone). Before/after diff: 1 added, 0 removed, 10 unchanged. `nslookup aws.kenwinsor.xyz 1.1.1.1` → 44.215.219.249.
- `certbot --nginx -d aws.kenwinsor.xyz --redirect --register-unsafely-without-email` (no email sent to Let's Encrypt; renewal is automatic). Cert CN `aws.kenwinsor.xyz`, issuer Let's Encrypt YE2, valid 2026-11-10 to 2027-02-08. `http://` → 301 to HTTPS. `certbot renew --dry-run` succeeded; `certbot.timer` active.

## Task 7: verification (2026-11-10)

Railway is down (trial ended), so the comparison baseline is the restored data and the repo, not the old live site. `kenwinsor.xyz` returned Railway's 404 throughout.

| Test | Evidence | Result |
| --- | --- | --- |
| Deployed code | Server on `d594399` (last `main` Railway served), then `dd6e272` (test skill) | Pass |
| `/` | 200 text/html, 7,597 B, title "Kenneth Winsor \| …" | Pass |
| `/privacy` | 200 text/html, 8,673 B | Pass |
| `/health` over HTTPS | 200 application/json | Pass |
| `/static/styles.css` | 200 text/css, 10,067 B | Pass |
| Font file | `/static/fonts/ibm-plex-sans-400.woff2` 200 font/woff2, 22,588 B (same as repo) | Pass |
| Unknown path | `/nope-404` → 404 | Pass |
| HTTPS | Let's Encrypt cert for `aws.kenwinsor.xyz`, HTTP → 301 | Pass |
| Data matches backup | Table hashes match Railway after restore and after the boot ingest (Task 5) | Pass |
| Change survives restart | Test skill `AWS migration test (remove before cutover)` committed as `dd6e272`, copied to the server as a git bundle (not pushed). After restart: shown on page, RDS `skills` = 9. After a second restart: still 9. | Pass |
| Survives reboot | `sudo reboot`; site back in ~15 s; swap on, service + nginx active with no manual step; test skill still shown; RDS `skills` = 9 | Pass |
| Cert renewal | `certbot renew --dry-run` success; timer active | Pass |
| RDS private | `Test-NetConnection` endpoint:5432 from laptop → False (resolves to private 172.31.15.230); PubliclyAccessible false; DB SG allows 5432 only from the web SG | Pass |
| App port closed | EIP:8000 → False; EIP:5432 → False | Pass |
| SSH limited | EIP:22 → True from my IP; SG allows 22 from two /32s only | Pass |
| IMDSv2 | `HttpTokens required`; tokenless request on the instance → 401 | Pass |
| Sizes in policy | t3.micro; db.t4g.micro, Single-AZ, 20 GB, encrypted, PostgreSQL 18.6, deletion protection on | Pass |
| Automated backups | Retention 1 day (Free plan limit, deviation); latest restorable 2026-11-10 07:10 UTC | Pass (with deviation) |
| Analytics | `GA_MEASUREMENT_ID` empty on the test copy on purpose | Not verified (set at cutover) |
| Independent backup copy | Dumps only on the laptop | Not verified (user to copy) |
