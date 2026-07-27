// Packs the two archives AMO needs: the built extension and the source.
//
// Do NOT use PowerShell's Compress-Archive for this. It writes Windows
// backslashes as ZIP path separators, which the spec forbids and AMO rejects
// outright ("Invalid file name in archive"). It also has no exclude support, so
// Vite's internal `.vite/manifest.json` ends up inside the extension zip — a
// dot-directory AMO also refuses, and a file the extension does not need.
import { createWriteStream } from 'node:fs';
import { mkdir, readdir, stat, readFile } from 'node:fs/promises';
import { join, relative, sep } from 'node:path';
import { deflateRawSync } from 'node:zlib';

const ROOT = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const OUT = join(ROOT, 'submit');
const SKIP = new Set(['node_modules', 'dist', 'dist-firefox', 'submit', '.vite', '.git']);
// Secrets never go to Mozilla. VITE_SUPABASE_ANON_KEY is public by design (it
// ships in the bundle regardless), but a source upload is not the place for an
// env file, and the next thing added to it might not be public.
const SKIP_FILES = new Set(['.env', '.env.local', '.env.development', '.env.production']);

async function walk(dir, base, acc = []) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (SKIP.has(entry.name) || SKIP_FILES.has(entry.name)) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) await walk(full, base, acc);
    else acc.push({ full, arc: relative(base, full).split(sep).join('/') });
  }
  return acc;
}

function crc32(buf) {
  let c, table = [];
  for (let n = 0; n < 256; n++) {
    c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  let crc = 0xffffffff;
  for (const b of buf) crc = table[(crc ^ b) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

async function zip(files, dest) {
  const chunks = [], central = [];
  let offset = 0;
  for (const f of files) {
    const data = await readFile(f.full);
    const comp = deflateRawSync(data);
    const name = Buffer.from(f.arc, 'utf8');
    const crc = crc32(data);

    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(20, 4);
    local.writeUInt16LE(0, 6); local.writeUInt16LE(8, 8);
    local.writeUInt32LE(crc, 14); local.writeUInt32LE(comp.length, 18);
    local.writeUInt32LE(data.length, 22); local.writeUInt16LE(name.length, 26);
    chunks.push(local, name, comp);

    const cen = Buffer.alloc(46);
    cen.writeUInt32LE(0x02014b50, 0); cen.writeUInt16LE(20, 4); cen.writeUInt16LE(20, 6);
    cen.writeUInt16LE(8, 10); cen.writeUInt32LE(crc, 16);
    cen.writeUInt32LE(comp.length, 20); cen.writeUInt32LE(data.length, 24);
    cen.writeUInt16LE(name.length, 28); cen.writeUInt32LE(offset, 42);
    central.push(cen, name);
    offset += local.length + name.length + comp.length;
  }
  const cdSize = central.reduce((n, b) => n + b.length, 0);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(files.length, 8); end.writeUInt16LE(files.length, 10);
  end.writeUInt32LE(cdSize, 12); end.writeUInt32LE(offset, 16);

  await new Promise((res, rej) => {
    const s = createWriteStream(dest);
    s.on('error', rej); s.on('finish', res);
    for (const c of [...chunks, ...central, end]) s.write(c);
    s.end();
  });
  return files.length;
}

await mkdir(OUT, { recursive: true });
const distDir = join(ROOT, 'dist-firefox');
await stat(distDir).catch(() => { throw new Error('dist-firefox/ missing — run `npm run build:firefox` first'); });

const ext = await walk(distDir, distDir);
const src = await walk(ROOT, ROOT);
console.log(`extension: ${await zip(ext, join(OUT, 'companion-extension.zip'))} files`);
console.log(`source:    ${await zip(src, join(OUT, 'companion-source.zip'))} files`);

for (const f of [...ext, ...src]) {
  const parts = f.arc.split('/');
  // AMO rejects backslash separators and dot-DIRECTORIES. A root dotfile like
  // .gitignore is fine; an env file is not, at any depth.
  if (f.arc.includes('\\') || parts.slice(0, -1).some((p) => p.startsWith('.')) || SKIP_FILES.has(parts.at(-1))) {
    throw new Error(`invalid archive path: ${f.arc}`);
  }
}
console.log('paths verified: forward slashes only, no dot-directories, no env files');
