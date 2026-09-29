# Azure VM Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the personal resume platform on `vm-career-platform`, serving the laptop's SQLite data, and prove it from the VM.

**Architecture:** One Ubuntu 24.04 VM runs the app as a single uvicorn process from a git checkout, with dependencies installed by uv from a committed lock file. The SQLite file is copied from the laptop with scp. uvicorn listens on `127.0.0.1:8000` only; the laptop reaches it through an SSH tunnel, so no web port is opened to the internet.

**Tech Stack:** Azure VM (Ubuntu 24.04, `Standard_B2ats_v2`, North Central US), apt, git, uv 0.10.11, Python 3.12, FastAPI/uvicorn, SQLite, Alembic.

**Spec:** The eight-step migration plan the user gave in the 2026-09-24 session (Server → Packages → Code → Python → Config → Data → Processes → Verify). No separate spec file.

## Global Constraints

- VM: `vm-career-platform` in resource group `rg-career-platform`, public IP `20.88.59.204`.
- SSH user `azureuser`, key `~/.ssh/isba4775_azure`, on every `ssh`/`scp`.
- Laptop public IPv4 is written here as `<LAPTOP_IP>` (not published). SSH is opened to `<LAPTOP_IP>/32` only.
- Repo: `https://github.com/kwinsor1lmu/career-platform` (public), cloned to `/home/azureuser/career-platform` on the VM.
- Data source: `C:\Users\kenne\Downloads\app.db`, SHA-256 `b817b95cc91783f23116a9b12f7d3fcbcd2f958e10fea525fd505407799eded4`, Alembic revision `0001`.
- `ENVIRONMENT` must stay `development`: `app/config.py` rejects SQLite when `ENVIRONMENT=production`.
- `DATABASE_URL=sqlite:///./data/app.db` is relative, so every app command runs with the repo root as its working directory.
- Do **not** start the app with `scripts/dev.sh`: it re-ingests `content/resume.json` into the database on every start and would overwrite the copied data.
- Azure CLI on the laptop is not on PATH. In PowerShell, set `$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"` and call `& $az ...`.

## Review Focus

1. **The data file was replaced on 2026-09-29.** `Downloads\app.db` now holds Kenneth Winsor's profile (loaded from `Downloads\kenneth-resume.json`); the demo version is backed up as `Downloads\app.db.bak-2026-09-29`. Re-check the hash in Step 6.1 if the file changes again.
2. **No lock file exists yet.** The repo has no `uv.lock`, so "uv sync from the lock file" would fail. The Python section creates and commits one first.
3. **`dev.sh` overwrites data.** Starting through `scripts/dev.sh` or Docker Compose would replace the copied rows with `content/resume.json`. The Processes step calls uvicorn directly.
4. **The fallback can hide a broken database.** If the database is unreadable, `/` silently serves `data/fallback.json`. The VM never gets a fallback file, so a page with data on it can only have come from the database.
5. **The process ends when the VM reboots.** `nohup` survives logging out of SSH, not a reboot or VM stop. Making it a systemd service is out of scope for this plan.

## Rollback (whole migration)

Run in order; each is also listed in its own step.

1. VM: `kill "$(cat ~/uvicorn.pid)"`
2. VM: `rm -rf ~/career-platform ~/uvicorn.log ~/uvicorn.pid`
3. VM: `rm -f ~/.local/bin/uv ~/.local/bin/uvx`
4. Laptop: delete the SSH rules (Server, Step 1 undo).

The VM, its disk, and the laptop's `Downloads\app.db` are left unchanged.

---

## 1. Server

### Step 1.1: Allow SSH from the laptop only

- [x] **Where:** Laptop (PowerShell).
- **Run:** First see which NSGs are attached, because traffic has to pass both a subnet NSG and a NIC NSG:

  ```powershell
  $az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
  & $az network nsg list -g rg-career-platform --query "[].{nsg:name, nics:length(networkInterfaces||``[]``), subnets:length(subnets||``[]``)}" -o table
  ```

  For **each** NSG with a nonzero `nics` or `subnets` count, add the rule (replace `<NSG>`):

  ```powershell
  & $az network nsg rule create -g rg-career-platform --nsg-name <NSG> -n AllowSSHFromLaptop --priority 1000 --direction Inbound --access Allow --protocol Tcp --source-address-prefixes <LAPTOP_IP>/32 --destination-port-ranges 22
  ```

- **Why:** The VM was created with no inbound ports open, so SSH is blocked until now. Allowing only the laptop's `/32` keeps port 22 closed to everyone else.
- **Check:** `& $az network nsg rule list -g rg-career-platform --nsg-name <NSG> -o table` shows `AllowSSHFromLaptop` with source `<LAPTOP_IP>/32`.
- **Undo:** `& $az network nsg rule delete -g rg-career-platform --nsg-name <NSG> -n AllowSSHFromLaptop` for each NSG.

### Step 1.2: First SSH login

- [x] **Where:** Laptop (Git Bash).
- **Run:**

  ```bash
  ssh -i ~/.ssh/isba4775_azure -o StrictHostKeyChecking=accept-new azureuser@20.88.59.204 'hostname; lsb_release -ds; nproc; free -m | head -2'
  ```

- **Why:** Confirms the key, user, and firewall rule work, and records the VM's host key in `~/.ssh/known_hosts`.
- **Check:** Prints `vm-career-platform`, `Ubuntu 24.04...`, `2`, and about 900 MB total memory. If it times out, the NSG rule is missing on one of the NSGs, or the laptop's public IP has changed (`curl -4 https://api.ipify.org`).
- **Undo:** `ssh-keygen -R 20.88.59.204` removes the saved host key. Nothing changes on the VM.

---

## 2. Packages

### Step 2.1: Install git and sqlite3

- [x] **Where:** VM (via `ssh -i ~/.ssh/isba4775_azure azureuser@20.88.59.204`).
- **Run:**

  ```bash
  dpkg -s git sqlite3 2>/dev/null | grep -E '^(Package|Status)'   # record what was already there
  sudo apt-get update
  sudo apt-get install -y git sqlite3
  ```

- **Why:** git clones the code. The sqlite3 CLI checks the copied database. Ubuntu cloud images often include git already, so the first line records which packages this step actually adds.
- **Check:** `git --version && sqlite3 --version` both print versions.
- **Undo:** `sudo apt-get remove -y <only the packages the first line showed as not installed>`.

---

## 3. Code

### Step 3.1: Clone the repository

- [x] **Where:** VM.
- **Run:**

  ```bash
  git clone https://github.com/kwinsor1lmu/career-platform.git ~/career-platform
  cd ~/career-platform && git log -1 --oneline
  ```

- **Why:** Puts the exact code from GitHub on the VM. The repo is public, so no credentials are needed.
- **Check:** `git log -1 --oneline` matches the laptop's `git log origin/main -1 --oneline`, and `ls` shows `app/ alembic/ scripts/ pyproject.toml`.
- **Undo:** `rm -rf ~/career-platform`.

---

## 4. Python

### Step 4.1: Create and commit the lock file

- [x] **Where:** Laptop (Git Bash, repo root `C:\Users\kenne\Desktop\ISBA\career-platform`).
- **Run:**

  ```bash
  uv lock
  git add uv.lock
  git commit -m "build: add uv lock file for VM deployment"
  git push origin main
  ```

- **Why:** The repo has no `uv.lock`, so "uv sync from the lock file" has nothing to read. Locking on the laptop pins the exact dependency versions the VM will install. uv lock files work across platforms, so a lock made on Windows installs correctly on Linux.
- **Check:** `git ls-files uv.lock` prints `uv.lock`, and `git status -sb` shows `main...origin/main` with nothing ahead.
- **Undo:** `git revert <that commit>` then `git push origin main`.

### Step 4.2: Pull the lock file on the VM

- [x] **Where:** VM.
- **Run:** `cd ~/career-platform && git pull --ff-only`
- **Why:** The clone in Step 3.1 predates the lock commit.
- **Check:** `test -f uv.lock && git log -1 --oneline` shows the lock commit.
- **Undo:** `git reset --hard <commit from Step 3.1>`.

### Step 4.3: Install uv

- [x] **Where:** VM.
- **Run:**

  ```bash
  curl -LsSf https://astral.sh/uv/0.10.11/install.sh | sh
  source ~/.local/bin/env
  ```

- **Why:** Installs uv 0.10.11, the laptop's version, so both machines read the lock file the same way. It installs to `~/.local/bin` without sudo.
- **Check:** `uv --version` prints `uv 0.10.11`.
- **Undo:** `rm -f ~/.local/bin/uv ~/.local/bin/uvx` and remove the line the installer added to `~/.bashrc`/`~/.profile`.

### Step 4.4: Install dependencies from the lock

- [x] **Where:** VM.
- **Run:** `cd ~/career-platform && uv sync --locked`
- **Why:** `--locked` makes uv fail instead of silently re-resolving if `uv.lock` doesn't match `pyproject.toml`. That way the VM runs the versions that were locked. uv uses Ubuntu's Python 3.12, which meets `requires-python >=3.11`.
- **Check:**

  ```bash
  .venv/bin/python --version                                  # Python 3.12.x
  .venv/bin/python -c "import app.config, fastapi, sqlalchemy; print('ok')"
  .venv/bin/alembic --version
  ```

  Don't import `app.main` yet: it creates the app and needs `.env` from Step 5.1.
- **Undo:** `rm -rf ~/career-platform/.venv`.

---

## 5. Config

### Step 5.1: Create `.env` from the template

- [x] **Where:** VM.
- **Run:**

  ```bash
  cd ~/career-platform
  cp -n .env.example .env
  chmod 600 .env
  cat .env
  ```

- **Why:** `app/config.py` reads `.env`. The template's values already fit this VM: `ENVIRONMENT=development` (production rejects SQLite) and `DATABASE_URL=sqlite:///./data/app.db`. `cp -n` won't overwrite an existing `.env`. `chmod 600` limits it to `azureuser`, since any future secrets would go here.
- **Check:** `.venv/bin/python -c "from app.config import Settings; s=Settings(); print(s.environment, s.database_url)"` prints `development sqlite:///./data/app.db`.
- **Undo:** `rm ~/career-platform/.env`.

---

## 6. Data

### Step 6.1: Confirm the source file on the laptop

- [x] **Where:** Laptop (Git Bash).
- **Run:**

  ```bash
  sha256sum ~/Downloads/app.db
  sqlite3 ~/Downloads/app.db "select name from profiles;" 2>/dev/null || python -c "import sqlite3;print(sqlite3.connect('file:'+__import__('os').path.expanduser('~/Downloads/app.db')+'?mode=ro',uri=True).execute('select name from profiles').fetchall())"
  ```

- **Why:** Make sure this is the right database before copying it. It should show "Kenneth Winsor" (see Review Focus 1).
- **Check:** The hash matches Global Constraints and the profile name is the one you expect. **Stop here if either is wrong.**
- **Undo:** Nothing to undo; this is read-only.

### Step 6.2: Copy the database to the VM

- [x] **Where:** VM, then laptop.
- **Run:**

  ```bash
  # VM
  mkdir -p ~/career-platform/data
  test ! -e ~/career-platform/data/app.db && echo "target is free"
  ```

  ```bash
  # Laptop (Git Bash)
  scp -i ~/.ssh/isba4775_azure ~/Downloads/app.db azureuser@20.88.59.204:career-platform/data/app.db
  ```

- **Why:** Moves your data to where `DATABASE_URL` points. The `test` line confirms nothing gets overwritten. Copying when no app is running avoids copying a half-written file.
- **Check (VM):**

  ```bash
  cd ~/career-platform
  sha256sum data/app.db                                     # must equal b817b95c...eded4
  sqlite3 data/app.db "pragma integrity_check;"             # ok
  (set -a; . ./.env; set +a; .venv/bin/alembic current)     # 0001 (head); alembic/env.py reads DATABASE_URL from the environment, not .env
  ```

- **Undo:** `rm ~/career-platform/data/app.db` on the VM. The laptop copy is untouched.

### Step 6.3: Record row counts for later comparison

- [x] **Where:** VM.
- **Run:**

  ```bash
  cd ~/career-platform
  for t in profiles experiences educations skills certifications contact_links; do printf '%s ' $t; sqlite3 data/app.db "select count(*) from $t;"; done
  ```

- **Why:** Gives a baseline to compare in the Verify step.
- **Check:** Matches the laptop counts from 2026-09-29: `profiles 1, experiences 1, educations 1, skills 8, certifications 0, contact_links 1`.
- **Undo:** Nothing to undo; this is read-only.

---

## 7. Processes

### Step 7.1: Start uvicorn in the background

- [x] **Where:** VM.
- **Run:**

  ```bash
  cd ~/career-platform
  nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > ~/uvicorn.log 2>&1 &
  echo $! > ~/uvicorn.pid
  ```

- **Why:** Runs the app without `scripts/dev.sh`, which would re-ingest the placeholder content over your data. Running from the repo root makes the relative `DATABASE_URL` point at `data/app.db`. Binding to `127.0.0.1` keeps the site private even if a web port is opened in the NSG later. `nohup` keeps it running after you log out of SSH. Calling `.venv/bin/uvicorn` directly, not `uv run`, means the saved PID is uvicorn's own.
- **Check:**

  ```bash
  sleep 2; ps -p "$(cat ~/uvicorn.pid)" -o pid,cmd
  grep -E "Application startup complete|Uvicorn running on http://127.0.0.1:8000" ~/uvicorn.log
  ```

  If the log shows a traceback instead, fix the cause before continuing.
- **Undo:** `kill "$(cat ~/uvicorn.pid)" && rm ~/uvicorn.pid`.

---

## 8. Verify

### Step 8.1: The site answers on the VM

- [x] **Where:** VM.
- **Run:**

  ```bash
  curl --fail -s http://127.0.0.1:8000/health; echo
  curl --fail -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
  ```

- **Why:** Checks that the process is up and the home page renders.
- **Check:** `{"status":"ok"}` then `200`.
- **Undo:** Nothing to undo; this is read-only.

### Step 8.2: The page shows your data from the database

- [x] **Where:** VM.
- **Run:**

  ```bash
  cd ~/career-platform
  test ! -e data/fallback.json && echo "no fallback present"
  name=$(sqlite3 data/app.db "select name from profiles limit 1;")
  curl --fail -s http://127.0.0.1:8000/ | grep -c "$name"
  sha256sum data/app.db
  ```

- **Why:** With no fallback file on the VM, the only place the profile name can come from is the database. The hash check shows that serving pages didn't modify the data.
- **Check:** Prints `no fallback present`, a count of `1` or more, and the same hash as Step 6.2.
- **Undo:** Nothing to undo; this is read-only.

### Step 8.3: See it from the laptop browser

- [x] **Where:** Laptop (Git Bash); leave it running while you look.
- **Run:** `ssh -i ~/.ssh/isba4775_azure -N -L 8000:127.0.0.1:8000 azureuser@20.88.59.204` and then open `http://127.0.0.1:8000/` in a browser.
- **Why:** Lets you view the site with no public web port. The tunnel runs over the SSH connection that Step 1.1 already allows. Stop any local app on port 8000 first.
- **Check:** The page shows the profile name and the experience/education entries from Step 6.3.
- **Undo:** Press `Ctrl-C` in the tunnel terminal.

---

## Verify Results

**Run on 2026-09-29: all checks passed.** Sections 1–7 completed first; uvicorn was running as PID 47901 on `127.0.0.1:8000`.

| Step | Check | What it tests | Pass looks like | Result |
|---|---|---|---|---|
| 8.1 | `curl --fail -s http://127.0.0.1:8000/health` (VM) | The uvicorn process is up and answering HTTP | `{"status":"ok"}` | ✅ `{"status":"ok"}` |
| 8.1 | `curl --fail ... -w "%{http_code}" http://127.0.0.1:8000/` (VM) | The home page renders without a server error | `200` | ✅ `200` |
| 8.2 | `test ! -e data/fallback.json` (VM) | No fallback file exists, so the page can only come from the database | `no fallback present` | ✅ `no fallback present` |
| 8.2 | `curl ... / \| grep -c "$name"`, name read from `data/app.db` (VM) | The page shows the profile stored in the copied database | Count ≥ 1 for `Kenneth Winsor` | ✅ `Kenneth Winsor` found 3 times |
| 8.2 | `sha256sum data/app.db` (VM) | Serving pages did not modify the data | `b817b95c...eded4`, same as Step 6.2 | ✅ `b817b95c...eded4`, unchanged |
| 8.3 | SSH tunnel, then fetch `http://127.0.0.1:8000/` (laptop) | The site is reachable from the laptop without a public web port | Page shows Kenneth Winsor's profile, LMU Event Staff experience, LMU education, and 8 skills | ✅ `/health` ok and `/` returned through the tunnel; title and visible text show the profile, headline, summary and Event Staff role. Final browser look is left to the user |

**Extra checks run alongside Verify:**

| Check | What it tests | Result |
|---|---|---|
| Page contains `Event Staff`, `Business Administration (Undergraduate)`, `Event Planning`, `Spanish`, `github.com/kwinsor1` | Every resume section made it from the database to the page | ✅ All found |
| Page contains `Ada Example` or `Example Co` | No demo seed content survived | ✅ 0 matches |
| `ss -ltn` for `0.0.0.0:8000` | The app is not listening on a public interface | ✅ Only `127.0.0.1:8000` |
| Response `Content-Type` and the em dash in the job title | Text encoding is correct end to end | ✅ `text/html; charset=utf-8`, real U+2014 em dash, no replacement characters |

**Earlier blocker, resolved:** the laptop's public IP changed between sessions, so the NSG rule `Allow-SSH-Laptop` no longer matched it and SSH timed out; the rule's source was updated to the new `<LAPTOP_IP>/32` on 2026-09-29. If SSH times out again, check the laptop IP first.
