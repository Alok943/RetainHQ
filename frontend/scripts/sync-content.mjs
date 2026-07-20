#!/usr/bin/env node
/**
 * sync-content.mjs
 * Copies lesson content JSONs from `content/roadmaps/` (repo root) into
 * `frontend/public/content/roadmaps/` and emits a manifest.json that maps
 * { [roadmapKey]: { [exact node title]: slug } }.
 *
 * Wired as `predev` / `prebuild` so content is always fresh.
 */

import { readdir, readFile, mkdir, writeFile, cp, stat } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..', '..');
const CONTENT_ROOT = join(REPO_ROOT, 'content', 'roadmaps');
const PUBLIC_ROOT = join(__dirname, '..', 'public', 'content', 'roadmaps');
const MANIFEST_PATH = join(__dirname, '..', 'public', 'content', 'manifest.json');
const SITEMAP_PATH = join(__dirname, '..', 'public', 'sitemap.xml');
const BASE_URL = 'https://retainhq.app';

// Most-recent-commit date per file under content/roadmaps, keyed by the git-relative
// (forward-slash) path. One `git log` call for all ~640 files rather than one per file.
// git log walks newest-first, so the first date seen for a path is its most recent commit.
function buildGitDateMap() {
  const map = new Map();
  let out;
  try {
    out = execFileSync(
      'git',
      ['log', '--name-only', '--pretty=format:%x01%cs', '--', 'content/roadmaps'],
      { cwd: REPO_ROOT, encoding: 'utf-8', maxBuffer: 64 * 1024 * 1024 }
    );
  } catch {
    return map; // not a git repo / git unavailable — caller falls back per-file
  }
  for (const chunk of out.split('\x01')) {
    if (!chunk) continue;
    const lines = chunk.split('\n');
    const date = lines[0];
    for (let i = 1; i < lines.length; i++) {
      const file = lines[i].trim();
      if (!file || map.has(file)) continue;
      map.set(file, date);
    }
  }
  return map;
}

// Best-effort lastmod for one lesson file: git history first, then file mtime.
// Returns null (omit <lastmod>) only if both are unavailable — an absent lastmod
// is more honest than a fabricated "today".
async function lastmodFor(gitDateMap, relPath, absPath) {
  const gitDate = gitDateMap.get(relPath);
  if (gitDate) return gitDate;
  try {
    const st = await stat(absPath);
    return st.mtime.toISOString().split('T')[0];
  } catch {
    return null;
  }
}

function urlEntry(path, priority, changefreq, lastmod) {
  const lastmodTag = lastmod ? `\n    <lastmod>${lastmod}</lastmod>` : '';
  return `  <url>\n    <loc>${BASE_URL}${path}</loc>${lastmodTag}\n    <changefreq>${changefreq}</changefreq>\n    <priority>${priority}</priority>\n  </url>`;
}

// max() that treats null/undefined as "no date" and ignores them.
function newer(a, b) {
  if (!a) return b;
  if (!b) return a;
  return a > b ? a : b;
}

async function main() {
  const manifest = {};
  // Collected for the generated sitemap: every static lesson page is its own
  // crawlable, keyword-targeted URL.
  const lessonEntries = []; // { url, lastmod }
  const roadmapKeys = new Set();
  const roadmapLastmod = new Map(); // roadmapKey -> newest child lesson date
  let siteLastmod = null; // newest lesson date across all roadmaps, for home + /roadmaps

  let roadmapDirs;
  try {
    roadmapDirs = await readdir(CONTENT_ROOT, { withFileTypes: true });
  } catch {
    console.log('[sync-content] No content/roadmaps directory found — skipping.');
    return;
  }

  const gitDateMap = buildGitDateMap();

  for (const entry of roadmapDirs) {
    if (!entry.isDirectory()) continue;
    const roadmapKey = entry.name;
    const srcDir = join(CONTENT_ROOT, roadmapKey);
    const destDir = join(PUBLIC_ROOT, roadmapKey);

    await mkdir(destDir, { recursive: true });

    const files = await readdir(srcDir);
    for (const file of files) {
      // Non-JSON assets a roadmap needs at runtime (e.g. SQL seed datasets) are copied as-is.
      if (file.endsWith('.sql')) {
        await cp(join(srcDir, file), join(destDir, file), { force: true });
        continue;
      }
      if (!file.endsWith('.json')) continue;

      const srcPath = join(srcDir, file);
      const destPath = join(destDir, file);

      // Copy the file
      await cp(srcPath, destPath, { force: true });

      // `_`-prefixed files are roadmap-level sidecars (e.g. _foundations.json), not
      // lessons: copied so the app can fetch them, but they get no manifest entry and
      // no sitemap URL — there is no /learn/_foundations page for a crawler to reach.
      if (file.startsWith('_')) continue;

      // Parse to build the manifest entry
      try {
        const raw = await readFile(srcPath, 'utf-8');
        const lesson = JSON.parse(raw);
        const key = lesson.roadmap || roadmapKey;
        const slug = lesson.slug || file.replace('.json', '');
        const title = lesson.title;

        if (!title) continue;
        if (!manifest[key]) manifest[key] = {};
        manifest[key][title] = slug;

        const relPath = `content/roadmaps/${roadmapKey}/${file}`;
        const lastmod = await lastmodFor(gitDateMap, relPath, srcPath);
        roadmapLastmod.set(roadmapKey, newer(roadmapLastmod.get(roadmapKey), lastmod));
        siteLastmod = newer(siteLastmod, lastmod);

        // URL segment is the route slug = content folder key.
        lessonEntries.push({ url: `/roadmaps/${roadmapKey}/learn/${slug}`, lastmod });
        roadmapKeys.add(roadmapKey);
      } catch (err) {
        console.warn(`[sync-content] Skipping ${file}: ${err.message}`);
      }
    }

    // Second pass: copy _numericals/ subdirectory if it exists (physics phase-end practice sets).
    const numDir = join(srcDir, '_numericals');
    let numFiles;
    try { numFiles = await readdir(numDir); } catch { numFiles = []; }
    if (numFiles.length) {
      const numDest = join(destDir, '_numericals');
      await mkdir(numDest, { recursive: true });
      for (const nf of numFiles) {
        if (!nf.endsWith('.json')) continue;
        await cp(join(numDir, nf), join(numDest, nf), { force: true });
      }
    }

    // Third pass: copy _test/ subdirectory if it exists (Tests-section question banks,
    // docs/SPEC-test-runtime.md). Same shape as _numericals — a phase-keyed JSON file.
    const testDir = join(srcDir, '_test');
    let testFiles;
    try { testFiles = await readdir(testDir); } catch { testFiles = []; }
    if (testFiles.length) {
      const testDest = join(destDir, '_test');
      await mkdir(testDest, { recursive: true });
      for (const tf of testFiles) {
        if (!tf.endsWith('.json')) continue;
        await cp(join(testDir, tf), join(testDest, tf), { force: true });
      }
    }
  }

  // Write manifest
  await mkdir(dirname(MANIFEST_PATH), { recursive: true });
  await writeFile(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + '\n');

  // Write sitemap — home + roadmap list + each roadmap + every lesson page.
  // lastmod on hub/static routes is the newest date among their child lessons (or absent
  // entirely if that can't be determined), never today's date.
  const entries = [
    urlEntry('/', '1.0', 'weekly', siteLastmod),
    urlEntry('/roadmaps', '0.8', 'weekly', siteLastmod),
    ...[...roadmapKeys].sort().map((k) => urlEntry(`/roadmaps/${k}`, '0.7', 'weekly', roadmapLastmod.get(k))),
    ...lessonEntries
      .sort((a, b) => (a.url < b.url ? -1 : a.url > b.url ? 1 : 0))
      .map((e) => urlEntry(e.url, '0.6', 'monthly', e.lastmod)),
  ];
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries.join('\n')}\n</urlset>\n`;
  await writeFile(SITEMAP_PATH, sitemap);

  const totalLessons = Object.values(manifest).reduce((s, m) => s + Object.keys(m).length, 0);
  const missingLastmod = lessonEntries.filter((e) => !e.lastmod).length;
  console.log(`[sync-content] Synced ${totalLessons} lesson(s) across ${Object.keys(manifest).length} roadmap(s).`);
  console.log(`[sync-content] Wrote sitemap with ${entries.length} URL(s).${missingLastmod ? ` ${missingLastmod} lesson(s) missing lastmod.` : ''}`);
}

main().catch((err) => {
  console.error('[sync-content] Fatal:', err);
  process.exit(1);
});
