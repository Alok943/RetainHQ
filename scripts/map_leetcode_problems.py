"""LeetCode problem -> concept mapping via the paid Gemini API.

NOT THE PRODUCTION PATH. Production mapping is done by Antigravity inside its own
subscription session, per content/PROMPT-leetcode-mapping.md - no API key, no API spend.

This script exists as an INDEPENDENT VERIFICATION tool: it produced the 91.0%/94.7%
calibration numbers quoted in that prompt, and can re-run the golden gate against a
known-real API call if an Antigravity result ever looks too good to be true. Running
`full` here would spend real money on the owner's key for work Antigravity does free -
don't, unless explicitly asked.

Contract: content/PROMPT-leetcode-mapping.md. The system prompt, vocabulary, and
scaffold list are PARSED FROM THAT FILE AT RUNTIME (never retyped here) so the prompt
doc stays the single source of truth. If you're editing the prompt's wording, you're
done; if you're editing behavior, edit the prompt, not this file.

This script does NOT do the guessing. It builds the request, POSTS it to Gemini, and
validates + records the response. There is no fallback classifier. A batch that fails
twice is parked, not guessed. See the boundary block at the top of the prompt file for
why that rule exists (2026-07-21 incident: a keyword lookup table stamped a model name
on its own output and passed every distributional health check).

!! THIS SCRIPT SPENDS REAL MONEY AND REFUSES TO RUN WITHOUT TWO EXPLICIT CONFIRMATIONS !!

    RETAINHQ_ALLOW_API_SPEND=1 python scripts/map_leetcode_problems.py golden --i-will-pay
    RETAINHQ_ALLOW_API_SPEND=1 python scripts/map_leetcode_problems.py full --i-will-pay

Without BOTH the env var and the flag it exits immediately. Added 2026-07-22 after an
unattended `full` run billed the owner despite a docstring telling it not to. Agents read
files and run commands; only a hard guard stops a spend.

Reads GEMINI_API_KEY from backend/.env. Requires google-genai (already a backend dep;
run with backend/.venv/Scripts/python.exe if it's not on the active interpreter).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import concurrent.futures
from collections import Counter
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parent.parent
CAT_DIR = ROOT / "content" / "leetcode-catalog"
PROMPT_PATH = ROOT / "content" / "PROMPT-leetcode-mapping.md"
ENV_PATH = ROOT / "backend" / ".env"

BATCH_SIZE = 40
# This script is the API-side VERIFICATION path only (see module docstring). Production
# mapping runs in Antigravity on gemini-3.1-pro with no API spend.
# flash-lite matches the owner's default tier for incidental API tasks. Note the tradeoff:
# the 91.0%/94.7% calibration in the prompt came from gemini-3.6-flash, so re-verifying on
# flash-lite compares against a WEAKER referee - pass --model gemini-3.6-flash when the
# point is to reproduce the calibration numbers rather than spot-check cheaply.
DEFAULT_MODEL = "gemini-3.5-flash-lite"   # owner default 2026-07-21 (cheapest tier)
FALLBACK_MODEL = "gemini-3.5-flash"       # confirmed live 2026-07-20, D-037

SCAFFOLD_MAX_REPEAT = 3      # authenticity check: no reason string on >3 problems
SCAFFOLD_MIN_DISTINCT_PCT = 0.60
MIN_ALT_COMBOS = 30
MAX_PRIMARY_SHARE = 0.08
MIN_AMBIGUOUS_SHARE = 0.08

WATCH_SLUGS = [
    "gcd-lcm-and-modular-arithmetic", "combinatorics-and-counting", "bitmask-dp",
    "pattern-matching-kmp", "rolling-hash-rabin-karp", "ordered-sets-and-sorted-containers",
]


# --------------------------------------------------------------------------- pydantic

class MappingRow(BaseModel):
    external_id: int
    primary: str
    supporting: list[str] = []
    alternatives: list[str] = []
    confidence: Literal["high", "medium", "low"]
    reason: str


class MappingBatch(BaseModel):
    results: list[MappingRow]


# --------------------------------------------------------------------------- prompt parsing

def load_prompt_contract() -> dict:
    text = PROMPT_PATH.read_text(encoding="utf-8")

    sec1 = text.split("## 1. SYSTEM PROMPT (send verbatim)", 1)[1]
    sec1, _ = sec1.split("## 2. USER MESSAGE", 1)
    blocks = re.findall(r"```\n(.*?)```", sec1, re.S)
    if len(blocks) < 2:
        sys.exit("FAIL  could not find vocabulary/scaffold blocks in the prompt file")
    vocab = set(blocks[0].split())
    scaffold = set(blocks[1].split())

    system_prompt = sec1.rsplit("```", 1)[-1].strip()
    # sec1 ends right after the scaffold block's prose (the "DO NOT" list); system_prompt
    # above only grabs post-block text, so rebuild the full verbatim block properly:
    system_prompt = sec1.strip()

    return {"system_prompt": system_prompt, "vocab": vocab, "scaffold": scaffold}


def load_gemini_key() -> str:
    if not ENV_PATH.exists():
        sys.exit(f"FAIL  {ENV_PATH} not found")
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("GEMINI_API_KEY="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                return val
    sys.exit("FAIL  GEMINI_API_KEY is empty or missing in backend/.env")


# --------------------------------------------------------------------------- model call

class Caller:
    """Thin wrapper around google-genai. Tracks every real call made."""

    def __init__(self, model: str, system_prompt: str):
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            sys.exit(
                "FAIL  google-genai not installed on this interpreter. Run with "
                "backend/.venv/Scripts/python.exe scripts/map_leetcode_problems.py ...\n"
                f"      ({e})"
            )
        self._genai = genai
        self._types = types
        self.client = genai.Client(api_key=load_gemini_key())
        self.system_prompt = system_prompt
        self.model = model
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.wall_start = time.time()
        self._verified = False

    def verify_model(self) -> None:
        """One tiny real call to confirm the model id is callable before spending
        a whole batch run on it. Falls back once; never fabricates success."""
        probe = [{"external_id": 1, "slug": "two-sum", "title": "Two Sum",
                   "difficulty": "easy", "tags": ["array", "hash-table"]}]
        try:
            self._raw_call(probe)
            self._verified = True
            print(f"  model verified: {self.model}")
        except Exception as e:
            if self.model != FALLBACK_MODEL:
                print(f"  {self.model} unavailable ({e}) -> falling back to {FALLBACK_MODEL}")
                self.model = FALLBACK_MODEL
                self._raw_call(probe)
                self._verified = True
                print(f"  model verified: {self.model}")
            else:
                sys.exit(f"FAIL  neither model is callable: {e}")

    def _raw_call(self, problems: list[dict]) -> MappingBatch:
        user_msg = (
            "Classify these problems. Return ONE object per problem, in input order.\n\n"
            + json.dumps(problems, ensure_ascii=False)
        )
        resp = self.client.models.generate_content(
            model=self.model,
            contents=[user_msg],
            config=self._types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                response_mime_type="application/json",
                response_schema=MappingBatch,
                temperature=0,
                max_output_tokens=8192,
            ),
        )
        self.calls += 1
        usage = getattr(resp, "usage_metadata", None)
        if usage:
            self.input_tokens += getattr(usage, "prompt_token_count", 0) or 0
            self.output_tokens += getattr(usage, "candidates_token_count", 0) or 0
        text = getattr(resp, "text", None)
        if not text:
            raise RuntimeError("empty response")
        return MappingBatch.model_validate_json(text)

    def classify_batch(self, problems: list[dict]) -> Optional[MappingBatch]:
        for attempt in range(2):
            try:
                return self._raw_call(problems)
            except (ValidationError, RuntimeError, Exception) as e:  # noqa: BLE001
                print(f"    batch attempt {attempt + 1} failed: {e}")
        return None


# --------------------------------------------------------------------------- validation

def validate_rows(batch: MappingBatch, input_ids: set[int], vocab: set[str],
                   scaffold: set[str]) -> tuple[list[MappingRow], list[str], set[int]]:
    """Returns (accepted_rows, errors, rejected_ids).

    rejected_ids MUST be retried or parked by the caller - never silently dropped.
    The 2026-07-21 flash-lite run lost 662 of 3,999 problems (16.6%) to per-row
    rejections that were printed and then discarded, and the run still reported
    itself complete because it only ever counted the rows that survived.
    """
    problems = []
    errs = []
    got_ids = {r.external_id for r in batch.results}
    if got_ids != input_ids:
        errs.append(f"external_id mismatch: expected {sorted(input_ids)}, got {sorted(got_ids)}")
        return [], errs, set(input_ids)

    rejected: set[int] = set()
    for r in batch.results:
        if r.primary != "out_of_scope":
            if r.primary not in vocab:
                errs.append(f"#{r.external_id}: primary {r.primary!r} not in vocabulary")
                rejected.add(r.external_id)
                continue
            if r.primary in scaffold:
                errs.append(f"#{r.external_id}: primary {r.primary!r} is a scaffold slug")
                rejected.add(r.external_id)
                continue
        bad_sup = [s for s in r.supporting if s not in vocab]
        bad_alt = [s for s in r.alternatives if s not in vocab]
        if bad_sup or bad_alt:
            # Salvage: drop only the offending secondary slugs, keep a valid primary.
            r.supporting = [s for s in r.supporting if s in vocab]
            r.alternatives = [s for s in r.alternatives if s in vocab]
            errs.append(f"#{r.external_id}: dropped unknown slug(s) supporting={bad_sup} alternatives={bad_alt}")
        r.supporting = [s for s in dict.fromkeys(r.supporting) if s != r.primary]
        r.alternatives = [s for s in dict.fromkeys(r.alternatives) if s != r.primary]
        overlap = set(r.supporting) & set(r.alternatives)
        if overlap:
            r.alternatives = [s for s in r.alternatives if s not in overlap]
        problems.append(r)
    return problems, errs, rejected


# --------------------------------------------------------------------------- golden gate

def cmd_golden(caller: Caller, contract: dict) -> bool:
    golden = json.loads((CAT_DIR / "golden.json").read_text(encoding="utf-8"))
    catalog = {p["external_id"]: p for p in
               json.loads((CAT_DIR / "catalog.v1.json").read_text(encoding="utf-8"))["problems"]}

    rows_in = []
    for g in golden:
        c = catalog.get(g["external_id"])
        if not c:
            print(f"  WARN #{g['external_id']} not in catalog, skipping")
            continue
        rows_in.append({"external_id": c["external_id"], "slug": c["slug"], "title": c["title"],
                         "difficulty": c["difficulty"], "tags": c["tags"]})

    results: dict[int, MappingRow] = {}
    for i in range(0, len(rows_in), BATCH_SIZE):
        chunk = rows_in[i:i + BATCH_SIZE]
        ids = {p["external_id"] for p in chunk}
        print(f"  batch {i // BATCH_SIZE + 1}: {len(chunk)} problems...")
        batch = caller.classify_batch(chunk)
        if batch is None:
            print(f"  batch {i // BATCH_SIZE + 1} PARKED (failed twice)")
            continue
        rows, errs, _rej = validate_rows(batch, ids, contract["vocab"], contract["scaffold"])
        for e in errs:
            print(f"    reject: {e}")
        for r in rows:
            results[r.external_id] = r

    by_id = {g["external_id"]: g for g in golden}
    anchored_hit = anchored_n = blind_hit = blind_n = 0
    confusion = []
    conf_band = Counter()
    conf_band_hit = Counter()
    for eid, g in by_id.items():
        r = results.get(eid)
        if r is None:
            continue
        hit = r.primary == g["human_primary"]
        conf_band[r.confidence] += 1
        conf_band_hit[r.confidence] += int(hit)
        if g.get("anchored"):
            anchored_n += 1
            anchored_hit += int(hit)
        else:
            blind_n += 1
            blind_hit += int(hit)
        if not hit:
            confusion.append((eid, g["title"], g["human_primary"], r.primary, r.reason))

    print()
    print(f"anchored agreement: {anchored_hit}/{anchored_n} ({anchored_hit/max(anchored_n,1):.1%})")
    print(f"BLIND agreement:    {blind_hit}/{blind_n} ({blind_hit/max(blind_n,1):.1%})  <- key metric")
    print()
    print("agreement by model confidence band:")
    for band in ("high", "medium", "low"):
        n = conf_band[band]
        h = conf_band_hit[band]
        print(f"  {band:<7} {h}/{n} ({h/max(n,1):.1%})")
    print()
    print(f"confusion list ({len(confusion)}):")
    for eid, title, human, model, reason in confusion:
        print(f"  #{eid:<5} {title[:34]:<34} human={human:<28} model={model:<28} | {reason}")

    high_n = conf_band["high"]
    high_hit = conf_band_hit["high"]
    passed = high_n > 0 and (high_hit / high_n) >= 0.85
    print()
    print(f"{'PASSED' if passed else 'FAILED'} - high-confidence gate needs >=85%, "
          f"got {high_hit}/{high_n} ({high_hit/max(high_n,1):.1%})")
    print(f"calls={caller.calls} in_tokens={caller.input_tokens} out_tokens={caller.output_tokens} "
          f"wall={time.time()-caller.wall_start:.1f}s model={caller.model}")
    return passed


# --------------------------------------------------------------------------- full pass

def cmd_full(caller: Caller, contract: dict) -> None:
    catalog = json.loads((CAT_DIR / "catalog.v1.json").read_text(encoding="utf-8"))["problems"]
    parked = []
    rejected_ids: set[int] = set()
    mappings: list[MappingRow] = []

    chunks = []
    for i in range(0, len(catalog), BATCH_SIZE):
        chunk = [{"external_id": p["external_id"], "slug": p["slug"], "title": p["title"],
                  "difficulty": p["difficulty"], "tags": p["tags"]} for p in catalog[i:i + BATCH_SIZE]]
        chunks.append(chunk)

    total = len(chunks)
    completed = 0

    def process_chunk(chunk, index):
        ids = {p["external_id"] for p in chunk}
        batch = caller.classify_batch(chunk)
        if batch is None:
            return index, ids, None, None
        rows, errs = validate_rows(batch, ids, contract["vocab"], contract["scaffold"])
        return index, ids, rows, errs

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_chunk, chunk, i): chunk for i, chunk in enumerate(chunks)}
        for future in concurrent.futures.as_completed(futures):
            index, ids, rows, errs = future.result()
            n = index + 1
            completed += 1
            if rows is None:
                print(f"  batch {n}/{total} PARKED")
                parked.append(sorted(ids))
                continue
            for e in errs:
                print(f"    reject: {e}")
            mappings.extend(rows)
            if completed % 10 == 0 or completed == total:
                print(f"  batch completed: {completed}/{total}  mapped so far: {len(mappings)}  calls: {caller.calls}")

    # Retry every rejected row once. Anything still bad is PARKED and reported -
    # never silently absent from the output.
    if rejected_ids:
        print(f"\n  retrying {len(rejected_ids)} rejected problem(s)...")
        by_id = {p["external_id"]: p for p in catalog}
        retry = [{"external_id": p["external_id"], "slug": p["slug"], "title": p["title"],
                  "difficulty": p["difficulty"], "tags": p["tags"]}
                 for i in sorted(rejected_ids) if (p := by_id.get(i))]
        still_bad: set[int] = set()
        for i in range(0, len(retry), BATCH_SIZE):
            chunk = retry[i:i + BATCH_SIZE]
            ids = {p["external_id"] for p in chunk}
            batch = caller.classify_batch(chunk)
            if batch is None:
                still_bad |= ids
                continue
            rows, errs, rej = validate_rows(batch, ids, contract["vocab"], contract["scaffold"])
            mappings.extend(rows)
            still_bad |= rej
        if still_bad:
            parked.append(sorted(still_bad))
            print(f"  {len(still_bad)} problem(s) PARKED after retry")

    mapped_ids = {r.external_id for r in mappings}
    absent = [p["external_id"] for p in catalog if p["external_id"] not in mapped_ids]
    if absent:
        print(f"\n  WARNING: {len(absent)}/{len(catalog)} catalog problems have NO mapping row")

    write_full_output(mappings, parked, caller, total_catalog=len(catalog))



def write_full_output(mappings: list[MappingRow], parked: list, caller: Caller,
                      total_catalog: int = 0) -> None:
    counts = Counter(r.confidence for r in mappings)
    n_oos = sum(1 for r in mappings if r.primary == "out_of_scope")
    envelope = {
        "mapping_version": "v1",
        "catalog_version": "v1",
        "model": caller.model,
        "prompt_version": "1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts": {"mapped": len(mappings), "out_of_scope": n_oos,
                   "high": counts["high"], "medium": counts["medium"], "low": counts["low"]},
        "mappings": [
            {"external_id": r.external_id, "primary": r.primary, "supporting": r.supporting,
             "alternatives": r.alternatives, "confidence": r.confidence, "reason": r.reason,
             "reviewed_by": None}
            for r in mappings
        ],
    }
    (CAT_DIR / "mapping.v1.json").write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    report = run_checks_and_report(mappings, parked, caller, total_catalog)
    (ROOT / "content" / "REPORT-leetcode-mapping.md").write_text(report, encoding="utf-8")
    print("\nwrote mapping.v1.json and REPORT-leetcode-mapping.md")
    print(report)


def run_checks_and_report(mappings: list[MappingRow], parked: list, caller: Caller,
                          total_catalog: int = 0) -> str:
    lines = ["# LeetCode mapping report\n"]
    lines.append(f"Model: {caller.model}  |  API calls: {caller.calls}  |  "
                 f"in_tokens: {caller.input_tokens}  out_tokens: {caller.output_tokens}  |  "
                 f"wall: {time.time()-caller.wall_start:.1f}s\n")

    if total_catalog:
        missing = total_catalog - len(mappings)
        lines.append("## Coverage")
        lines.append(f"- {len(mappings)}/{total_catalog} catalog problems mapped "
                     f"({len(mappings)/total_catalog:.1%}) -> {'OK' if missing == 0 else 'FAIL'}")
        if missing:
            lines.append(f"- **{missing} problems have NO mapping row.** A run is not complete "
                         f"until every catalog problem is either mapped or explicitly parked.")
        lines.append("")

    reasons = Counter(r.reason for r in mappings)
    n = len(mappings)
    distinct_pct = len(reasons) / max(n, 1)
    max_repeat = max(reasons.values()) if reasons else 0
    auth_ok = max_repeat <= SCAFFOLD_MAX_REPEAT and distinct_pct >= SCAFFOLD_MIN_DISTINCT_PCT

    alt_combos = {tuple(sorted(r.alternatives)) for r in mappings if r.alternatives}
    alt_pct = sum(1 for r in mappings if r.alternatives) / max(n, 1)

    lines.append("## Authenticity checks")
    lines.append(f"- reason diversity: {len(reasons)} distinct / {n} rows ({distinct_pct:.1%}), "
                 f"max repeat {max_repeat}x -> {'OK' if auth_ok else 'FAIL'}")
    alt_ok = len(alt_combos) >= MIN_ALT_COMBOS and 0.10 <= alt_pct <= 0.40
    lines.append(f"- alternatives: {len(alt_combos)} distinct combos, {alt_pct:.1%} of rows carry one -> "
                 f"{'OK' if alt_ok else 'FAIL'}")
    lines.append(f"- call accounting: {caller.calls} calls for {n + sum(len(p) for p in parked)} problems")
    lines.append("")
    lines.append("### spot check (5 random rows)")
    for r in random.sample(mappings, min(5, len(mappings))):
        lines.append(f"- #{r.external_id} primary={r.primary} conf={r.confidence} :: {r.reason}")
    lines.append("")

    by_primary = Counter(r.primary for r in mappings)
    # out_of_scope is a bucket, not a concept - SQL/shell/JS legitimately cluster there,
    # so counting it against the concentration cap produces a false FAIL.
    concept_only = Counter({k: v for k, v in by_primary.items() if k != "out_of_scope"})
    n_concept = sum(concept_only.values())
    top_primary_share = max(concept_only.values()) / max(n_concept, 1) if concept_only else 0
    ambiguous = sum(1 for r in mappings if r.confidence in ("low", "medium"))
    ambiguous_pct = ambiguous / max(n, 1)

    lines.append("## Distributional health checks")
    top_slug = concept_only.most_common(1)[0][0] if concept_only else "-"
    lines.append(f"- max primary share (excl. out_of_scope): {top_primary_share:.1%} "
                 f"[{top_slug}] (cap {MAX_PRIMARY_SHARE:.0%}) -> "
                 f"{'OK' if top_primary_share <= MAX_PRIMARY_SHARE else 'FAIL'}")
    lines.append(f"- out_of_scope: {by_primary.get('out_of_scope', 0)} "
                 f"({by_primary.get('out_of_scope', 0)/max(n,1):.1%}) - reported, not capped")
    lines.append(f"- low+medium share: {ambiguous_pct:.1%} (floor {MIN_AMBIGUOUS_SHARE:.0%}) -> "
                 f"{'OK' if ambiguous_pct >= MIN_AMBIGUOUS_SHARE else 'FAIL'}")
    for slug in WATCH_SLUGS:
        lines.append(f"- {slug}: {by_primary.get(slug, 0)} problems")
    lines.append("")
    lines.append("### top 15 / bottom (zero-usage) slugs")
    for s, c in by_primary.most_common(15):
        lines.append(f"  {c:5d}  {s}")
    lines.append("")
    lines.append(f"parked batches: {len(parked)}")
    for p in parked:
        lines.append(f"  {p}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["golden", "full"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--i-will-pay", action="store_true",
                    help="Required for any run. Confirms you accept real API charges on "
                         "GEMINI_API_KEY. Production mapping is free via Antigravity.")
    args = ap.parse_args()

    # HARD SPEND GUARD - not a docstring warning.
    #
    # 2026-07-22: this script was run unattended with no arguments (mode `full`,
    # DEFAULT_MODEL, key auto-read from backend/.env) despite the owner's explicit
    # instruction that mapping runs in Antigravity on subscription quota, and despite a
    # docstring saying not to. It billed real money. A comment does not stop an agent
    # or a careless shell command; an argparse flag does.
    #
    # Both gates below must be satisfied, so neither an agent reading the file nor a
    # copy-pasted command can spend money without a human typing the flag.
    if not args.i_will_pay:
        sys.exit(
            "REFUSED - this script spends real money on GEMINI_API_KEY.\n"
            "  Production mapping does NOT use this script: it runs inside Antigravity on\n"
            "  subscription quota, per content/PROMPT-leetcode-mapping.md.\n"
            "  This script is the API-side VERIFICATION path only.\n"
            "  If you genuinely intend to be billed, re-run with --i-will-pay "
            "and RETAINHQ_ALLOW_API_SPEND=1."
        )
    if os.environ.get("RETAINHQ_ALLOW_API_SPEND") != "1":
        sys.exit(
            "REFUSED - --i-will-pay given but RETAINHQ_ALLOW_API_SPEND is not set to 1.\n"
            "  Two independent confirmations are required for a billable run."
        )
    if args.mode == "full":
        print("WARNING: `full` mode maps the entire catalog (~100 calls). "
              "`golden` mode costs ~6 calls and answers most questions.")

    contract = load_prompt_contract()
    print(f"loaded contract: {len(contract['vocab'])} vocab slugs, "
          f"{len(contract['scaffold'])} scaffold slugs")

    caller = Caller(model=args.model, system_prompt=contract["system_prompt"])
    caller.verify_model()

    if args.mode == "golden":
        passed = cmd_golden(caller, contract)
        return 0 if passed else 1
    else:
        cmd_full(caller, contract)
        return 0


if __name__ == "__main__":
    sys.exit(main())
