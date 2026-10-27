# Project 1 submission

- Repository: https://github.com/kwinsor1lmu/career-platform
- Live site: https://kenwinsor.xyz/
- Final commit SHA: `________` (fill in from `git rev-parse HEAD` after the last evidence commit; the same SHA goes in Brightspace)

Items marked **Unverified** in the linked files still need evidence.

## 1. README, spec, and plans

- [README](../README.md)
- Original application spec: [2026-09-15-personal-resume-career-platform-design.md](superpowers/specs/2026-09-15-personal-resume-career-platform-design.md)
- Plans: [application](superpowers/plans/2026-09-15-personal-resume-career-platform.md) · [Azure VM migration](superpowers/plans/2026-09-24-azure-vm-migration.md) · [operate the VM](superpowers/plans/2026-10-01-operate-the-vm.md) · [Railway migration](superpowers/plans/2026-10-07-railway-migration.md)

## 2. Diagrams (Azure and Railway, with email and analytics)

- [README → Architecture](../README.md#architecture)
- [Request path, from Wi-Fi to the database](request-path-diagram.md)

## 3. Migration, data comparison, cutover, and rollback

- Plan and dependency inventory: [Railway migration plan](superpowers/plans/2026-10-07-railway-migration.md) · [README → Migration](../README.md#migration-to-railway-and-postgresql)
- Source vs target comparison, cutover, and post-cutover checks: [railway-cutover.md](evidence/railway-cutover.md)
- Rollback for code, data, schema, and hosting: [README → Roll back a bad change](../README.md#roll-back-a-bad-change)
- Responsibilities on Azure vs Railway: [README → Who manages what](../README.md#who-manages-what-azure-vs-railway)

## 4. Azure HTTP/restart evidence and final DNS/HTTPS

- Azure build and migration: [ex03.md](evidence/ex03.md) · [Azure migration plan results](superpowers/plans/2026-09-24-azure-vm-migration.md)
- systemd, Nginx, and firewall setup with results: [operate-the-vm plan](superpowers/plans/2026-10-01-operate-the-vm.md). The controlled VM restart is **Unverified** (see README → Limitations).
- HTTPS on the VM (my Exercise 04 explanation): [how-this-site-is-secured.md](how-this-site-is-secured.md)
- Final DNS records and `www` redirect checks: [README → DNS records](../README.md#dns-records)
- Final HTTPS on Railway: [railway-cutover.md → HTTPS at the new destination](evidence/railway-cutover.md#https-at-the-new-destination)

## 5. Reviewed change through Railway

- Commit [bdd262c](https://github.com/kwinsor1lmu/career-platform/commit/bdd262c): projects read from the database, with a 503 when it's down
- Tests, push, and the live result: [railway-cutover.md → Verified website update](evidence/railway-cutover.md#verified-website-update)
- Recovery: [README → Roll back a bad change](../README.md#roll-back-a-bad-change)

## 6. Zoho email

- Sending, receiving, and replying: [ex06.md](evidence/ex06.md)
- SPF, DKIM, and DMARC results: [zoho-header-check.md](evidence/zoho-header-check.md) (**Unverified** until filled in)
- Records and explanation: [README → Email](../README.md#email-zoho)

## 7. GA4

- [ex06.md → Google Analytics](evidence/ex06.md#3-google-analytics)
- How events get to Google, and why the click is useful: [README → Analytics](../README.md#analytics-ga4)

## 8. Failures, decisions, reflection, costs, and limitations

- [Investigated failures](../README.md#investigated-failures): [ex03.md](evidence/ex03.md) (application/dependency), the domain suspension and the Railway certificate stall (DNS/TLS), and [ex05.md](evidence/ex05.md) (deliberate lab simulation)
- [Decisions](../README.md#decisions)
- [Reflection](../README.md#reflection)
- [Costs, expiration dates, and cleanup](../README.md#costs-expiration-dates-and-cleanup)
- [Limitations](../README.md#limitations)

Earlier exercise evidence: [ex03.md](evidence/ex03.md) · [ex05.md](evidence/ex05.md) · [ex06.md](evidence/ex06.md)
