// Golden runner: finds and runs every *.golden.mjs under src/dsa, reports pass/fail, exits 1 on
// any failure. Wired as `npm run golden`. Each golden is a self-contained node script that asserts
// its generator's trace invariants (and, for compile-frames, byte-identical compiled frames).
// See docs/dsa-viz-implementation-plan.md (M0).
import { readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import { execFileSync } from 'node:child_process';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const dsaDir = join(root, 'src', 'dsa');

function findGoldens(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...findGoldens(full));
    else if (entry.name.endsWith('.golden.mjs')) out.push(full);
  }
  return out;
}

const files = findGoldens(dsaDir).sort();
if (!files.length) { console.error('No *.golden.mjs files found under src/dsa'); process.exit(1); }

let failed = 0;
for (const f of files) {
  const rel = relative(root, f);
  try {
    execFileSync(process.execPath, [f], { stdio: 'ignore' });
    console.log(`  PASS  ${rel}`);
  } catch {
    failed++;
    console.error(`  FAIL  ${rel}`);
    try { execFileSync(process.execPath, [f], { stdio: 'inherit' }); } catch { /* already reported */ }
  }
}
console.log(failed === 0
  ? `\nAll ${files.length} golden suite(s) passed.`
  : `\n${failed}/${files.length} golden suite(s) FAILED.`);
process.exit(failed === 0 ? 0 : 1);
