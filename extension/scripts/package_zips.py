"""Package dist-firefox/ and dist-chrome/ into store-submittable zips.

WHY THIS EXISTS INSTEAD OF `Compress-Archive`
---------------------------------------------
Windows PowerShell 5.1's `Compress-Archive` writes entry names using the OS
path separator, so every nested file lands in the archive as
`assets\\foo.js` rather than `assets/foo.js`. The ZIP spec (APPNOTE 4.4.17.1)
requires forward slashes, and AMO rejects such an archive outright:

    Invalid file name in archive: assets\\activity_tracker-DX2XVkAx.js

It reports only the FIRST offending entry, so fixing that one file and
re-uploading just surfaces the next — the whole archive is malformed, not one
file in it.

This was initially misdiagnosed as cosmetic because `zipfile.namelist()`
NORMALIZES backslashes to forward slashes on read — so a Python-based check
reports a clean archive while the bytes on disk are malformed. The
verification below therefore parses the raw local-file-header bytes rather
than trusting the library, which is the only check that would actually have
caught it.

Usage (from extension/):
    python scripts/package_zips.py

The source archive (companion-source.zip) is NOT built here — `git archive`
already emits spec-correct forward slashes and, unlike walking the working
tree, includes exactly the tracked files and nothing else (no .env, no
node_modules, no dist output):

    git archive --format=zip -o extension/submit/companion-source.zip HEAD:extension
"""
import struct
import sys
import zipfile
from pathlib import Path

EXTENSION_ROOT = Path(__file__).resolve().parent.parent
SUBMIT_DIR = EXTENSION_ROOT / "submit"

TARGETS = [
    ("dist-firefox", "companion-extension.zip"),
    ("dist-chrome", "companion-chrome.zip"),
]


def build(src_dir: Path, out_path: Path) -> int:
    """Zip `src_dir`'s CONTENTS (not the directory itself) with POSIX names."""
    files = sorted(p for p in src_dir.rglob("*") if p.is_file())
    if not files:
        sys.exit(f"ERROR: {src_dir} is empty or missing — run the build first.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            # .as_posix() is the whole point — forward slashes on every OS.
            arcname = f.relative_to(src_dir).as_posix()
            # Defence in depth: the build scripts already strip .vite/, but a
            # hidden dot-entry is an automatic AMO rejection, so never package
            # one even if a future build step reintroduces it.
            if any(part.startswith(".") for part in arcname.split("/")):
                print(f"  skipped hidden entry: {arcname}")
                continue
            z.write(f, arcname)
    return len(files)


def raw_entry_names(zip_path: Path) -> list[bytes]:
    """Entry names read straight from local file headers — no library
    normalization in the way. See the module docstring for why that matters."""
    data = zip_path.read_bytes()
    names, off = [], 0
    while (i := data.find(b"PK\x03\x04", off)) != -1:
        name_len = struct.unpack_from("<H", data, i + 26)[0]
        names.append(data[i + 30: i + 30 + name_len])
        off = i + 4
    return names


def main() -> None:
    failed = False
    for src_name, zip_name in TARGETS:
        src = EXTENSION_ROOT / src_name
        out = SUBMIT_DIR / zip_name
        if out.exists():
            out.unlink()
        build(src, out)

        names = raw_entry_names(out)
        backslash = [n for n in names if b"\\" in n]
        hidden = [n for n in names if any(p.startswith(b".") for p in n.split(b"/") if p)]

        status = "OK" if not backslash and not hidden else "FAIL"
        if status == "FAIL":
            failed = True
        print(
            f"[{status}] {zip_name}: {len(names)} entries, "
            f"{len(backslash)} backslash, {len(hidden)} hidden "
            f"({out.stat().st_size / 1024:.1f} KB)"
        )
        for n in backslash[:3]:
            print(f"        BAD: {n!r}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
