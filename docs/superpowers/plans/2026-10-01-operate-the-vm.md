# Operate the VM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the resume site work like a real website: visitors open `http://20.88.59.204` with no port number, it starts at boot, it comes back after a crash, port 8000 stays private, and nothing in the app runs as root.

**Architecture:** systemd, Ubuntu's built-in process manager, runs the app as a service named `career-platform` under `azureuser`. uvicorn runs **two worker processes**, so if one crashes the other keeps serving while the dead one is replaced. nginx listens on public port 80 and passes each request to the app on `127.0.0.1:8000`, which can only be reached from inside the VM.

**Tech Stack:** Ubuntu 24.04, systemd, nginx (from apt), uvicorn ≥ 0.30 (already in `~/career-platform/.venv`), FastAPI, SQLite.

**Spec:** The user's request in the 2026-09-30 `operate-the-vm` session. There's no separate spec file. It follows on from `docs/superpowers/plans/2026-09-24-azure-vm-migration.md`.

## The VM (checked read-only with `az` on 2026-09-30)

| | |
|---|---|
| VM | `vm-career-platform` (the subscription's only VM), running |
| Resource group / region | `rg-career-platform`, North Central US |
| Size / OS | `Standard_B2ats_v2` (2 vCPU, 1 GiB), Ubuntu 24.04 LTS |
| Public IP | `20.88.59.204` (no DNS name) |
| SSH | `ssh -i ~/.ssh/isba4775_azure azureuser@20.88.59.204` (key only; password login is off) |
| NSG `vm-career-platformNSG` | `Allow-SSH-Laptop` 22 from `<LAPTOP_IP>/32` (prio 300); **`Allow-HTTP-80` 80 from `*` (prio 310), already present** |
| App | `~/career-platform`: code, `.venv`, `.env`, `data/app.db` |

## Global Constraints

- Service name: `career-platform`. It runs as user `azureuser`, never root.
- Use the existing `~/career-platform` code, `.venv`, `.env`, and `data/app.db`. **Don't change any file in the repo** and don't add tests.
- The app listens on `127.0.0.1:8000` only. No NSG rule may open port 8000.
- You add the port-80 rule yourself in the Azure portal as `Allow-HTTP-80` at priority 320. Claude doesn't change Azure.
- Don't start the app with `scripts/dev.sh`, because it re-ingests `content/resume.json` over your data and binds to `0.0.0.0`.
- Leave out crash and reboot tests; you'll run those yourself.
- Every `ssh` uses `-i ~/.ssh/isba4775_azure azureuser@20.88.59.204`.

## Review Focus

1. **`Allow-HTTP-80` already exists (priority 310, source `*`).** If you create it again in the portal, it will either fail or overwrite the existing rule. Decide in Step 3.1 whether to keep it or move it to 320.
2. **The hand-started uvicorn may still be holding port 8000.** If it is, the new service fails with "address already in use". Step 0.2 stops it first.
3. **nginx's default "Welcome to nginx" page.** If the default site stays enabled, port 80 returns 200 but shows the wrong page. The checks look for your name, not just a 200.
4. **Workers replacing themselves needs uvicorn ≥ 0.30.** Older versions don't restart a worker that dies. Step 0.1 checks the version.
5. **The laptop's IP changes.** If SSH hangs, compare `curl -4 https://api.ipify.org` with the `Allow-SSH-Laptop` source before you suspect anything else.

## How the pieces fit

```
Visitor ──http :80──▶ [NSG allows 80] ──▶ nginx (port 80, public)
                                            │ proxy_pass
                                            ▼
                         uvicorn supervisor on 127.0.0.1:8000  (user azureuser)
                           ├─ worker 1 ┐  if a worker dies, the supervisor starts a new one
                           └─ worker 2 ┘  if the supervisor dies, systemd restarts it
```

Port 8000 is never reachable from the Internet, for two reasons. The app binds to `127.0.0.1` (only the VM itself can connect), and the NSG has no rule for port 8000.

**Total time:** about 20 minutes. **Where things run:** **Laptop** means Git Bash on your PC, **VM** means inside the SSH session, and **Portal** means the Azure website.

---

## 0. Before you start

### Step 0.1: Log in and look around

- [ ] **Where:** Laptop, then VM.
- **Run:**

  ```bash
  ssh -i ~/.ssh/isba4775_azure azureuser@20.88.59.204
  # now on the VM:
  cd ~/career-platform
  .venv/bin/uvicorn --version            # need 0.30 or newer
  ls .env data/app.db                    # both must exist
  sha256sum data/app.db                  # write this down; we compare it at the end
  ss -ltnp | grep -E ':(80|8000)\b'      # what is listening now
  dpkg -s nginx 2>/dev/null | grep Status || echo "nginx not installed"
  ```

- **Why:** This confirms the files the service relies on are there, and records the starting state so you can tell what you changed.
- **Check:** uvicorn is 0.30 or newer, both files are listed, and you've noted the hash. You'll probably see something on `127.0.0.1:8000` (the hand-started app) and nothing on `:80`.
- **Undo:** Nothing to undo; these commands only read.

### Step 0.2: Stop the hand-started app

- [ ] **Where:** VM.
- **Run:**

  ```bash
  test -f ~/uvicorn.pid && kill "$(cat ~/uvicorn.pid)"; rm -f ~/uvicorn.pid
  sleep 1; ss -ltn | grep ':8000\b' || echo "port 8000 is free"
  ```

- **Why:** Two programs can't listen on the same port. The old `nohup` process has to go so the service can take over port 8000. The site is down from here until Step 1.2, which takes about a minute.
- **Check:** Prints `port 8000 is free`. If something is still listening, `pgrep -af uvicorn` shows the PID; `kill` it.
- **Undo:** Restart it by hand the old way (migration plan, Step 7.1).

### Section 0 results (run 2026-09-30, from the laptop over SSH)

Steps 0.1 and 0.2 are both done, and every check passed. **The site is offline from here until Step 1.2 starts the service.**

| Step | What ran (VM) | Expected | Result |
|---|---|---|---|
| 0.1 | `.venv/bin/uvicorn --version` | 0.30 or newer | ✅ `uvicorn 0.54.0`, CPython 3.12.3 |
| 0.1 | `ls -l .env data/app.db` | Both exist | ✅ `.env` (`-rw-------`, azureuser) and `data/app.db` (212,992 bytes) |
| 0.1 | `sha256sum data/app.db` | Write down for Step 4.2 | ✅ `b817b95cc91783f23116a9b12f7d3fcbcd2f958e10fea525fd505407799eded4`, the same as the migration plan's hash |
| 0.1 | `ss -ltnp \| grep -E ':(80\|8000)\b'` | The hand-started app on 8000, nothing on 80 | ✅ Only `127.0.0.1:8000`, held by `uvicorn` PID 48675; nothing on `:80` |
| 0.1 | `dpkg -s nginx` | Record whether nginx is already installed | ✅ `nginx not installed`, so Step 2.1's undo (purge) applies |
| 0.2 | `kill "$(cat ~/uvicorn.pid)"; rm -f ~/uvicorn.pid` | Old process stopped | ✅ `~/uvicorn.pid` held 48675 and it was killed; the pid file is gone |
| 0.2 | `ss -ltn \| grep ':8000\b'` | `port 8000 is free` | ✅ `port 8000 is free` |
| 0.2 | `ps -C uvicorn,python3,python -o pid=,args= \| grep app.main` | No app left running | ✅ `no app process running` |

**Note:** The plan's fallback check, `pgrep -af uvicorn`, matches its own `ssh` command line because that line contains the word "uvicorn". That makes it look as if something is still running. Use the `ps -C ... | grep app.main` check above instead.

---

## 1. The app as a service (systemd)

**For beginners:** systemd starts and supervises programs on Linux. You describe a program in a small "unit file": who runs it, from which folder, and with which command. systemd then starts it at boot and restarts it if it exits. The unit file goes in `/etc/systemd/system/`, outside the repo.

### Step 1.1: Write the unit file

- [ ] **Where:** VM.
- **Run:**

  ```bash
  sudo tee /etc/systemd/system/career-platform.service > /dev/null <<'EOF'
  [Unit]
  Description=career-platform resume site (uvicorn)
  After=network.target
  # Never stop retrying after repeated crashes
  StartLimitIntervalSec=0

  [Service]
  User=azureuser
  Group=azureuser
  WorkingDirectory=/home/azureuser/career-platform
  ExecStart=/home/azureuser/career-platform/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
  Restart=always
  RestartSec=2

  [Install]
  WantedBy=multi-user.target
  EOF
  sudo systemd-analyze verify /etc/systemd/system/career-platform.service
  ```

- **Why, line by line:**
  - `User=`/`Group=` run the app as `azureuser`, not root.
  - `WorkingDirectory=` matters because `.env` and `DATABASE_URL=sqlite:///./data/app.db` are both found relative to this folder.
  - `--host 127.0.0.1` keeps port 8000 private. `--workers 2` gives one worker per vCPU, so one crash leaves the other worker serving.
  - `Restart=always` with `RestartSec=2` means that if the whole process dies, it comes back after 2 seconds.
  - `StartLimitIntervalSec=0` stops systemd from giving up after 5 quick crashes.
  - `WantedBy=multi-user.target` is what "start at boot" hooks into.
- **Check:** `systemd-analyze verify` prints nothing, which means no errors.
- **Undo:** `sudo rm /etc/systemd/system/career-platform.service && sudo systemctl daemon-reload`.

### Step 1.2: Enable and start it

- [ ] **Where:** VM.
- **Run:**

  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now career-platform
  ```

- **Why:** `daemon-reload` makes systemd read the new file. `enable` sets it to start at boot, and `--now` also starts it right away.
- **Check:**

  ```bash
  systemctl is-enabled career-platform          # enabled
  systemctl is-active career-platform           # active
  journalctl -u career-platform -n 20 --no-pager   # "Application startup complete" (twice, once per worker)
  curl --fail -s http://127.0.0.1:8000/health; echo   # {"status":"ok"}
  pid=$(systemctl show -p MainPID --value career-platform)
  ps -o user=,pid=,ppid=,args= --pid "$pid" --ppid "$pid"
  ```

  The `ps` output shows the supervisor plus at least two worker processes, and every one has user `azureuser`. If the service isn't `active`, the `journalctl` output says why.
- **Undo:** `sudo systemctl disable --now career-platform`.

### Section 1 results (run 2026-09-30 laptop time; the VM's journal shows Oct 01 22:22 UTC)

Steps 1.1 and 1.2 are both done, and every check passed. The site is back up on the VM at `127.0.0.1:8000`, now running as the `career-platform` service. It can't be reached from outside the VM yet; Section 2 adds nginx on port 80.

| Step | What ran (VM) | Expected | Result |
|---|---|---|---|
| 1.1 | `test ! -e .../career-platform.service` | No existing unit to overwrite | ✅ `no existing unit (ok)` |
| 1.1 | `sudo tee /etc/systemd/system/career-platform.service` (unit exactly as above), then `cat` | The file matches the plan | ✅ Contents identical to Step 1.1 |
| 1.1 | `sudo systemd-analyze verify ...` | No output | ✅ No warnings, exit 0 |
| 1.2 | `sudo systemctl daemon-reload && sudo systemctl enable --now career-platform` | Enabled and started | ✅ Created symlink in `multi-user.target.wants`, so it starts at boot |
| 1.2 | `systemctl is-enabled` / `is-active` | `enabled` / `active` | ✅ `enabled` / `active` |
| 1.2 | `journalctl -u career-platform -n 20` | "Application startup complete", twice | ✅ Parent process 52692; workers 52695 and 52696 each logged `Application startup complete.` |
| 1.2 | `curl --fail -s http://127.0.0.1:8000/health` | `{"status":"ok"}` | ✅ `{"status":"ok"}` |
| 1.2 | `curl ... -w "%{http_code}" http://127.0.0.1:8000/` | `200` | ✅ `200` |
| 1.2 | `ps -o user:20= --pid $MainPID --ppid $MainPID \| sort \| uniq -c` | The supervisor and at least 2 workers, all `azureuser` | ✅ `4 azureuser`: supervisor 52692, workers 52695 and 52696, plus Python's `multiprocessing.resource_tracker` helper (52694) |
| 1.2 | `systemctl show career-platform -p User -p Restart -p WorkingDirectory` | `azureuser`, `always`, the repo root | ✅ `User=azureuser`, `Restart=always`, `WorkingDirectory=/home/azureuser/career-platform` |
| extra | `ss -ltnp \| grep -E ':(80\|8000)\b'` | 8000 on localhost only | ✅ Only `127.0.0.1:8000`, shared by the supervisor and both workers; nothing on `:80` |
| extra | Page contains the name from `data/app.db`, and no `data/fallback.json` exists | The page comes from the database | ✅ `Kenneth Winsor` found 3 times; `no fallback present` |
| extra | `sha256sum data/app.db` | Same as Step 0.1 | ✅ `b817b95c...eded4`, unchanged |

**Note:** Plain `ps -o user=` cuts the name off at 8 characters (`azureus+`). Use `ps -o user:20=` to see the full `azureuser`.

---

## 2. The public front door (nginx)

**For beginners:** Only root can listen on ports below 1024, such as 80. Running your app as root would break the non-root rule. Instead, nginx (a small, well-tested web server) opens port 80 and forwards each request to the app on `127.0.0.1:8000`. nginx's own request handlers run as the low-privilege `www-data` user.

### Step 2.1: Install nginx

- [ ] **Where:** VM.
- **Run:** `sudo apt-get update && sudo apt-get install -y nginx`
- **Why:** Installs nginx and enables it at boot (Ubuntu does that by default).
- **Check:** `systemctl is-enabled nginx` prints `enabled`, and `curl -s http://127.0.0.1/ | grep -o '<title>.*</title>'` shows `Welcome to nginx!` for now.
- **Undo:** `sudo apt-get purge -y nginx nginx-common && sudo apt-get autoremove -y` (only if Step 0.1 showed it wasn't installed before).

### Step 2.2: Point nginx at the app

- [ ] **Where:** VM.
- **Run:**

  ```bash
  sudo tee /etc/nginx/sites-available/career-platform > /dev/null <<'EOF'
  server {
      listen 80 default_server;
      listen [::]:80 default_server;
      server_name _;

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  EOF
  sudo ln -sf /etc/nginx/sites-available/career-platform /etc/nginx/sites-enabled/career-platform
  sudo rm -f /etc/nginx/sites-enabled/default
  sudo nginx -t && sudo systemctl reload nginx
  ```

- **Why:** `default_server` with `server_name _` means "answer every request on port 80, whatever address was typed". `proxy_pass` forwards the request to the app, and the `proxy_set_header` lines pass along the visitor's real address. Removing the `default` link turns off the welcome page. The original file stays in `sites-available` in case you want it back.
- **Check:** `nginx -t` prints `syntax is ok` and `test is successful`. Then run:

  ```bash
  curl --fail -s http://127.0.0.1/health; echo                  # {"status":"ok"}, via nginx this time
  name=$(sqlite3 ~/career-platform/data/app.db "select name from profiles limit 1;")
  curl --fail -s http://127.0.0.1/ | grep -c "$name"            # 1 or more
  ```

- **Undo:** `sudo rm /etc/nginx/sites-enabled/career-platform /etc/nginx/sites-available/career-platform && sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default && sudo systemctl reload nginx`.

### Step 2.3: Make nginx come back if it crashes

- [ ] **Where:** VM.
- **Run:**

  ```bash
  sudo mkdir -p /etc/systemd/system/nginx.service.d
  printf '[Service]\nRestart=on-failure\nRestartSec=2\n' | sudo tee /etc/systemd/system/nginx.service.d/restart.conf
  sudo systemctl daemon-reload
  ```

- **Why:** nginx is now the only way into the site, so it needs the same safety net as the app. Ubuntu's nginx unit doesn't restart on a crash by default. This "drop-in" file adds that setting without editing the packaged unit.
- **Check:** `systemctl show nginx -p Restart` prints `Restart=on-failure`.
- **Undo:** `sudo rm -r /etc/systemd/system/nginx.service.d && sudo systemctl daemon-reload`.

### Section 2 results (run 2026-09-30 laptop time; VM clock Oct 01 ~22:24 UTC)

Steps 2.1, 2.2 and 2.3 are all done, and every check passed. nginx now serves your resume on port 80 inside the VM. Port 8000 is still on `127.0.0.1` only. Because `Allow-HTTP-80` already exists in the NSG, the site is probably reachable from the Internet already; Section 4 confirms that from the laptop.

| Step | What ran (VM) | Expected | Result |
|---|---|---|---|
| 2.1 | `sudo apt-get update && sudo apt-get install -y nginx` | Installs cleanly | ✅ nginx `1.24.0-2ubuntu7.18` installed with no errors (full log in the git-ignored folder `.superpowers/sdd/.../step-2.1.log`) |
| 2.1 | `systemctl is-enabled nginx` / `is-active` | `enabled` / `active` | ✅ `enabled` / `active` |
| 2.1 | `curl -s http://127.0.0.1/ \| grep -o '<title>.*</title>'` | `Welcome to nginx!` for now | ✅ `<title>Welcome to nginx!</title>` |
| 2.1 | `ss -ltnp` | Port 80 opened by nginx | ✅ `0.0.0.0:80` and `[::]:80`; port 8000 still only `127.0.0.1:8000` |
| 2.2 | `test ! -e /etc/nginx/sites-available/career-platform` | Nothing to overwrite | ✅ `no existing site file (ok)`; `sites-enabled` held only `default` |
| 2.2 | `sudo tee` site file, `ln -sf` into `sites-enabled`, `rm -f sites-enabled/default` | Only the career-platform site is enabled | ✅ `sites-enabled` now holds only `career-platform`; `default` is kept in `sites-available` |
| 2.2 | `sudo nginx -t && sudo systemctl reload nginx` | `syntax is ok` / `test is successful` | ✅ Both lines printed; reload succeeded |
| 2.2 | `curl --fail -s http://127.0.0.1/health` | `{"status":"ok"}`, via nginx | ✅ `{"status":"ok"}` |
| 2.2 | `curl ... http://127.0.0.1/ \| grep -c "$name"` | 1 or more | ✅ `3`; status `200` |
| 2.2 | Page `<title>` | Your resume, not the nginx welcome page | ✅ `Kenneth Winsor \| Business Administration Student at Loyola Marymount University \| ...` |
| extra | `curl ... http://127.0.0.1/static/styles.css` | The stylesheet loads through the proxy | ✅ `200` |
| 2.3 | `printf ... \| sudo tee /etc/systemd/system/nginx.service.d/restart.conf`; `daemon-reload` | Drop-in in place | ✅ Written (no existing drop-in directory before) |
| 2.3 | `systemctl show nginx -p Restart` | `Restart=on-failure` | ✅ `Restart=on-failure`, `RestartUSec=2s`, `DropInPaths=/etc/systemd/system/nginx.service.d/restart.conf` |
| extra | `ps -C nginx -o user:20=,pid=,args=` | Only the master runs as root | ✅ master 53336 is `root`; workers 53477 and 53478 are `www-data` |
| extra | `systemctl is-active nginx career-platform`, then `curl` `/` | Both still up after the reload | ✅ `active` / `active`; `/` → `200` |

---

## 3. The firewall (you, in the Azure portal)

### Step 3.1: Port 80 open, port 8000 not

- [ ] **Where:** Portal → `vm-career-platform` → Networking → Network settings → `vm-career-platformNSG`.
- **Do:** A rule named `Allow-HTTP-80` (port 80, source Any, priority **310**) **already exists**, so creating it again with the same name will fail or replace the existing rule. Choose one:
  - **Keep the existing rule.** It already does the job, and nothing changes.
  - **Move it to 320 as you planned.** Edit the existing rule and change its priority to 320. Port 80 stays open the whole time.
- **Why:** The NSG is Azure's firewall in front of the VM. Port 80 must be allowed for visitors to get in. Port 8000 needs no rule at all, because the NSG blocks anything not explicitly allowed.
- **Check (Laptop, PowerShell, read-only):**

  ```powershell
  $az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
  & $az network nsg rule list -g rg-career-platform --nsg-name vm-career-platformNSG --query "[].{name:name, port:destinationPortRange, src:sourceAddressPrefix, prio:priority}" -o table
  ```

  Shows `Allow-HTTP-80` on port 80 and `Allow-SSH-Laptop` on port 22, with **no** row for 8000.
- **Undo:** Put the rule back the way it was in the portal.

---

## 4. Verify from outside

### Step 4.1: Visitors get the site; port 8000 is closed

- [ ] **Where:** Laptop (Git Bash).
- **Run:**

  ```bash
  curl --fail -s -o /dev/null -w "%{http_code}\n" http://20.88.59.204/          # 200
  curl --fail -s http://20.88.59.204/ | grep -o '<title>.*</title>'            # your name, not "Welcome to nginx"
  curl -s --max-time 5 http://20.88.59.204:8000/ || echo "8000 closed (good)"
  ```

  Then open `http://20.88.59.204` in a browser.
- **Why:** This tests the site the way a visitor reaches it, from outside Azure, with no port number in the address.
- **Check:** You get `200`, the title shows your resume, `8000 closed (good)` is printed, and the browser shows your page.
- **Undo:** Nothing to undo; these commands only read.

### Step 4.2: Nothing runs as root; 8000 is local only; data unchanged

- [ ] **Where:** VM.
- **Run:**

  ```bash
  ss -ltnp | grep -E ':(80|8000)\b'
  pid=$(systemctl show -p MainPID --value career-platform)
  ps -o user= --pid "$pid" --ppid "$pid" | sort -u
  sha256sum ~/career-platform/data/app.db
  ```

- **Check:**
  - Port 8000 is listed only on `127.0.0.1:8000`, and port 80 on `0.0.0.0:80` (and `[::]:80`).
  - The user list prints only `azureuser`.
  - The hash matches the one from Step 0.1.
  - nginx's master process is root (it has to be, to open port 80), but it's nginx, not your app.
- **Undo:** Nothing to undo; these commands only read.

**Left for you:** the crash test (`sudo kill -9` a worker, then the supervisor) and the reboot test (`sudo reboot`, then Step 4.1 again).

### Reboot, crash, and outside-check results (run 2026-10-26 PDT = 2026-10-27 UTC, from the laptop over SSH)

Run by Claude Code at my request, after the domain had moved to Railway. The VM serves the same app as the rollback, so these tests didn't affect the live site. Times are from the VM's clock (UTC), which matched a web server's `Date` header; my laptop clock was about 7 minutes slow that day. The VM had been up since its first boot on 2026-09-24.

| Test | What ran | Expected | Result |
|---|---|---|---|
| Before | `curl --resolve kenwinsor.xyz:443:20.88.59.204 https://kenwinsor.xyz/` | `200` | ✅ `200` |
| Before | `systemctl is-enabled career-platform nginx` | `enabled` ×2 | ✅ `enabled`, `enabled` |
| Reboot | `sudo systemctl reboot` | VM restarts | ✅ Previous boot's journal ends `05:41:36 systemd-shutdown … Sending SIGTERM to remaining processes`; `who -b` → `system boot 2026-10-27 05:41` |
| After reboot | `journalctl -b -u nginx`, `journalctl -b -u career-platform` | Both start on their own | ✅ `05:41:49 Started career-platform.service`, `05:41:50 Started nginx.service`, workers 839 and 840 `Started server process` at 05:41:54. No manual steps |
| After reboot | `systemctl is-active career-platform nginx` | `active` ×2 | ✅ `active`, `active` |
| After reboot | `ss -ltn` | 80/443 public, 8000 on localhost only | ✅ `0.0.0.0:80`, `0.0.0.0:443`, `127.0.0.1:8000` |
| After reboot | `curl http://127.0.0.1:8000/health` on the VM; `https://kenwinsor.xyz/` and `/health` via `--resolve` to the VM | `{"status":"ok"}`, `200`, name from the database | ✅ `{"status":"ok"}`, `200`, `Kenneth Winsor` ×5 |
| Worker crash | `sudo kill -9 840` (one worker) at 05:42:44 | The supervisor replaces it; the site keeps answering | ✅ Journal: `Child process [840] died`, then `Started server process [1323]` at 05:42:45. Workers went from `837 839 840` to `837 839 1323`. Page `200` |
| Supervisor crash | `sudo kill -9 677` (uvicorn's main process) at 05:42:47 | systemd restarts the service | ✅ `Main process exited, code=killed, status=9/KILL`, then `Scheduled restart job, restart counter is at 1` and `Started career-platform.service` at 05:42:49. New MainPID 1339, `NRestarts=1`, page `200` |
| Process users | `ps -o user,args -C nginx,uvicorn,python3` | App not root | ✅ App (PID 1339) runs as `azureuser`; nginx workers as `www-data`. Root: nginx master and the Azure agent (`waagent`) only |
| Outside: port 80 | `curl -H "Host: kenwinsor.xyz" http://20.88.59.204/` | Redirect to HTTPS | ✅ `301` → `https://kenwinsor.xyz/` |
| Outside: port 8000 | `curl -m 8 http://20.88.59.204:8000/` | Blocked by the NSG | ✅ No response (`000`, timed out) |
| Outside: SSH | From the home IP `68.228.92.204` (allowed) | Connects | ✅ Connected. Testing a non-allowed IP wasn't possible from here; the NSG rule allows only the school and home /32s |

---

## Day-to-day commands (VM)

| To... | Run |
|---|---|
| See status | `systemctl status career-platform` |
| Read logs | `journalctl -u career-platform -f` |
| Restart after `git pull` | `sudo systemctl restart career-platform` |
| nginx logs | `sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log` |

## Rollback (everything)

1. VM: `sudo systemctl disable --now career-platform && sudo rm /etc/systemd/system/career-platform.service`
2. VM: `sudo rm -r /etc/systemd/system/nginx.service.d && sudo systemctl daemon-reload`
3. VM: the undo from Step 2.2, then the undo from Step 2.1 if nginx was new.
4. Portal: put `Allow-HTTP-80` back the way it was before Step 3.1.

The repo, `.venv`, `.env`, and `data/app.db` are never modified.
