# Task 3 report

## Scope
Implemented the task-3 persistence layer in the personal-resume-platform worktree: SQLAlchemy 2 typed models, a database session factory, Alembic environment and initial migration, and a focused schema test.

## Commit
- d63653a2df1d48dee04539fb6b045ca22168a1d7
- feat: add portable resume persistence schema
- Trailer: Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

## Commands and exact output

### Failed schema test before implementation
Command:
```bash
cd /workspaces/career-platform/.worktrees/personal-resume-platform && pytest tests/db/test_schema.py -q
```

Output:
```text
=================================== ERRORS ====================================
___________________ ERROR collecting tests/db/test_schema.py ___________________
ImportError while importing test module '/workspaces/career-platform/.worktrees/personal-resume-platform/tests/db/test_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/workusr/local/python/3.14.2/lib/python3.14/importlib/__init__.py:88: in <module>
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/db/test_schema.py:1: in <module>
    from sqlalchemy import create_engine, inspect
E   ModuleNotFoundError: No module named 'sqlalchemy'
=========================== short test summary info ==========================
ERROR tests/db/test_schema.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.16s
```

### Dependency install
Command:
```bash
cd /workspaces/career-platform/.worktrees/personal-resume-platform && python -m pip install -e '.[dev]'
```

Output summary:
```text
Successfully built personal-resume-platform
Successfully installed alembic-1.20.0 psycopg-3.3.5 psycopg-binary-3.3.5 sqlalchemy-2.0.54 greenlet-3.5.6 mako-1.4.1
```

### Final validation
Command:
```bash
cd /workspaces/career-platform/.worktrees/personal-resume-platform && mkdir -p data && pytest tests/db/test_schema.py -q && DATABASE_URL=sqlite:///./data/app.db alembic upgrade head
```

Output:
```text
.                                                                        [100%]
1 passed in 0.42s
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, Initial resume schema
```

### Missing DATABASE_URL guard
Command:
```bash
cd /workspaces/career-platform/.worktrees/personal-resume-platform && env -u DATABASE_URL alembic upgrade head
```

Output:
```text
Traceback (most recent call last):
  File "/home/codespace/.python/current/bin/alembic", line 6, in <module>
    sys.exit(main())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/alembic/config.py", line 1039, in main
    CommandLine(prog=prog).main(argv=argv)
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/alembic/config.py", line 1029, in run_cmd
    fn(
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/alembic/command.py", line 487, in upgrade
    script.run_env()
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/alembic/script/base.py", line 550, in run_env
    util.load_python_file(self.dir, "env.py")
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/alembic/util/pyfiles.py", line 114, in load_python_file
    module = load_module_py(module_id, path)
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/alembic/util/pyfiles.py", line 132, in load_module_py
    spec.loader.exec_module(module)  # type: ignore
  File "<frozen importlib._bootstrap_external>", line 759, in exec_module
  File "/workspaces/career-platform/.worktrees/personal-resume-platform/alembic/env.py", line 29, in <module>
    config.set_main_option("sqlalchemy.url", get_database_url())
                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/career-platform/.worktrees/personal-resume-platform/alembic/env.py", line 21, in get_database_url
    raise RuntimeError(
        "DATABASE_URL is not set. Example: DATABASE_URL=sqlite:///./data/app.db"
    )
RuntimeError: DATABASE_URL is not set. Example: DATABASE_URL=sqlite:///./data/app.db
```

## Concerns
- The migration and model purposely keep `stable_id`, `visibility`, `display_order`, `owner_id`, and `profile_id` explicit so the persistence contract remains portable across SQLite and PostgreSQL.
- SQLite uses a local `data/` file for validation; that runtime artifact is intentionally left out of the Git commit.
- UTC handling for timezone-aware timestamps should be enforced at the connection layer in deployment; the model uses SQLAlchemy `DateTime(timezone=True)` and Postgres/SQLite compatibility is good, but production deployments should still set a UTC timezone if the database is not already configured.
- Alembic refuses to proceed without a `DATABASE_URL`, which is intentional to avoid silent defaults and to keep the migration path actionable.

## Fix round: reviewer findings and remediation

### Root cause summary
1. `owner_id` was stored on each content table but only `profile_id` was a foreign key; this allowed mismatched ownership in the database.
2. `visibility` was a free-form string with no portable check constraint.
3. `display_order` was indexed twice in model metadata, which caused SQLite to fail during `Base.metadata.create_all()` with `OperationalError: index ... already exists`.

### Fixed schema boundary
- Every content table now enforces a composite foreign key: `(profile_id, owner_id) -> (profiles.id, profiles.owner_id)`.
- `visibility` now uses a portable SQL check constraint: `IN ('draft', 'private', 'published')` across profiles and content tables.
- `display_order` remains indexed via `index=True` in the model, while the migration creates the matching standalone index names to keep Alembic metadata consistent.

### Verification commands and output
Command:
```bash
cd /workspaces/career-platform/.worktrees/personal-resume-platform && rm -rf data && mkdir -p data && pytest tests/db/test_schema.py -q && DATABASE_URL=sqlite:///./data/app.db alembic upgrade head && DATABASE_URL=sqlite:///./data/app.db alembic check
```

Output:
```text
.                                                                        [100%]
1 passed in 0.39s
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, Initial resume schema
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.schemas
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.tables
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.types
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.constraints
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.defaults
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.comments
No new upgrade operations detected.
```
