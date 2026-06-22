// Client-side SQL execution, powered by PGlite (real Postgres -> WASM).
// Loaded LAZILY from CDN on first use — never bundled, exactly like the Pyodide
// runner — so it costs nothing until a learner actually runs a query. We use
// PGlite (not sql.js) so lessons get true Postgres semantics (ILIKE, RETURNING,
// window functions, NULL three-valued logic) matching the Supabase/Postgres stack.
//
// The whole SQL roadmap shares ONE seeded dataset (content/roadmaps/sql/_dataset.sql).
// Every query runs against it. To keep that dataset pristine across lessons —
// including INSERT/UPDATE/DELETE lessons — each run is wrapped in BEGIN/ROLLBACK,
// so a mutation's RETURNING/rowcount is observable but the data resets afterwards.

// Pin the 0.2.x line; PGlite resolves its own .wasm/.data from the same CDN path.
const PGLITE_CDN = 'https://cdn.jsdelivr.net/npm/@electric-sql/pglite@0.2/dist/index.js';
const DATASET_URL = '/content/roadmaps/sql/_dataset.sql';

let _sharedDbPromise = null;
// Serialize access to the shared connection — PGlite is single-connection, and we
// must not interleave two BEGIN/ROLLBACK envelopes on it.
let _queue = Promise.resolve();

async function importPGlite() {
  const mod = await import(/* @vite-ignore */ PGLITE_CDN);
  return mod.PGlite;
}

// Singleton: boot PGlite + seed the canonical dataset exactly once.
function getSharedDb() {
  if (!_sharedDbPromise) {
    _sharedDbPromise = (async () => {
      const PGlite = await importPGlite();
      const db = new PGlite();
      const res = await fetch(DATASET_URL);
      if (!res.ok) throw new Error('Could not load the SQL dataset.');
      await db.exec(await res.text());
      return db;
    })().catch((e) => {
      _sharedDbPromise = null; // allow retry on failure
      throw e;
    });
  }
  return _sharedDbPromise;
}

function shape(result) {
  // PGlite returns { rows: [{col: val}], fields: [{name}], affectedRows }.
  const columns = (result.fields || []).map((f) => f.name);
  const rows = result.rows || [];
  return { columns, rows, affectedRows: result.affectedRows ?? null };
}

/**
 * Run a single SQL statement and return its result set.
 * @param {string} sql   The query (a single statement).
 * @param {string=} setupSql  Optional topic-specific extra DDL/seed, additive to the
 *                             canonical dataset and run in a throwaway database.
 * @returns {Promise<{columns:string[], rows:object[], affectedRows:?number, error:?string}>}
 */
export async function runSql(sql, setupSql) {
  try {
    if (setupSql) {
      // Isolated throwaway DB: canonical dataset + the lesson's extras, discarded after.
      const PGlite = await importPGlite();
      const db = new PGlite();
      const res = await fetch(DATASET_URL);
      if (res.ok) await db.exec(await res.text());
      await db.exec(setupSql);
      const out = shape(await db.query(sql));
      return { ...out, error: null };
    }
    // Shared DB, serialized, wrapped so mutations don't persist between runs.
    const run = _queue.then(async () => {
      const db = await getSharedDb();
      await db.exec('BEGIN');
      try {
        const out = shape(await db.query(sql));
        return { ...out, error: null };
      } finally {
        await db.exec('ROLLBACK');
      }
    });
    // Keep the queue alive even if this run rejects.
    _queue = run.catch(() => {});
    return await run;
  } catch (e) {
    const msg = (e && e.message) ? e.message : String(e);
    return { columns: [], rows: [], affectedRows: null, error: msg };
  }
}

export default runSql;
