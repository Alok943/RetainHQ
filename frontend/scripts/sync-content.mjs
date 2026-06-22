#!/usr/bin/env node
/**
 * sync-content.mjs
 * Copies lesson content JSONs from `content/roadmaps/` (repo root) into
 * `frontend/public/content/roadmaps/` and emits a manifest.json that maps
 * { [roadmapKey]: { [exact node title]: slug } }.
 *
 * Wired as `predev` / `prebuild` so content is always fresh.
 */

import { readdir, readFile, mkdir, writeFile, cp } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CONTENT_ROOT = join(__dirname, '..', '..', 'content', 'roadmaps');
const PUBLIC_ROOT = join(__dirname, '..', 'public', 'content', 'roadmaps');
const MANIFEST_PATH = join(__dirname, '..', 'public', 'content', 'manifest.json');

async function main() {
  const manifest = {};

  let roadmapDirs;
  try {
    roadmapDirs = await readdir(CONTENT_ROOT, { withFileTypes: true });
  } catch {
    console.log('[sync-content] No content/roadmaps directory found — skipping.');
    return;
  }

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
      } catch (err) {
        console.warn(`[sync-content] Skipping ${file}: ${err.message}`);
      }
    }
  }

  // Write manifest
  await mkdir(dirname(MANIFEST_PATH), { recursive: true });
  await writeFile(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + '\n');

  const totalLessons = Object.values(manifest).reduce((s, m) => s + Object.keys(m).length, 0);
  console.log(`[sync-content] Synced ${totalLessons} lesson(s) across ${Object.keys(manifest).length} roadmap(s).`);
}

main().catch((err) => {
  console.error('[sync-content] Fatal:', err);
  process.exit(1);
});
