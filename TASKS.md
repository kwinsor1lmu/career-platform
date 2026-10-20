# Project 1 gaps

From the repo audit on 2026-10-20. Due Thursday, 2026-10-22, 1:45 PM. Each line gives the gap, then what closes it.

## Blockers

- [ ] Real resume and Railway fixes exist only on `railway-migration`, not `main`: merge it, then `content/resume.json` on `main` no longer says "Ada Example"
- [ ] Domain suspended by Namecheap: `dig NS kenwinsor.xyz` returns `brit`/`rocco.ns.cloudflare.com`

## 1. Personal application

- [ ] No projects in the database: a projects table in `app/models.py` plus a new migration in `alembic/versions/`, ingested from `content/resume.json`
- [ ] Outage serves the full fallback with 200: when the DB fails, the profile stays visible, the page shows "Projects temporarily unavailable" and returns 503, checked in `tests/integration/test_database_outage.py`
- [ ] Fallback copy may count as substituted sample data: reword or remove in `app/services/resume.py`
- [ ] No test that projects return after recovery without a restart: new test in `tests/integration/`
- [ ] Database choice not explained: a section in `README.md`

## 2. Azure deployment

- [ ] Operate-the-VM plan not committed: commit `docs/superpowers/plans/2026-10-01-operate-the-vm.md`
- [ ] No results for the firewall (Section 3) or outside checks (Section 4): results tables in that plan
- [ ] No controlled restart test: dated `sudo reboot` result in that plan, with the site back afterward
- [ ] No crash test: dated `kill -9` worker/supervisor results in that plan
- [ ] HTTPS/certbot setup steps not recorded: add to that plan or `docs/how-this-site-is-secured.md`

## 3. Domain and HTTPS

- [ ] Cloudflare DNS records not documented: a records table (name, type, value, DNS-only/proxied) in `README.md` or `docs/`
- [ ] Railway plan makes `www` DNS-only, but the brief wants it proxied: fix Task 6 in `docs/superpowers/plans/2026-10-07-railway-migration.md`
- [ ] Bare domain not on Railway: `curl -sI https://kenwinsor.xyz/` returns 200 from Railway with a valid certificate
- [ ] `www` redirect unchecked: `curl -sI http://www.kenwinsor.xyz/` and `curl -sI https://www.kenwinsor.xyz/` both redirect to `https://kenwinsor.xyz/`
- [ ] Railway certificate not verified: `openssl s_client` output (hostname, validity, renewal) in `docs/how-this-site-is-secured.md`
- [ ] Ex05 uses the supplied simulation, not your domain: keep it labeled as simulated, and write up a real DNS/TLS failure in `README.md`

## 4. Railway and PostgreSQL migration

- [ ] Tasks 4–7 not run: results recorded in `docs/superpowers/plans/2026-10-07-railway-migration.md`
- [ ] PostgreSQL compatibility check not recorded: Task 4 rehearsal results
- [ ] No real change to project data: a committed change to `content/resume.json` shown live
- [ ] Source and target data not compared: row counts and a public-data diff, VM vs Railway
- [ ] Rendered pages not compared: VM vs Railway page diff
- [ ] Target not tested before the domain moved: `*.up.railway.app` checks recorded before DNS changed
- [ ] No cutover record or post-cutover checks: dated cutover section with results
- [ ] Rollback covers DNS only: rollback that also handles writes made after cutover
- [ ] No Azure vs Railway responsibilities comparison: a section in `README.md`

## 5. Verified website update

- [ ] Railway auto-deploy from GitHub not shown: evidence (screenshot or deploy log) in `docs/evidence/`
- [ ] No reviewed and locally tested change: a commit with tests passing, recorded in the README or evidence
- [ ] Commit SHA not visible on the live site: the app shows the SHA (e.g. `/health` or a footer), matching `git rev-parse HEAD`
- [ ] No restore procedure that covers the database: a section in `README.md`
- [ ] Git history not scanned for secrets: `git log -p | grep -iE "password|postgresql://"` finds nothing sensitive

## 6. Zoho email

- [ ] Header check file missing: create `docs/evidence/zoho-header-check.md`
- [ ] SPF/DKIM/DMARC results missing: `spf=pass dkim=pass dmarc=pass` from Test 02's headers in `docs/evidence/ex06.md`
- [ ] MX/SPF/DKIM/DMARC records not documented: record values in `docs/evidence/ex06.md`
- [ ] No test before MX was published: record what happened (or say it was missed) in `docs/evidence/ex06.md`
- [ ] Outbound arrival unconfirmed: confirm Test 02 and the reply arrived in the outside mailbox, in `docs/evidence/ex06.md`
- [ ] Reply sent while DNS was suspended: re-send after DNS returns and note it in `docs/evidence/ex06.md`

## 7. GA4 analytics

- [ ] Page view and interaction not captured: Realtime or DebugView screenshot of `page_view` and `click` (with `link_url`/`outbound`) in `docs/evidence/`
- [ ] Click tracking relies on Enhanced Measurement, which isn't in the repo: record that it's enabled, or add a custom event in `app/static/consent.js`
- [ ] Browser-to-GA path not explained: a section in `README.md`
- [ ] Why the event matters not explained: a section in `README.md`
- [ ] Test went through a hosts-file override: re-test on the real domain after DNS returns

## 8. Engineering record

- [ ] `README.md` is only a heading: write site overview, setup and update steps
- [ ] No code and data rollback: section in `README.md`
- [ ] No Azure diagram (with email and GA): diagram in `README.md`
- [ ] No Railway diagram (with email and GA): diagram in `README.md`
- [ ] Migration not summarized: section in `README.md`
- [ ] No two decisions with alternatives: section in `README.md`
- [ ] No two investigated failures (one app/DB, one network/DNS/TLS): section in `README.md` (candidates: Windows fsync bug and SSH IP change in `docs/evidence/ex03.md`, Namecheap suspension in `docs/evidence/ex06.md`)
- [ ] No reflection: section in `README.md`
- [ ] No costs or trial end dates: section in `README.md`
- [ ] No limitations: section in `README.md`
- [ ] Submission index is incomplete: final commit SHA and all required links in `docs/project-1-submission.md`
- [ ] Agent-written plans not checked or labeled: check against the repo and label agent-assisted and retrospective writing
- [ ] Stray files at repo root: remove or move `task-5-report.md`–`task-8-report.md` and `.superpowers/`
- [ ] Costs, trial dates and Brightspace submission can't be checked from the repo: record them, then submit on Brightspace
