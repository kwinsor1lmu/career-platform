# AWS migration: architecture decision

Decided 2026-11-03 (session 18).

I chose **EC2 + Single-AZ RDS PostgreSQL** over **EC2 + local PostgreSQL** because **I want the least operating work I can get without changing application code**, and I accept **about $13/month more (~$26 vs ~$13, covered by the $100 credit) and a database that goes down if its one availability zone has an outage**.

Lambda + API Gateway + RDS was rejected: it would need a Mangum adapter, moving `alembic upgrade` and content ingest out of startup, and replacing the on-disk fallback file, and it isn't covered by the course deployment policy.

## Checks

| Requirement | How this option meets it |
| --- | --- |
| App runs with changes I understand | No code changes; only `DATABASE_URL` points at RDS |
| Data moves intact | `pg_dump` from Railway, `pg_restore` from the EC2 instance into RDS |
| PostgreSQL stays private | RDS not publicly accessible; port 5432 only from the EC2 security group |
| Every service on my plan | EC2 t3.micro, RDS db.t3/t4g.micro Single-AZ 20 GB, gp3, public IPv4: all Free-plan eligible and paid from credits |

Watch-out: `scripts/dev.sh` runs `ingest_content.py` on every start, which syncs the database to `content/resume.json` and deletes rows not in it.

## Planned request path

```mermaid
flowchart LR
  B["Browser"] -. "DNS lookup" .-> CF["Cloudflare DNS<br/>aws.kenwinsor.xyz → Elastic IP<br/>(DNS only, grey cloud)"]
  B == "HTTPS 443" ==> SG1

  subgraph AWS["AWS us-east-1 · default VPC"]
    subgraph EC2["EC2 t3.micro · Ubuntu 26.04 · Elastic IP"]
      SG1["EC2 security group<br/>80, 443 from anywhere<br/>22 from my IP only"]
      NG["Nginx<br/>TLS ENDS HERE (Let's Encrypt)<br/>80 → 443 redirect"]
      UV["uvicorn 127.0.0.1:8000<br/>systemd"]
      FB[("data/fallback.json")]
    end
    subgraph RDSBOX["RDS PostgreSQL 18 · Single-AZ · not public"]
      SG2["RDS security group<br/>5432 from EC2 SG only"]
      DB[("career-platform-db<br/>20 GB gp3 encrypted")]
      SNAP[("Automated backups<br/>7 days")]
    end
  end

  OFF[("Independent pg_dump<br/>outside AWS")]
  ME["My laptop"] -- "SSH 22" --> SG1

  SG1 --> NG --> UV
  UV -- "Postgres 5432" --> SG2 --> DB
  UV --> FB
  DB -.-> SNAP
  DB -. "manual export" .-> OFF

  RW["Railway (still serves kenwinsor.xyz until cutover)"]
```
