# Runbook — database backup & restore

**Written 2026-07-26, after an incident in which every user's `activities` and `reviews`
rows were destroyed and there was nothing to restore from.** Read `DECISIONS.md` D-039 for
the post-mortem. This runbook exists so that never happens twice.

Current posture: Supabase **free plan — no provider-side backups and no PITR.** The only
backup that exists is the one `.github/workflows/backup-db.yml` takes nightly. If that
workflow is red or its secrets are unset, **you have no backup.**

---

## 1. What is backed up

| | |
|---|---|
| **What** | `public` schema, full (DDL + data), custom-format `pg_dump` archive |
| **Plus** | `auth.users` data-only, **reference/reconciliation only** — not a drop-in restore |
| **Where** | GitHub Actions artifact `db-backup-<stamp>` on the private `Alok943/RetainHQ` repo |
| **Retention** | 90 days |
| **Encryption** | GPG symmetric, AES-256, passphrase = `BACKUP_PASSPHRASE` repo secret |
| **Schedule** | 19:00 UTC daily (00:30 IST) + manual via the Actions tab |
| **Size** | DB is ~15 MB, so dumps are small and fast |

### Known gaps — accept them knowingly or fix them

- **Up to 24h of data loss.** Nightly snapshots, no PITR. Supabase Pro (~$25/mo) adds
  daily provider backups and a PITR add-on; that is the real fix if the user base grows
  past "people I know".
- **Single point of failure.** The dumps live in the same GitHub account as the code. Lose
  the account, lose both. Copying artifacts offsite (R2/B2 free tier) is the obvious upgrade.
- **The passphrase must live outside GitHub.** If `BACKUP_PASSPHRASE` exists only as a repo
  secret and the account is lost, every artifact is unreadable. Put it in a password manager.
- **Storage/Auth are not covered.** Only Postgres. Supabase Auth is dumped for reference only.

---

## 2. One-time setup

1. **Supabase Dashboard → Project Settings → Database → Connection string → Session pooler.**
   Copy the URI. It must be port **5432**, host `…pooler.supabase.com`, user `postgres.<ref>`.

   > The app's `DATABASE_URL` is the **transaction** pooler (`:6543`) and will NOT work —
   > `pg_dump` needs session state. The direct `db.<ref>.supabase.co` host is IPv6-only and
   > unreachable from GitHub runners. The workflow hard-fails on both mistakes rather than
   > writing a broken dump.

2. **Repo → Settings → Secrets and variables → Actions → New repository secret:**
   - `BACKUP_DATABASE_URL` — the session-pooler URI from step 1
   - `BACKUP_PASSPHRASE` — a long random string, **also saved in a password manager**

3. **Actions tab → "Nightly DB backup" → Run workflow.** Confirm it goes green and produces
   an artifact. Do not wait for the first scheduled run to discover a typo.

4. **Do the restore drill in §4.** A backup nobody has restored is a guess, not a backup.

---

## 3. Reading a backup

```bash
gpg --batch --decrypt --output retainhq-public.dump retainhq-public-<stamp>.dump.gpg
pg_restore --list retainhq-public.dump | head -40
```

Row counts without restoring anything:

```bash
pg_restore --list retainhq-public.dump | grep "TABLE DATA"
```

---

## 4. Restore drill (do this on a scratch project, not production)

Create a throwaway Supabase project (or a local Postgres 17), then:

```bash
pg_restore --no-owner --no-privileges --clean --if-exists -d "$SCRATCH_URI" retainhq-public.dump
```

Then verify the tables that matter:

```bash
psql "$SCRATCH_URI" -c "SELECT (SELECT count(*) FROM activities) AS activities, (SELECT count(*) FROM reviews) AS reviews, (SELECT count(*) FROM user_progress) AS progress;"
```

Log the date of the last successful drill here:

| Drill date | Outcome |
|---|---|
| _never_ | **Restore path is UNTESTED.** |

---

## 5. Real recovery — "production lost data"

**Stop writing to production first.** Every minute the app runs, users create rows that a
restore will overwrite or collide with.

1. **Confirm what is actually gone**, and whether it was TRUNCATE or DELETE — they look
   identical in the app but different in the stats:

   ```sql
   SELECT relname, n_live_tup, n_tup_ins, n_tup_del
   FROM pg_stat_user_tables
   WHERE relname IN ('activities','reviews','user_progress');
   ```

   `n_live_tup = 0` with `n_tup_del` unchanged ⇒ **TRUNCATE**. `n_tup_del` jumping by roughly
   the lost row count ⇒ **DELETE**. This is how the 2026-07-26 incident was identified.

2. **Pick the newest artifact whose canary was green.** A red run may have backed up an
   already-damaged database.

3. **Prefer a table-scoped restore over a whole-database one** when only some tables were
   lost — it avoids clobbering rows written since the snapshot:

   ```bash
   pg_restore --no-owner --no-privileges --data-only \
     --table=activities --table=reviews \
     -d "$PROD_SESSION_URI" retainhq-public.dump
   ```

   Restore parents before children (`activities` before `reviews`), or FK checks will reject rows.

4. **Re-apply migrations** if the snapshot predates the current head:
   `cd backend && alembic upgrade head`

5. **Rebuild what does not need a backup at all** — see §6.

6. **Write down what happened** in `DECISIONS.md` before the details fade.

---

## 6. What is rebuildable without a backup

Not everything needs restoring. These are generated from files in the repo, so re-running
the seeder is faster and safer than a restore:

| Data | Rebuild with |
|---|---|
| `problems`, `problem_concepts` | `backend/scripts/import_leetcode_catalog.py` (from `content/leetcode-catalog/*.json`) |
| `roadmaps`, `roadmap_nodes` | the relevant `backend/seed_*.py` — **but read the warning below** |
| Lesson content | `content/roadmaps/**` → `sync-content.mjs`; never lived in the DB |

> **Seed scripts are not safe by default.** ~32 of them still use
> `DELETE FROM roadmap_nodes WHERE roadmap_id = … ` + re-INSERT with fresh UUIDs
> (`BACKLOG.md`, 2026-07-10). Re-running one against a roadmap with live `user_progress`
> cascade-wipes that progress. Only `seed_python_swe.py` uses the progress-safe upsert.
> Take a manual backup before running any seeder against production.

---

## 7. Manual backup before anything risky

Before a migration, a seeder run, or a bulk import against production — one command:

```bash
pg_dump "$SESSION_POOLER_URI" --schema=public --no-owner --no-privileges --format=custom --file="pre-change-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

Or just trigger the workflow manually from the Actions tab and wait for it to go green.

---

## 8. Prevention already in place

- **Migration `a9d4f7c2e618`** puts `BEFORE TRUNCATE` triggers on the ten user-data tables.
  `TRUNCATE … CASCADE` from a content table now aborts loudly instead of silently draining
  user history. To truncate one deliberately, drop its trigger in an explicit migration.
- **The nightly canary** fails the workflow if a critical table hits zero rows, turning
  silent data loss into an email within 24h instead of "the Home page looks wrong".
