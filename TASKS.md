# Project 1 gaps

From the repo audit on 2026-10-20 (due Thursday, 2026-10-22, 1:45 PM). **Status updated 2026-10-26.** Each line gives the gap, then what closed it or what's still needed.

## Blockers

- [x] Real resume and Railway fixes only on `railway-migration`: merged to `main` (000bc92); live site shows the real resume
- [x] Domain suspended by Namecheap: contact verified; registry lists `brit`/`rocco.ns.cloudflare.com` again

## 1. Personal application

- [x] Projects in the database: `projects` table (Alembic 0002), ingested from `content/resume.json` (bdd262c)
- [x] Outage behavior: profile visible, "Projects temporarily unavailable", 503 (`tests/integration/test_database_outage.py`)
- [x] Fallback copy: real published profile only, labeled as a saved copy; projects never come from it
- [x] Recovery without restart: `tests/integration/test_projects_recovery.py`
- [x] Database choice explained: README → What the site does

## 2. Azure deployment

- [x] Operate-the-VM plan committed
- [x] Outside checks: results table in the operate-the-VM plan (port 80 → 301, 8000 blocked, SSH from an allowed IP)
- [x] Controlled restart test: dated `sudo reboot` results in the operate-the-VM plan
- [x] Crash test: dated `kill -9` worker and supervisor results in the operate-the-VM plan
- [ ] HTTPS/certbot setup steps: only the result is recorded (`docs/how-this-site-is-secured.md`); the setup commands aren't

## 3. Domain and HTTPS

- [x] Cloudflare DNS records documented: README → DNS records
- [x] `www` proxied with a redirect rule (the plan's DNS-only `www` was superseded; see railway-cutover.md)
- [x] Bare domain on Railway with a valid certificate: railway-cutover.md
- [x] `www` redirect checked for http and https: README → DNS records
- [x] Railway certificate verified: railway-cutover.md → HTTPS at the new destination
- [x] Real DNS/TLS failures written up: the domain suspension and the Railway certificate stall (README → Investigated failures); Ex05 stays labeled as a simulation

## 4. Railway and PostgreSQL migration

- [x] Cutover run and recorded: docs/evidence/railway-cutover.md
- [ ] PostgreSQL rehearsal from the laptop: not possible (Railway public DB credentials don't work); the deploy ran the migrations instead
- [x] Real change to project data: f6b65fa (placeholder → real resume)
- [ ] Row-level source vs target comparison: not possible from the laptop; the rendered pages were compared instead
- [x] Rendered pages compared: railway-cutover.md
- [x] Target tested before the domain moved: railway-cutover.md
- [x] Cutover and post-cutover checks: railway-cutover.md
- [x] Rollback covering code, data, schema, and hosting: README → Roll back a bad change
- [x] Azure vs Railway responsibilities: README

## 5. Verified website update

- [ ] Railway deploy evidence: screenshot of Deployments showing `bdd262c` Active, still to add
- [x] Reviewed and locally tested change: bdd262c (59 tests passing)
- [ ] Commit SHA visible on the live site: not added; the SHA is linked through the push and live checks instead
- [x] Restore procedure covering the database: README
- [x] Git history scanned for secrets: nothing found (2026-10-26)

## 6. Zoho email

- [x] Header check file: docs/evidence/zoho-header-check.md
- [x] SPF/DKIM/DMARC results: all pass (2026-10-26)
- [x] Records documented: README → DNS records
- [ ] Test before MX was published: write what happened in ex06.md
- [x] Outbound arrival: Tests 02 and 04 and the reply arrived in the school mailbox (checked 2026-10-26)
- [x] Re-send after DNS returned: authentication check sent and verified on 2026-10-26

## 7. GA4 analytics

- [x] Page view and click captured: ex06.md (Realtime events and click parameters)
- [x] Click tracking: Enhanced Measurement outbound click (`link_url`, `link_domain`, `outbound` present)
- [x] Browser-to-GA path explained: README → Analytics
- [x] Why the event matters: README → Analytics and ex06.md
- [x] Re-tested on the real domain after DNS returned

## 8. Engineering record

- [x] README written, with all required sections
- [ ] Reflection in my own words (README has draft points)
- [x] Costs: Railway trial ends about 2026-11-07 ($4.22 left), domain $2, Azure $10.52 spent
- [ ] Azure credit remaining (optional; not available from the CLI)
- [x] Submission index with all required links
- [x] Agent-written docs labeled as agent-assisted and retrospective
- [x] Stray task reports moved to `docs/superpowers/reports/`
- [ ] Final commit SHA in the submission index, then submit on Brightspace
