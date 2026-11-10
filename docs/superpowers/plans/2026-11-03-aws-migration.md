# AWS Migration (EC2 + Single-AZ RDS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a verified copy of career-platform on AWS at `aws.kenwinsor.xyz` (EC2 t3.micro + Single-AZ RDS PostgreSQL 18), restored from the Railway backup, while Railway keeps serving `kenwinsor.xyz`.

**Architecture:** One Ubuntu 26.04 EC2 instance in us-east-1a runs nginx (TLS via Let's Encrypt) in front of uvicorn on 127.0.0.1:8000 under systemd, exactly like the Azure VM. The app connects over verified TLS to a private RDS PostgreSQL 18.6 instance in the same AZ, as a least-privilege `career_app` login. No application code changes.

**Tech Stack:** AWS CLI v2 (profile `isba-4775`), EC2, RDS PostgreSQL 18.6, Ubuntu 26.04, systemd, nginx, certbot, uv + Python 3.12, PostgreSQL 18 client, Cloudflare CLI.

**Spec:** Guide sections 7–11 (https://raw.githubusercontent.com/LMU-ISBA/isba-4775-fa26/main/guides/aws-migration.md), `docs/aws-migration-decision.md`, and the backup record in `docs/aws-migration-notes.md`.

## Global Constraints

- Every AWS command: `--profile isba-4775`, region `us-east-1`. Never root. In Git Bash, `export MSYS_NO_PATHCONV=1` first.
- Stay inside `ISBA4775EC2Migration`: EC2 `t3.micro`, IMDSv2 `required` in the launch command; RDS `db.t4g.micro`, Single-AZ, 20 GB, encrypted, not publicly accessible. Never use AdministratorAccess to get past a denial; decode it with `aws sts decode-authorization-message`.
- Don't upgrade the plan, buy support, or touch Cloudflare records other than the new `aws` A record. Railway and its database keep running; `kenwinsor.xyz` DNS is unchanged until Task 8, which needs separate approval.
- Secrets (RDS master password, `career_app` password, SSH private key) never go in chat, Git, or command output. Local copies live in `C:\Users\kenne\Secrets\career-platform\` (outside the repo).
- Work on branch `aws-migration`. Before any push, confirm in the Railway dashboard (career-platform → Settings → Source) that Railway deploys only `main`.
- Never run the Azure deploy script or any seed script on AWS. The only content load is `scripts/dev.sh`'s ingest at service start.
- Compare table hashes with `PGTZ=UTC` and `diff --strip-trailing-cr`.
- Log every deviation in `docs/aws-migration-notes.md` under the task's heading.

## Names and values

| Thing | Value |
| --- | --- |
| AZ / subnet | `us-east-1a` / `subnet-0be565ddfa84e77ac` (default VPC `vpc-0f40dbefab9ac2f36`) |
| Web security group | `career-platform-web-sg`: 22 from `<my IP>/32`, 80 and 443 from `0.0.0.0/0` |
| DB security group | `career-platform-db-sg`: 5432 only from `career-platform-web-sg` |
| Key pair | `isba4775-aws`, imported from `~/.ssh/isba4775_aws.pub` (ed25519, passphrase, loaded in the Windows ssh-agent) |
| RDS | `career-platform-db`, postgres 18.6, `db.t4g.micro`, 20 GB gp3 encrypted, no autoscaling, backups 7 days (window 10:00–10:30 UTC), maintenance Sun 10:30–11:00 UTC, deletion protection on, master user `postgres_admin` |
| App database / login | `career_platform`, owned by `career_app` |
| Instance | `career-platform-web`, t3.micro, Ubuntu 26.04 amd64 from SSM `/aws/service/canonical/ubuntu/server/26.04/stable/current/amd64/hvm/ebs-gp3/ami-id`, 20 GB gp3 encrypted, IMDSv2 required, CPU credits standard |
| Elastic IP | tag `Name=career-platform-eip` |
| Server paths | code `/home/ubuntu/career-platform`, env `/etc/career-platform.env` (root 600), unit `/etc/systemd/system/career-platform.service`, nginx `/etc/nginx/sites-available/career-platform`, RDS CA `/etc/ssl/rds/global-bundle.pem`, master creds `/root/.pgpass` (600) |
| Test hostname | `aws.kenwinsor.xyz`, A record, DNS only (grey cloud) |

## Review Focus

- **My IP changes (home ↔ school):** SSH times out. Expected fix is revoking/re-adding the port 22 rule for the new `/32`, never opening `0.0.0.0/0`. Task 2 records the exact two commands in the notes.
- **RDS TLS verification fails** (missing CA bundle, wrong hostname): the service fails at `alembic upgrade` instead of silently falling back to an unverified connection. Task 5 checks `sslmode=verify-full` with `psql` before the service ever starts.
- **Boot-time ingest deletes rows not in `resume.json`:** a test row inserted with SQL disappears on restart. Task 7's test record goes through `resume.json` on the branch, and the plan never inserts content with SQL.
- **t3.micro runs out of memory** during `uv sync` or with 2 workers: the install or service is OOM-killed. Task 4 adds a 1 GiB swap file before installing, and Task 7's reboot check confirms it persists.
- **Cost after teardown:** an unattached Elastic IP or a stopped RDS instance keeps billing (and RDS restarts itself after 7 days). The teardown checklist in Task 8 releases the EIP and deletes RDS with a final snapshot, and verifies both with `describe-*`.

---

### Task 1: Hash script, SSH key, and security groups (guide §7–8 prerequisites)

**Files:**
- Create: `docs/aws-migration-table-hashes.sql` (the per-table count + MD5 query from section 2, unchanged)
- Modify: `docs/aws-migration-notes.md` (new `## Section 7–8` heading)

- [ ] **Step 1:** Save the section 2 hash query as `docs/aws-migration-table-hashes.sql`. Verify: run it against `career_restore_test` with `PGTZ=UTC`; `diff --strip-trailing-cr` against `C:\Users\kenne\Backups\career-platform\railway-20261103-135114.hashes.txt` prints nothing.
- [ ] **Step 2 (user, own terminal):** `ssh-keygen -t ed25519 -f $HOME\.ssh\isba4775_aws -C isba4775-aws` with a passphrase. In admin PowerShell, `Set-Service ssh-agent -StartupType Manual; Start-Service ssh-agent`, then (normal terminal) `ssh-add $HOME\.ssh\isba4775_aws`. Verify: `ssh-add -l` lists the key. The agent uses `C:\Windows\System32\OpenSSH\ssh.exe` for every SSH/SCP from here on, not Git Bash's `ssh`.
- [ ] **Step 3:** `aws ec2 import-key-pair --key-name isba4775-aws --public-key-material fileb://<pub>`; tag it. Verify: `describe-key-pairs` fingerprint matches `ssh-keygen -lf` of the `.pub` (ED25519, SHA256).
- [ ] **Step 4:** Find my public IP (`curl -s https://checkip.amazonaws.com`). Create both security groups in the default VPC with the rules in the table; the DB group's ingress uses `--source-group <web-sg-id>`, not a CIDR. Verify: `describe-security-groups` shows exactly those rules and nothing else inbound.
- [ ] **Step 5:** Record IDs, my IP, and the two "IP changed" commands (`revoke-security-group-ingress` old /32, `authorize-security-group-ingress` new /32) in the notes.

### Task 2: Create the RDS database (guide §7)

**Interfaces:** Consumes `career-platform-db-sg` from Task 1. Produces the RDS endpoint hostname and the master password file `C:\Users\kenne\Secrets\career-platform\rds-master-password.txt`.

- [ ] **Step 1:** Generate a 32-character password from `[A-Za-z0-9]` into the secrets file without printing it (e.g. Python `secrets`). Verify: file length is 32; nothing printed.
- [ ] **Step 2:** Show the user the full `aws rds create-db-instance` command with the password replaced by `****`, and wait for approval. Flags: every RDS value in the table plus `--no-multi-az --no-publicly-accessible --storage-encrypted --no-manage-master-user-password --vpc-security-group-ids <db-sg> --availability-zone us-east-1a --copy-tags-to-snapshot --tags Key=Name,Value=career-platform-db`. No `--max-allocated-storage`.
- [ ] **Step 3:** Run it once, passing the password from the file (`--master-user-password "$(cat …)"`). Don't wait for it; move to Task 3.
- [ ] **Step 4 (later, after Task 3):** Verify with `describe-db-instances`: `DBInstanceStatus=available`, `PubliclyAccessible=false`, `MultiAZ=false`, `AvailabilityZone=us-east-1a`, `DBInstanceClass=db.t4g.micro`, `AllocatedStorage=20`, `StorageType=gp3`, `StorageEncrypted=true`, `BackupRetentionPeriod=7`, `DeletionProtection=true`, `EngineVersion=18.6`, and VPC SG = `career-platform-db-sg` only. User also checks the console (Endpoints → Additional configurations → Publicly accessible: No). Record the endpoint in the notes.

### Task 3: Launch the EC2 instance and Elastic IP (guide §8)

**Interfaces:** Consumes key pair and `career-platform-web-sg` from Task 1. Produces instance ID, Elastic IP, and a verified `known_hosts` entry.

- [ ] **Step 1:** Resolve the AMI ID from SSM; confirm with `describe-images` that it's Canonical (owner `099720109477`), `x86_64`, and the name contains `ubuntu-` and `server` but not `pro`.
- [ ] **Step 2:** Show the user the full `aws ec2 run-instances` command and wait for approval. It must include `--instance-type t3.micro --key-name isba4775-aws --subnet-id subnet-0be565ddfa84e77ac --security-group-ids <web-sg> --metadata-options HttpTokens=required,HttpEndpoint=enabled --credit-specification CpuCredits=standard --block-device-mappings` (root `/dev/sda1`, 20 GB, gp3, encrypted, delete on termination) and `Name=career-platform-web` tags on the instance and volume.
- [ ] **Step 3:** Launch once. On a denial, decode the message and report which statement fired; don't retry with changed sizes.
- [ ] **Step 4:** Allocate an Elastic IP (tag `career-platform-eip`) and associate it with the instance. Verify: `describe-addresses` shows the association.
- [ ] **Step 5:** Wait for `get-console-output` to contain the `BEGIN SSH HOST KEY FINGERPRINTS` block. Compare its ED25519 fingerprint with `ssh-keyscan -t ed25519 <EIP> | ssh-keygen -lf -`. Only if they match, add the key to `known_hosts`. Verify: `ssh ubuntu@<EIP> 'hostname; lsb_release -ds'` connects without a host-key prompt and prints Ubuntu 26.04.
- [ ] **Step 6:** User checks the console Instances page: ID, public IP = EIP, security group, 20 GiB encrypted gp3 volume, IMDSv2 required. Record in the notes.

### Task 4: Prepare the server

**Interfaces:** Produces `/home/ubuntu/career-platform/.venv` (Python 3.12) and installed `nginx`, `certbot`, `psql`/`pg_restore` 18.

- [ ] **Step 1:** Create and enable a 1 GiB `/swapfile` (in `/etc/fstab`). Verify: `swapon --show` lists it.
- [ ] **Step 2:** `apt update && apt full-upgrade`, then install `nginx certbot python3-certbot-nginx postgresql-client-18 git`. Confirm `unattended-upgrades` is enabled. Verify: `pg_restore --version` ≥ 18.6, `nginx -v`, `certbot --version`.
- [ ] **Step 3:** Download the RDS CA bundle from `https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem` to `/etc/ssl/rds/global-bundle.pem` (root-owned, 644).
- [ ] **Step 4:** Install uv with Astral's standalone installer as `ubuntu`; record the version. Clone `https://github.com/kwinsor1lmu/career-platform.git` into `/home/ubuntu/career-platform` and check out the `main` commit Railway is serving (record SHA). Run `uv sync --frozen --no-dev --python 3.12`. Verify: `.venv/bin/python --version` is 3.12.x and `.venv/bin/uvicorn --version` works.

### Task 5: Database login, restore, and first start (guide §9)

**Interfaces:** Consumes RDS endpoint (Task 2), server from Task 4, dump `railway-20261103-135114.dump` and its hashes file. Produces a running `career-platform` systemd service.

- [ ] **Step 1:** Copy the master password to the server's `/root/.pgpass` (600) by piping the local file over SSH, never as a command argument. Verify as root: `psql "host=<endpoint> dbname=postgres user=postgres_admin sslmode=verify-full sslrootcert=/etc/ssl/rds/global-bundle.pem" -Atc "select version(), ssl from pg_stat_ssl where pid=pg_backend_pid()"` prints PostgreSQL 18.6 and `t`.
- [ ] **Step 2:** Generate the `career_app` password on the server (root, not printed). As master, run: `CREATE ROLE career_app LOGIN PASSWORD …`, `CREATE DATABASE career_platform OWNER career_app`, `REVOKE ALL ON DATABASE career_platform FROM PUBLIC`. Verify: `\l career_platform` shows owner `career_app`; connecting as `career_app` to the `postgres` database is still possible but `CREATE DATABASE` as `career_app` fails.
- [ ] **Step 3:** Write `/etc/career-platform.env` (root 600): `ENVIRONMENT=production`, `DATABASE_URL=postgresql+psycopg://career_app:<pw>@<endpoint>:5432/career_platform?sslmode=verify-full&sslrootcert=/etc/ssl/rds/global-bundle.pem`, `CONTENT_PATH=content/resume.json`, `FALLBACK_PATH=data/fallback.json`, `HOST=127.0.0.1`, `PORT=8000`, `WEB_CONCURRENCY=2`, `GA_MEASUREMENT_ID=` (empty: test traffic stays out of the production GA property until cutover).
- [ ] **Step 4:** `scp` the dump to `/home/ubuntu/` and verify its SHA-256 equals `2cd8a79c…85d04fefa`. Restore as `career_app` with `pg_restore --no-owner --no-privileges --exit-on-error` into the empty `career_platform`, timing it. Verify: hash query (PGTZ=UTC) on RDS matches the Railway hashes file exactly. Delete the dump from the server.
- [ ] **Step 5:** Write the systemd unit: `User=ubuntu`, `WorkingDirectory=/home/ubuntu/career-platform`, `EnvironmentFile=/etc/career-platform.env`, `Environment=PATH=/home/ubuntu/career-platform/.venv/bin:/usr/bin:/bin`, `ExecStart=/home/ubuntu/career-platform/scripts/dev.sh`, `Restart=on-failure`, `RestartSec=5`, `After=network-online.target`, `Wants=network-online.target`, `WantedBy=multi-user.target`. Enable and start.
- [ ] **Step 6:** Verify: `journalctl -u career-platform` shows `alembic` (no new migrations), validate and ingest succeed, and uvicorn starts 2 workers on 127.0.0.1:8000; `curl -s 127.0.0.1:8000/health` returns `{"status":"ok"}`; `ss -tlnp` shows nothing new listening on a public address. Re-run the hash query: still matches Railway (ingest made no changes). Any mismatch is a finding to report, not to fix silently.

### Task 6: DNS, nginx, and HTTPS on the test name (guide §10 first half)

- [ ] **Step 1:** nginx site for `server_name aws.kenwinsor.xyz` proxying to `http://127.0.0.1:8000` with `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto` headers; disable the default site. Verify: `nginx -t` passes; `curl -H 'Host: aws.kenwinsor.xyz' http://<EIP>/health` returns ok.
- [ ] **Step 2:** Show the user the Cloudflare CLI command, then add **only** `A aws → <EIP>`, proxied false, TTL auto. Verify: CLI lists the record; user confirms the grey cloud and unchanged apex/www/mail (MX, SPF, DKIM, DMARC) records in the dashboard; `nslookup aws.kenwinsor.xyz 1.1.1.1` returns the EIP.
- [ ] **Step 3:** `certbot --nginx -d aws.kenwinsor.xyz --redirect` with the user's email. Verify: `curl -sI http://aws.kenwinsor.xyz` → 301 to https; `curl -s https://aws.kenwinsor.xyz/health` → ok with a valid cert; `certbot renew --dry-run` succeeds; `systemctl list-timers` shows certbot's timer. User checks the padlock.

### Task 7: Verify the AWS copy (guide §10 second half)

**Files:** Modify `content/resume.json` (temporary test skill), `docs/aws-migration-notes.md`.

- [ ] **Step 1:** Record the deployed commit on the server and compare with Railway's; pages `/`, `/privacy`, `/health`, `/static/styles.css`, a font file, and an unknown path (404) return the same status on both hosts, and `/` shows the same resume content.
- [ ] **Step 2 (test record):** On `aws-migration`, add a skill with `id` `aws-migration-test` and name `AWS migration test (remove before cutover)` to `content/resume.json`; `python scripts/validate_content.py content/resume.json` passes; commit. After the user confirms Railway deploys only `main`, push the branch. On the server, check out the branch and `systemctl restart career-platform`. Verify: the skill shows on `https://aws.kenwinsor.xyz/`, the `skills` count on RDS is 9, and after a second restart it's still there. `kenwinsor.xyz` still shows 8 skills.
- [ ] **Step 3 (reboot):** `sudo reboot`. Verify after it returns: swap active, service active without manual action, `/health` ok over HTTPS, still 9 skills.
- [ ] **Step 4 (security):** From the laptop, `Test-NetConnection <rds-endpoint> -Port 5432` fails (private); `Test-NetConnection <EIP> -Port 8000` fails; SSH works from my IP. Re-run the Task 2 Step 4 and Task 3 Step 6 checks for sizes and settings.
- [ ] **Step 5:** Write every check, its evidence, and anything not verified into the notes. Commit the notes, the hash script, and this plan (no secrets, no dumps).

### Task 8: Cutover and teardown (guide §11, needs separate approval)

Not run in this session unless every Task 7 check passed and the user approves. When it is: revert the test skill on the branch and redeploy; take a final Railway dump (new temporary SSH key, removed afterward) and restore it to RDS; issue the production certificate for `kenwinsor.xyz` and `www` with DNS-01 before moving traffic; save the existing apex record; stop the Railway web service; change only the apex record; set `GA_MEASUREMENT_ID=G-RDD033RLK7`; verify production. Rollback: restore the saved apex record and restart Railway, reconciling any rows written on AWS first.

**Teardown checklist (whenever AWS is retired):** final RDS snapshot then delete (`--final-db-snapshot-identifier`, after turning off deletion protection); terminate the instance; release the Elastic IP; delete security groups and the key pair; delete the `aws` DNS record; verify each with `describe-*` and the Billing console; `aws logout --profile isba-4775`.
