#!/usr/bin/env python3
"""Caveman validator for RetainHQ content JSON. Pure stdlib — no installs.

Run from the repo root:  python content/validate.py
Checks every roadmaps/<roadmap>/<slug>.json for:
  - required fields + correct types/enums
  - slug matches filename
  - sources present and look like URLs
  - prerequisites/unlocks resolve to other curated slugs in the SAME roadmap
Exits non-zero if anything fails, so it can gate a commit later.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "roadmaps"
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Prediction derive registry (frontend/src/dsa/predict.js). A lesson's viz.predictions[].derive
# must name a function that actually exists there — parsed from the source so the two can't drift.
_PREDICT_JS = Path(__file__).resolve().parent.parent / "frontend" / "src" / "dsa" / "predict.js"
try:
    _m = re.search(r"const DERIVES = \{(.*?)\n\};", _PREDICT_JS.read_text(encoding="utf-8"), re.S)
    DERIVE_NAMES = set(re.findall(r"^  (\w+)\(events", _m.group(1), re.M)) if _m else set()
except OSError:
    DERIVE_NAMES = set()
PREDICTION_LEVELS = {"easy", "medium", "hard", "expert"}

KIND = {"concept", "milestone", "aptitude", "reasoning", "theory", "engineering", "dsa", "physics", "numericals", "test"}
TIER = {"tier1", "tier2", "tier3"}
DIFF = {"easy", "medium", "hard"}
FREQ = {"low", "medium", "high"}
CHECK_TYPES = {"predict-output", "predict-result", "explain-behavior", "find-bug", "choose-model", "debug-misconception"}
RUNTIMES = {"python", "sql", "none"}

DIAGRAM_TYPES = {"ray", "circuit", "graph", "free-body", "image", "schematic"}

# Test-section question banks (content/PROMPT-tests.md, docs/SPEC-test-runtime.md).
TEST_TYPES = {"fillup", "numeric", "code-output", "code-fix", "code-write", "query-write", "mcq"}
RAY_OPTICS = {"concave-mirror", "convex-mirror", "concave-lens", "convex-lens"}

# diagram3d — interactive R3F concept simulators (content/PROMPT-physics-3d.md).
# Scoped to EXACTLY these 6 scene-kinds; nothing else gets 3D.
DIAGRAM3D_SCENES = {"orbit", "magnetic-field", "fleming-rule", "em-induction", "dispersion-prism", "longitudinal-wave"}
AXIS_VALUES = {"+x", "-x", "+y", "-y", "+z", "-z"}
MAGNETIC_SOURCES = {"bar-magnet", "straight-wire", "solenoid", "circular-loop"}
CURRENT_DIRECTIONS = {"into", "out", "n/a"}
FLEMING_RULES = {"left", "right"}
INDUCTION_MOTIONS = {"insert", "withdraw"}
INDUCTION_POLES = {"N", "S"}
AMPLITUDE_VALUES = {"soft", "loud"}

errors = []
warnings = []


def err(f, msg):
    errors.append(f"  [FAIL] {f}: {msg}")


def warn(f, msg):
    warnings.append(f"  [warn] {f}: {msg}")


def req(d, key, f, typ=None):
    if key not in d:
        err(f, f"missing required field '{key}'")
        return False
    if typ is not None and not isinstance(d[key], typ):
        err(f, f"'{key}' should be {typ.__name__}, got {type(d[key]).__name__}")
        return False
    return True


def extract_prose(d):
    prose = []
    
    # overview
    ov = d.get("overview", {})
    if isinstance(ov, dict):
        prose.extend([ov.get("what"), ov.get("why")])
        
    # why_it_exists
    wie = d.get("why_it_exists", {})
    if isinstance(wie, dict):
        prose.extend([wie.get("problem"), wie.get("naive_solution"), wie.get("better_idea")])
        
    # mental_model
    mm = d.get("mental_model", {})
    if isinstance(mm, dict):
        prose.extend([mm.get("intuition"), mm.get("description")])
        
    # explanation, analogy
    prose.extend([d.get("explanation"), d.get("analogy")])
    
    # sections[].body
    for s in d.get("sections", []) or []:
        if isinstance(s, dict):
            prose.append(s.get("body"))
            
    # why_learning_this[]
    wlt = d.get("why_learning_this", [])
    if isinstance(wlt, list):
        prose.extend(wlt)
        
    # method[]
    m = d.get("method", [])
    if isinstance(m, list):
        prose.extend(m)
        
    # formula.explain
    fm = d.get("formula", {})
    if isinstance(fm, dict):
        prose.append(fm.get("explain"))
        
    # worked_example
    we = d.get("worked_example")
    if isinstance(we, list):
        for w in we:
            if isinstance(w, dict):
                prose.extend([w.get("problem"), w.get("answer")])
                steps = w.get("steps")
                if isinstance(steps, list):
                    prose.extend(steps)
    elif isinstance(we, dict):
        prose.extend([we.get("problem"), we.get("answer")])
        steps = we.get("steps")
        if isinstance(steps, list):
            prose.extend(steps)

    # key_points[].detail
    kp = d.get("key_points")
    if isinstance(kp, list):
        for k in kp:
            if isinstance(k, dict):
                prose.append(k.get("detail"))

    # common_mistakes[].explanation
    cm = d.get("common_mistakes")
    if isinstance(cm, list):
        for c in cm:
            if isinstance(c, dict):
                prose.append(c.get("explanation"))

    return " ".join(str(x) for x in prose if isinstance(x, str) and x.strip())


def _validate_physics_diagram(diag, path, rel):
    """Validate a physics diagram object. Deep-checks for types with live renderers
    (ray, graph, image); membership-only for unbuilt types (circuit, free-body)."""
    if not isinstance(diag, dict):
        err(rel, f"{path} must be an object"); return
    dtype = diag.get("type")
    if dtype not in DIAGRAM_TYPES:
        err(rel, f"{path}.type must be one of {sorted(DIAGRAM_TYPES)}")
        return
    # --- Deep validation for types with live renderers ---
    if dtype == "ray":
        optic = diag.get("optic")
        if optic not in RAY_OPTICS:
            err(rel, f"{path}.optic must be one of {sorted(RAY_OPTICS)}")
        fl = diag.get("focal_length")
        if not isinstance(fl, (int, float)) or fl <= 0:
            err(rel, f"{path}.focal_length must be a positive number")
        od = diag.get("object_distance")
        if not isinstance(od, (int, float)) or od <= 0:
            err(rel, f"{path}.object_distance must be a positive number")
    elif dtype == "graph":
        axes = diag.get("axes")
        if not isinstance(axes, dict) or not axes.get("x") or not axes.get("y"):
            err(rel, f"{path}.axes must be an object with non-empty 'x' and 'y'")
        if not diag.get("curve") and not diag.get("line"):
            err(rel, f"{path} needs at least one of 'curve' or 'line'")
    elif dtype == "image":
        if not diag.get("asset"):
            err(rel, f"{path} needs a non-empty 'asset'")
    elif dtype == "schematic":
        bodies = diag.get("bodies")
        if not isinstance(bodies, list) or not bodies:
            err(rel, f"{path} needs a non-empty 'bodies' list")
        elif not all(isinstance(b, dict) and b.get("id") and isinstance(b.get("x"), (int, float))
                     and isinstance(b.get("y"), (int, float)) for b in bodies):
            err(rel, f"{path}.bodies each need 'id' and numeric 'x'/'y'")
    # circuit and free-body: membership-only, no deep checks (renderer not built yet)


def _validate_diagram3d(diag, path, rel):
    """Validate a `diagram3d` object (content/PROMPT-physics-3d.md). Checks the
    schema envelope, the scene-kind's required params, and the optional
    prediction/manipulate/reflection blocks. `poster`, if present, is a normal
    2D diagram object and reuses _validate_physics_diagram."""
    if not isinstance(diag, dict):
        err(rel, f"{path} must be an object"); return
    if diag.get("schema_version") != 1:
        err(rel, f"{path}.schema_version must be 1")
    scene = diag.get("scene")
    if scene not in DIAGRAM3D_SCENES:
        err(rel, f"{path}.scene must be one of {sorted(DIAGRAM3D_SCENES)}")
        return
    if not diag.get("caption"):
        err(rel, f"{path} needs a non-empty 'caption'")

    if scene == "orbit":
        central = diag.get("central")
        if not isinstance(central, dict) or not central.get("label") or not isinstance(central.get("mass"), (int, float)):
            err(rel, f"{path}.central must be an object with 'label' and numeric 'mass'")
        satellite = diag.get("satellite")
        if not isinstance(satellite, dict) or not satellite.get("label") or not isinstance(satellite.get("mass"), (int, float)):
            err(rel, f"{path}.satellite must be an object with 'label' and numeric 'mass'")
        if not isinstance(diag.get("radius_km"), (int, float)) or diag.get("radius_km") <= 0:
            err(rel, f"{path}.radius_km must be a positive number")
    elif scene == "magnetic-field":
        if diag.get("source") not in MAGNETIC_SOURCES:
            err(rel, f"{path}.source must be one of {sorted(MAGNETIC_SOURCES)}")
        if diag.get("current_direction") not in CURRENT_DIRECTIONS:
            err(rel, f"{path}.current_direction must be one of {sorted(CURRENT_DIRECTIONS)}")
    elif scene == "fleming-rule":
        rule = diag.get("rule")
        if rule not in FLEMING_RULES:
            err(rel, f"{path}.rule must be one of {sorted(FLEMING_RULES)}")
        if diag.get("field_direction") not in AXIS_VALUES:
            err(rel, f"{path}.field_direction must be one of {sorted(AXIS_VALUES)}")
        if rule == "left":
            if diag.get("current_direction") not in AXIS_VALUES:
                err(rel, f"{path}.current_direction must be one of {sorted(AXIS_VALUES)} for rule=left")
        elif rule == "right":
            if diag.get("motion_direction") not in AXIS_VALUES and diag.get("current_direction") not in AXIS_VALUES:
                err(rel, f"{path} needs 'motion_direction' (preferred) or 'current_direction' in {sorted(AXIS_VALUES)} for rule=right")
    elif scene == "em-induction":
        if diag.get("motion") not in INDUCTION_MOTIONS:
            err(rel, f"{path}.motion must be one of {sorted(INDUCTION_MOTIONS)}")
        if diag.get("magnet_pole") not in INDUCTION_POLES:
            err(rel, f"{path}.magnet_pole must be one of {sorted(INDUCTION_POLES)}")
    elif scene == "dispersion-prism":
        pass  # no required params beyond scene/caption
    elif scene == "longitudinal-wave":
        if not isinstance(diag.get("frequency"), (int, float)) or diag.get("frequency") <= 0:
            err(rel, f"{path}.frequency must be a positive number")
        if "amplitude" in diag and diag.get("amplitude") not in AMPLITUDE_VALUES:
            err(rel, f"{path}.amplitude, if present, must be one of {sorted(AMPLITUDE_VALUES)}")

    pred = diag.get("prediction")
    if pred is not None:
        if not isinstance(pred, dict) or not pred.get("question"):
            err(rel, f"{path}.prediction needs a non-empty 'question'")
        else:
            choices = pred.get("choices")
            if not isinstance(choices, list) or not choices:
                err(rel, f"{path}.prediction.choices must be a non-empty list")
            answer = pred.get("answer")
            if not isinstance(answer, int) or not isinstance(choices, list) or not (0 <= answer < len(choices)):
                err(rel, f"{path}.prediction.answer must be a valid index into 'choices'")

    manip = diag.get("manipulate")
    if manip is not None:
        if not isinstance(manip, dict) or not manip.get("param"):
            err(rel, f"{path}.manipulate needs a non-empty 'param'")
        elif not isinstance(manip.get("options"), list) or not manip.get("options"):
            err(rel, f"{path}.manipulate.options must be a non-empty list")

    refl = diag.get("reflection")
    if refl is not None and (not isinstance(refl, dict) or not refl.get("prompt")):
        err(rel, f"{path}.reflection needs a non-empty 'prompt'")

    poster = diag.get("poster")
    if poster is not None:
        _validate_physics_diagram(poster, f"{path}.poster", rel)


def validate_sections(d, rel):
    """Optional 'illustration' (a hero image) + 'sections' (the born-visual interleaved
    layout: each block = a short body + optional image/animation + optional recap). Both
    are additive — theory/engineering lessons may use a monolithic 'explanation' instead."""
    ill = d.get("illustration")
    if ill is not None and (not isinstance(ill, dict) or not ill.get("asset") or not ill.get("alt")):
        err(rel, "illustration, if present, needs non-empty 'asset' and 'alt'")
    secs = d.get("sections")
    if secs is None:
        return
    if not isinstance(secs, list) or not secs:
        err(rel, "sections, if present, must be a non-empty list of {body, image?, animation?, recap?}")
        return
    for i, s in enumerate(secs):
        if not isinstance(s, dict) or not s.get("body"):
            err(rel, f"sections[{i}] needs a non-empty 'body'")
            continue
        img = s.get("image")
        if img is not None and (not isinstance(img, dict) or not img.get("asset") or not img.get("alt")):
            err(rel, f"sections[{i}].image needs non-empty 'asset' and 'alt'")
        an = s.get("animation")
        if an is not None and (not isinstance(an, dict) or an.get("type") not in {"sequence", "cycle", "vector-space"}):
            err(rel, f"sections[{i}].animation.type must be one of sequence|cycle|vector-space")


def main():
    if not ROOT.exists():
        print(f"No content yet at {ROOT}. Curate a topic first.")
        return 0

    files = sorted(ROOT.glob("*/*.json"))
    # Also discover phase-end numericals + test banks stored one level deeper.
    files += sorted(ROOT.glob("*/_numericals/*.json"))
    files += sorted(ROOT.glob("*/_test/*.json"))
    if not files:
        print("No topic JSON found under content/roadmaps/<roadmap>/.")
        return 0

    # First pass: load + per-file checks, build slug index per roadmap.
    by_roadmap = {}
    docs = {}
    for path in files:
        rel = path.relative_to(ROOT.parent)
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(rel, f"invalid JSON: {e}")
            continue
        except UnicodeDecodeError as e:
            err(rel, f"not valid UTF-8 (wrong encoding, e.g. a stray temp/dump file?): {e}")
            continue
        docs[path] = d

        for k in ("slug", "title", "roadmap", "kind", "tier"):
            req(d, k, rel, str)
        if d.get("slug") and not SLUG.match(d["slug"]):
            err(rel, f"slug '{d['slug']}' is not kebab-case")
        if d.get("slug") and d["slug"] != path.stem:
            err(rel, f"slug '{d['slug']}' != filename '{path.stem}'")
        if d.get("kind") not in KIND:
            err(rel, f"kind must be one of {KIND}")
        if d.get("tier") not in TIER:
            err(rel, f"tier must be one of {TIER}")
        if d.get("roadmap") and d["roadmap"] != path.parent.name and path.parent.name not in ("_numericals", "_test"):
            err(rel, f"roadmap '{d['roadmap']}' != folder '{path.parent.name}'")

        m = d.get("metadata")
        if not isinstance(m, dict):
            err(rel, "missing 'metadata' object")
        else:
            if m.get("difficulty") not in DIFF:
                err(rel, f"metadata.difficulty must be one of {DIFF}")
            if m.get("interview_frequency") not in FREQ:
                err(rel, f"metadata.interview_frequency must be one of {FREQ}")
            if not isinstance(m.get("importance"), int) or not (1 <= m.get("importance", 0) <= 10):
                err(rel, "metadata.importance must be int 1-10")
            for edge in ("prerequisites", "unlocks"):
                if not isinstance(m.get(edge), list):
                    err(rel, f"metadata.{edge} must be a list of slugs")

        # Glossary validation (optional, all kinds)
        glos = d.get("glossary")
        if glos is not None:
            if not isinstance(glos, list):
                err(rel, "glossary must be a list")
            else:
                seen_terms = set()
                prose_text = extract_prose(d)
                for i, entry in enumerate(glos):
                    if not isinstance(entry, dict) or not entry.get("term") or not entry.get("definition"):
                        err(rel, f"glossary[{i}] must be an object with non-empty 'term' and 'definition' strings")
                        continue
                    term = entry["term"]
                    if not isinstance(term, str) or not isinstance(entry["definition"], str):
                        err(rel, f"glossary[{i}] 'term' and 'definition' must be strings")
                        continue
                    if "example" in entry and not isinstance(entry["example"], str):
                        err(rel, f"glossary[{i}] 'example' if present must be a string")
                        
                    t_lower = term.lower()
                    if t_lower in seen_terms:
                        err(rel, f"duplicate term in glossary: {term!r}")
                    seen_terms.add(t_lower)
                    
                    escaped_term = re.escape(term)
                    if not re.search(r'\b' + escaped_term + r'\b', prose_text, re.IGNORECASE):
                        warn(rel, f"glossary term {term!r} does not appear as a whole word in the lesson's prose fields")

        # Aptitude is its OWN thin lesson shape (kind: "aptitude"): intuition + rule + trick + recall.
        # None of the python/sql fields (overview, *_walkthrough, understanding_checks, practice_tasks)
        # apply — branch entirely and skip them. See content/PROMPT-aptitude.md.
        if d.get("kind") == "aptitude":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition' one-liner)")
            fm = d.get("formula")
            if not isinstance(fm, dict) or not fm.get("statement"):
                err(rel, "formula is required (object with a non-empty 'statement')")
            # worked_example REQUIRED: 1-2 representative problems solved step-by-step with the
            # method, so a learner can actually reach the oa_questions. Bridges formula -> OA.
            we = d.get("worked_example")
            if not isinstance(we, list) or not we:
                err(rel, "worked_example is required: a non-empty list of {problem, steps[], answer}")
            else:
                for i, w in enumerate(we):
                    if not isinstance(w, dict) or not w.get("problem") or not w.get("answer") or not isinstance(w.get("steps"), list) or not w.get("steps"):
                        err(rel, f"worked_example[{i}] needs 'problem', a non-empty 'steps' list, and 'answer'")
            sc = d.get("shortcuts")
            if not isinstance(sc, list) or not sc:
                err(rel, "shortcuts is required: a non-empty list of trick cards")
            else:
                for i, s in enumerate(sc):
                    if not isinstance(s, dict) or not s.get("title") or not s.get("trick"):
                        err(rel, f"shortcuts[{i}] needs non-empty 'title' and 'trick'")
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 OA-style items")
            else:
                for i, q in enumerate(oq):
                    if not isinstance(q, dict) or not q.get("question") or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs both 'question' and 'answer'")
            # hook + pattern_discovery are OPTIONAL; validate shape if present, enforce THE LAW.
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            pd = d.get("pattern_discovery")
            if pd is not None:
                cases = pd.get("cases") if isinstance(pd, dict) else None
                if not isinstance(pd, dict) or not isinstance(cases, list) or not cases or not pd.get("rule"):
                    err(rel, "pattern_discovery, if present, needs a non-empty 'cases' list and a 'rule'")
                elif not all(isinstance(c, str) and c.strip() for c in cases):
                    err(rel, "pattern_discovery.cases must be a list of non-empty observation STRINGS (not objects)")
                else:
                    keys = list(d.keys())
                    if "formula" in keys and keys.index("pattern_discovery") > keys.index("formula"):
                        warn(rel, "THE LAW: pattern_discovery should come BEFORE formula (discovery first)")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

        # Theory (Core CS: OS/DBMS/Networks, System Design) is a no-runtime concept
        # lesson (kind: "theory"): intuition + an EXPLANATION + recall. No code/formula/method.
        # See content/PROMPT-coreCS.md.
        if d.get("kind") == "theory":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition')")
            if not d.get("sections") and (not isinstance(d.get("explanation"), str) or not d.get("explanation").strip()):
                err(rel, "explanation OR sections is required (a non-empty explanation string, or a born-visual sections list)")
            validate_sections(d, rel)
            kp = d.get("key_points")
            if kp is not None:
                if not isinstance(kp, list) or not all(isinstance(p, dict) and p.get("title") and p.get("detail") for p in kp):
                    err(rel, "key_points, if present, must be a list of {title, detail} objects")
            # animation (optional, PROCESS concepts only): actors + directed steps so a
            # generic SVG renderer can animate the process. `term` per step is optional.
            # animation supports the box-flow types (sequence|cycle) OR vector-space
            # (the embeddings/RAG geometry — clusters + a query landing near one + top-k).
            an = d.get("animation")
            if an is not None:
                atype = an.get("type") if isinstance(an, dict) else None
                if atype not in {"sequence", "cycle", "vector-space"}:
                    err(rel, "animation.type must be one of sequence|cycle|vector-space")
                elif atype == "vector-space":
                    clusters = an.get("clusters")
                    labels = {c.get("label") for c in clusters} if isinstance(clusters, list) else set()
                    if not isinstance(clusters, list) or len(clusters) < 2 or not all(isinstance(c, dict) and c.get("label") for c in clusters):
                        err(rel, "vector-space animation needs 'clusters': a list of >=2 {label, color?}")
                    q = an.get("query")
                    if not isinstance(q, dict) or not q.get("label") or q.get("near") not in labels:
                        err(rel, "vector-space animation needs 'query': {label, near} where 'near' is a cluster label")
                    if not isinstance(an.get("k"), int) or an.get("k") < 1:
                        err(rel, "vector-space animation needs integer 'k' >= 1")
                else:
                    actors = an.get("actors")
                    ids = {a.get("id") for a in actors} if isinstance(actors, list) else set()
                    if not isinstance(actors, list) or len(actors) < 2 or not all(isinstance(a, dict) and a.get("id") and a.get("label") for a in actors):
                        err(rel, "animation.actors must be a list of >=2 {id, label}")
                    steps = an.get("steps")
                    if not isinstance(steps, list) or not steps or not all(
                        isinstance(s, dict) and s.get("from") in ids and s.get("to") in ids and s.get("label") for s in steps
                    ):
                        err(rel, "animation.steps must be a non-empty list of {from, to, label} referencing actor ids")
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 interview-style items")
            else:
                for i, q in enumerate(oq):
                    if not isinstance(q, dict) or not q.get("question") or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs both 'question' and 'answer'")
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

        # Engineering (AI Engineering: LLMs/RAG/Agents, applied backend) is theory + REAL CODE
        # (kind: "engineering"): same teach-from-scratch depth as theory, PLUS required
        # code_snippets (illustrative, not Pyodide-runnable — these call an LLM/network) and an
        # optional process animation (the RAG pipeline / agent loop is a `sequence`).
        # See content/PROMPT-engineering.md.
        if d.get("kind") == "engineering":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition')")
            if not d.get("sections") and (not isinstance(d.get("explanation"), str) or not d.get("explanation").strip()):
                err(rel, "explanation OR sections is required (a non-empty explanation string, or a born-visual sections list)")
            validate_sections(d, rel)
            # code_snippets REQUIRED: this is what separates engineering from theory. Real,
            # readable code a learner can map to the explanation. Not executed in-browser.
            cs = d.get("code_snippets")
            if not isinstance(cs, list) or not cs:
                err(rel, "code_snippets is required: a non-empty list of {title, language, code, explanation}")
            else:
                for i, c in enumerate(cs):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("code") or not c.get("explanation"):
                        err(rel, f"code_snippets[{i}] needs non-empty 'title', 'code', and 'explanation'")
                    elif not isinstance(c.get("language"), str) or not c.get("language"):
                        err(rel, f"code_snippets[{i}] needs a 'language' string (e.g. python, bash, json)")
            kp = d.get("key_points")
            if kp is not None:
                if not isinstance(kp, list) or not all(isinstance(p, dict) and p.get("title") and p.get("detail") for p in kp):
                    err(rel, "key_points, if present, must be a list of {title, detail} objects")
            # animation supports the box-flow types (sequence|cycle) OR vector-space
            # (the embeddings/RAG geometry — clusters + a query landing near one + top-k).
            an = d.get("animation")
            if an is not None:
                atype = an.get("type") if isinstance(an, dict) else None
                if atype not in {"sequence", "cycle", "vector-space"}:
                    err(rel, "animation.type must be one of sequence|cycle|vector-space")
                elif atype == "vector-space":
                    clusters = an.get("clusters")
                    labels = {c.get("label") for c in clusters} if isinstance(clusters, list) else set()
                    if not isinstance(clusters, list) or len(clusters) < 2 or not all(isinstance(c, dict) and c.get("label") for c in clusters):
                        err(rel, "vector-space animation needs 'clusters': a list of >=2 {label, color?}")
                    q = an.get("query")
                    if not isinstance(q, dict) or not q.get("label") or q.get("near") not in labels:
                        err(rel, "vector-space animation needs 'query': {label, near} where 'near' is a cluster label")
                    if not isinstance(an.get("k"), int) or an.get("k") < 1:
                        err(rel, "vector-space animation needs integer 'k' >= 1")
                else:
                    actors = an.get("actors")
                    ids = {a.get("id") for a in actors} if isinstance(actors, list) else set()
                    if not isinstance(actors, list) or len(actors) < 2 or not all(isinstance(a, dict) and a.get("id") and a.get("label") for a in actors):
                        err(rel, "animation.actors must be a list of >=2 {id, label}")
                    steps = an.get("steps")
                    if not isinstance(steps, list) or not steps or not all(
                        isinstance(s, dict) and s.get("from") in ids and s.get("to") in ids and s.get("label") for s in steps
                    ):
                        err(rel, "animation.steps must be a non-empty list of {from, to, label} referencing actor ids")
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 interview-style items")
            else:
                for i, q in enumerate(oq):
                    if not isinstance(q, dict) or not q.get("question") or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs both 'question' and 'answer'")
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

        # DSA (Algorithms Visualized) — computational-thinking lesson (kind: "dsa"). Mixes concept +
        # execution-trace nodes; the FIVE questions drive the fields. `viz` (a generator key registered
        # in frontend/src/dsa/registry.js) is present only on trace nodes. See docs/dsa-architecture.md.
        if d.get("kind") == "dsa":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition')")
            wie = d.get("why_it_exists")
            if not isinstance(wie, dict) or not wie.get("problem") or not wie.get("better_idea"):
                err(rel, "why_it_exists is required: object with 'problem' and 'better_idea' (naive_solution optional)")
            if not d.get("sections") and (not isinstance(d.get("explanation"), str) or not d.get("explanation").strip()):
                err(rel, "explanation OR sections is required (the teaching body)")
            validate_sections(d, rel)
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 interview-style items")
            else:
                for i, q in enumerate(oq):
                    if not isinstance(q, dict) or not q.get("question") or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs both 'question' and 'answer'")
            # optional five-questions enrichment — validate shape if present
            for fld in ("failure_signals", "interesting_facts", "related"):
                v = d.get(fld)
                if v is not None and (not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v)):
                    err(rel, f"{fld}, if present, must be a list of non-empty strings")
            wn = d.get("when_not_to_use")
            if wn is not None and (not isinstance(wn, list) or not all(isinstance(x, dict) and x.get("scenario") and x.get("reason") for x in wn)):
                err(rel, "when_not_to_use, if present, must be a list of {scenario, reason}")
            ee = d.get("engineering_examples")
            if ee is not None and (not isinstance(ee, list) or not all(isinstance(x, dict) and x.get("title") and x.get("why_this_algorithm") for x in ee)):
                err(rel, "engineering_examples, if present, must be a list of {title, why_this_algorithm, problem?}")
            pr = d.get("practice")
            if pr is not None and (not isinstance(pr, list) or not all(isinstance(x, dict) and x.get("title") and x.get("url") for x in pr)):
                err(rel, "practice, if present, must be a list of {title, url, difficulty?, why?}")
            pat = d.get("pattern")
            if pat is not None and (not isinstance(pat, dict) or not pat.get("name")):
                err(rel, "pattern, if present, needs a non-empty 'name'")
            kp = d.get("key_points")
            if kp is not None and (not isinstance(kp, list) or not all(isinstance(p, dict) and p.get("title") and p.get("detail") for p in kp)):
                err(rel, "key_points, if present, must be a list of {title, detail}")
            viz = d.get("viz")
            if viz is not None and (not isinstance(viz, dict) or not viz.get("generator")):
                err(rel, "viz, if present, needs a 'generator' (a key registered in frontend/src/dsa/registry.js)")
            if isinstance(viz, dict):
                # explain-this-frame needs the lesson's repeated decision — required on viz lessons
                if not (isinstance(mm, dict) and mm.get("repeated_decision")):
                    err(rel, "viz lessons require mental_model.repeated_decision (powers explain-this-frame)")
                preds = viz.get("predictions")
                if preds is not None:
                    if not isinstance(preds, list) or not preds:
                        err(rel, "viz.predictions, if present, must be a non-empty list of checkpoints")
                    else:
                        for i, p in enumerate(preds):
                            if not isinstance(p, dict):
                                err(rel, f"viz.predictions[{i}] must be an object"); continue
                            if not p.get("prompt"):
                                err(rel, f"viz.predictions[{i}] needs a non-empty 'prompt'")
                            if not p.get("at_op") and not p.get("at_step"):
                                err(rel, f"viz.predictions[{i}] must anchor via 'at_op' and/or 'at_step'")
                            occ = p.get("occurrence", "first")
                            if occ not in ("first", "last") and not (isinstance(occ, int) and occ >= 1):
                                err(rel, f"viz.predictions[{i}].occurrence must be 'first', 'last', or a 1-based integer")
                            lvl = p.get("level", "medium")
                            if lvl not in PREDICTION_LEVELS:
                                err(rel, f"viz.predictions[{i}].level must be one of {sorted(PREDICTION_LEVELS)}")
                            dv = str(p.get("derive") or "")
                            name = dv.split("(")[0].strip()
                            if DERIVE_NAMES and name not in DERIVE_NAMES:
                                err(rel, f"viz.predictions[{i}].derive '{dv}' is not a registered derive fn in frontend/src/dsa/predict.js ({sorted(DERIVE_NAMES)})")
                vsteps = viz.get("steps")
                if vsteps is not None:
                    if not isinstance(vsteps, list) or not vsteps:
                        err(rel, "viz.steps, if present, must be a non-empty list of {id, label}")
                    else:
                        for i, s in enumerate(vsteps):
                            if not isinstance(s, dict) or not s.get("id") or not s.get("label"):
                                err(rel, f"viz.steps[{i}] needs non-empty 'id' and 'label'")
                # Code panel (M2 / D7, OPTIONAL). Schema:
                #   viz.code = { "python": { "src": "<multiline string>", "lineMap": { "<step_id>": [1,2], ... } }, "java": {...}, ... }
                # `lineMap` keys are canonical step_ids (must be one of viz.steps[].id when steps is
                # authored); values are 1-based line numbers into that language's `src`. Not required.
                vcode = viz.get("code")
                if vcode is not None:
                    if not isinstance(vcode, dict) or not vcode:
                        err(rel, "viz.code, if present, must be a non-empty object of {lang: {src, lineMap}}")
                    else:
                        step_ids = None
                        if isinstance(vsteps, list) and vsteps:
                            step_ids = {s.get("id") for s in vsteps if isinstance(s, dict) and s.get("id")}
                        for lang, entry in vcode.items():
                            if not isinstance(entry, dict) or not isinstance(entry.get("src"), str) or not entry.get("src").strip():
                                err(rel, f"viz.code['{lang}'] needs a non-empty string 'src'")
                                continue
                            line_map = entry.get("lineMap")
                            if not isinstance(line_map, dict):
                                err(rel, f"viz.code['{lang}'] needs a dict 'lineMap'")
                                continue
                            n_lines = len(entry["src"].split("\n"))
                            for step_id, line_nos in line_map.items():
                                if step_ids is not None and step_id not in step_ids:
                                    err(rel, f"viz.code['{lang}'].lineMap key '{step_id}' is not one of viz.steps[].id")
                                if not isinstance(line_nos, list) or not line_nos or not all(
                                    isinstance(n, int) and 1 <= n <= n_lines for n in line_nos
                                ):
                                    err(rel, f"viz.code['{lang}'].lineMap['{step_id}'] must be a list of ints in [1, {n_lines}]")
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

        # Reasoning (Logical Reasoning + Verbal) is a method-based lesson (kind: "reasoning"):
        # intuition + an ordered METHOD + one WORKED EXAMPLE. No formula, no discovery.
        # See content/PROMPT-reasoning.md.
        if d.get("kind") == "reasoning":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition')")
            method = d.get("method")
            if not isinstance(method, list) or len(method) < 2 or not all(isinstance(s, str) and s for s in method):
                err(rel, "method is required: an ordered list of >=2 non-empty step strings")
            we = d.get("worked_example")
            if (not isinstance(we, dict) or not we.get("problem") or not we.get("answer")
                    or not isinstance(we.get("steps"), list) or not we.get("steps")):
                err(rel, "worked_example is required: object with 'problem', non-empty 'steps' list, and 'answer'")
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 OA-style items")
            else:
                for i, q in enumerate(oq):
                    if not isinstance(q, dict) or not q.get("question") or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs both 'question' and 'answer'")
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

        # Physics (NCERT School) — conceptual + numerical lesson (kind: "physics"): teach-from-
        # scratch explanation in Hinglish + English terms, EXACTLY 2 unrelated worked examples with
        # numericals, optional structured diagrams (ray/circuit/graph/free-body/image).
        # See content/PROMPT-physics.md.
        if d.get("kind") == "physics":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition')")
            if isinstance(mm, dict) and not mm.get("description"):
                warn(rel, "mental_model.description is strongly recommended for physics lessons")
            if not d.get("sections") and (not isinstance(d.get("explanation"), str) or not d.get("explanation").strip()):
                err(rel, "explanation OR sections is required (the teach-from-scratch body)")
            validate_sections(d, rel)
            # worked_example: EXACTLY 2 unrelated examples, each with problem + steps + answer.
            we = d.get("worked_example")
            if not isinstance(we, list) or len(we) != 2:
                err(rel, "worked_example must be a list of EXACTLY 2 items (two unrelated contexts)")
            else:
                for i, w in enumerate(we):
                    if not isinstance(w, dict):
                        err(rel, f"worked_example[{i}] must be an object"); continue
                    if not w.get("problem"):
                        err(rel, f"worked_example[{i}] needs a non-empty 'problem'")
                    if not isinstance(w.get("steps"), list) or not w.get("steps"):
                        err(rel, f"worked_example[{i}] needs a non-empty 'steps' list")
                    else:
                        for j, st in enumerate(w["steps"]):
                            if not isinstance(st, dict) or not st.get("narration"):
                                err(rel, f"worked_example[{i}].steps[{j}] needs a non-empty 'narration'")
                    if not w.get("answer"):
                        err(rel, f"worked_example[{i}] needs a non-empty 'answer'")
                    # per-example diagram (optional; diagram3d and diagram are mutually optional)
                    wed = w.get("diagram")
                    if wed is not None:
                        _validate_physics_diagram(wed, f"worked_example[{i}].diagram", rel)
                    wed3 = w.get("diagram3d")
                    if wed3 is not None:
                        _validate_diagram3d(wed3, f"worked_example[{i}].diagram3d", rel)
            # top-level diagram (optional; diagram3d and diagram are mutually optional)
            diag = d.get("diagram")
            if diag is not None:
                _validate_physics_diagram(diag, "diagram", rel)
            diag3d = d.get("diagram3d")
            if diag3d is not None:
                _validate_diagram3d(diag3d, "diagram3d", rel)
            # animation (optional)
            an = d.get("animation")
            if an is not None:
                atype = an.get("type") if isinstance(an, dict) else None
                if atype not in {"sequence", "cycle"}:
                    err(rel, "animation.type must be one of sequence|cycle for physics")
            kp = d.get("key_points")
            if kp is not None:
                if not isinstance(kp, list) or not all(isinstance(p, dict) and p.get("title") and p.get("detail") for p in kp):
                    err(rel, "key_points, if present, must be a list of {title, detail} objects")
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 board/school-exam items")
            else:
                for i, q in enumerate(oq):
                    q_text = q.get("question") or q.get("q") if isinstance(q, dict) else None
                    if not isinstance(q, dict) or not q_text or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs 'question' (or 'q') and 'answer'")
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

        # Numericals (phase-end practice sets for physics). kind: "numericals".
        # Shape: { phase, roadmap, kind, problems: [{prompt, given[], solution_steps[], answer, ...}] }
        if d.get("kind") == "numericals":
            if not d.get("phase"):
                err(rel, "phase is required for numericals")
            probs = d.get("problems")
            if not isinstance(probs, list) or not probs:
                err(rel, "problems must be a non-empty list")
            else:
                for i, p in enumerate(probs):
                    if not isinstance(p, dict):
                        err(rel, f"problems[{i}] must be an object"); continue
                    if not p.get("prompt"):
                        err(rel, f"problems[{i}] needs a non-empty 'prompt'")
                    if not isinstance(p.get("solution_steps"), list) or not p.get("solution_steps"):
                        err(rel, f"problems[{i}] needs a non-empty 'solution_steps' list")
                    else:
                        for j, st in enumerate(p["solution_steps"]):
                            if not isinstance(st, dict) or not st.get("narration"):
                                err(rel, f"problems[{i}].solution_steps[{j}] needs 'narration'")
                    if not p.get("answer"):
                        err(rel, f"problems[{i}] needs a non-empty 'answer'")
                    pd_diag = p.get("problem_diagram")
                    if pd_diag is not None:
                        _validate_physics_diagram(pd_diag, f"problems[{i}].problem_diagram", rel)
                    pd_diag3d = p.get("problem_diagram3d")
                    if pd_diag3d is not None:
                        _validate_diagram3d(pd_diag3d, f"problems[{i}].problem_diagram3d", rel)
                    sd_diag = p.get("solution_diagram")
                    if sd_diag is not None:
                        _validate_physics_diagram(sd_diag, f"problems[{i}].solution_diagram", rel)
                    sd_diag3d = p.get("solution_diagram3d")
                    if sd_diag3d is not None:
                        _validate_diagram3d(sd_diag3d, f"problems[{i}].solution_diagram3d", rel)
            continue

        # Test-section question banks. kind: "test". content/PROMPT-tests.md,
        # docs/SPEC-test-runtime.md. Shape: { phase, roadmap, kind, questions: [...] }.
        if d.get("kind") == "test":
            if not d.get("phase"):
                err(rel, "phase is required for a test bank")
            qs = d.get("questions")
            if not isinstance(qs, list) or not qs:
                err(rel, "questions must be a non-empty list")
                continue

            seen_ids = set()
            trap_count = 0
            mcq_count = 0
            production_count = 0
            for i, q in enumerate(qs):
                if not isinstance(q, dict):
                    err(rel, f"questions[{i}] must be an object"); continue
                qid = q.get("id")
                if not qid or not isinstance(qid, str):
                    err(rel, f"questions[{i}] needs a non-empty 'id'")
                elif qid in seen_ids:
                    err(rel, f"questions[{i}].id '{qid}' is duplicated in this file")
                else:
                    seen_ids.add(qid)

                node = q.get("node")
                if not node or not isinstance(node, str):
                    err(rel, f"questions[{i}] needs a non-empty 'node'")
                elif d.get("roadmap") and not (ROOT / d["roadmap"] / f"{node}.json").exists():
                    err(rel, f"questions[{i}].node '{node}' does not resolve to a lesson in roadmap '{d['roadmap']}'")

                qtype = q.get("type")
                if qtype not in TEST_TYPES:
                    err(rel, f"questions[{i}].type must be one of {sorted(TEST_TYPES)}")

                if q.get("difficulty") not in DIFF:
                    err(rel, f"questions[{i}].difficulty must be one of {DIFF}")
                if not q.get("prompt"):
                    err(rel, f"questions[{i}] needs a non-empty 'prompt'")
                if not q.get("explain"):
                    err(rel, f"questions[{i}] needs a non-empty 'explain'")

                is_trap = q.get("trap", False)
                if is_trap:
                    trap_count += 1
                    if not q.get("trap_note"):
                        err(rel, f"questions[{i}] has trap=true but no 'trap_note'")
                if qtype == "mcq":
                    mcq_count += 1
                elif qtype in ("fillup", "numeric", "code-fix", "code-write", "query-write"):
                    production_count += 1

                # --- type-specific required fields ---
                if qtype == "fillup":
                    if not q.get("answer"):
                        err(rel, f"questions[{i}] (fillup) needs a non-empty 'answer'")
                elif qtype == "numeric":
                    if not isinstance(q.get("answer"), (int, float)):
                        err(rel, f"questions[{i}] (numeric) needs a numeric 'answer'")
                    if not isinstance(q.get("tolerance"), (int, float)) or q.get("tolerance") < 0:
                        err(rel, f"questions[{i}] (numeric) needs a non-negative numeric 'tolerance'")
                elif qtype == "code-output":
                    if not q.get("code"):
                        err(rel, f"questions[{i}] (code-output) needs non-empty 'code'")
                    if not q.get("answer"):
                        err(rel, f"questions[{i}] (code-output) needs a non-empty 'answer'")
                elif qtype in ("code-fix", "code-write"):
                    if not q.get("starter"):
                        err(rel, f"questions[{i}] ({qtype}) needs non-empty 'starter'")
                    if not q.get("asserts"):
                        err(rel, f"questions[{i}] ({qtype}) needs non-empty 'asserts'")
                    if not q.get("answer"):
                        err(rel, f"questions[{i}] ({qtype}) needs a non-empty 'answer'")
                elif qtype == "query-write":
                    if not q.get("schema_sql"):
                        err(rel, f"questions[{i}] (query-write) needs non-empty 'schema_sql'")
                    if not q.get("canonical_query"):
                        err(rel, f"questions[{i}] (query-write) needs non-empty 'canonical_query'")
                    if not isinstance(q.get("order_matters"), bool):
                        err(rel, f"questions[{i}] (query-write) needs boolean 'order_matters'")
                elif qtype == "mcq":
                    opts = q.get("options")
                    if not isinstance(opts, list) or len(opts) < 2:
                        err(rel, f"questions[{i}] (mcq) needs 'options': a list of >=2")
                        opts = None
                    ans = q.get("answer")
                    if not isinstance(ans, int) or (opts and not (0 <= ans < len(opts))):
                        err(rel, f"questions[{i}] (mcq) needs integer 'answer' as a valid index into 'options'")
                    miscs = q.get("misconceptions")
                    if not isinstance(miscs, list) or (opts and len(miscs) != len(opts)):
                        err(rel, f"questions[{i}] (mcq) needs 'misconceptions' with the SAME length as 'options'")

            # Authoring-quality guidance (PROMPT-tests.md ratios) — advisory, not fatal.
            n = len(qs) or 1
            if trap_count / n < 0.25:
                warn(rel, f"trap ratio {trap_count}/{n} is below the ~25% target")
            if mcq_count / n > 0.20:
                warn(rel, f"mcq ratio {mcq_count}/{n} exceeds the ~20% cap")
            if production_count / n < 0.60:
                warn(rel, f"production-format ratio {production_count}/{n} is below the ~60% target")
            continue

        ov = d.get("overview")
        if not isinstance(ov, dict) or not all(ov.get(k) for k in ("what", "why")):
            err(rel, "overview.what and overview.why are required")

        for k in ("why_learning_this", "common_mistakes", "recall_questions", "practice_tasks", "sources"):
            if not isinstance(d.get(k), list) or not d.get(k):
                err(rel, f"'{k}' must be a non-empty list")

        for i, s in enumerate(d.get("sources", []) or []):
            if not isinstance(s, str) or not s.startswith("http"):
                err(rel, f"sources[{i}] is not a URL: {s!r}")

        for i, rq in enumerate(d.get("recall_questions", []) or []):
            if not isinstance(rq, dict) or not rq.get("q") or not rq.get("answer"):
                err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")

        # Execution block branches on runtime: python -> code_walkthrough, sql -> query_walkthrough.
        runtime = d.get("runtime", "python")
        if runtime not in RUNTIMES:
            err(rel, f"runtime must be one of {RUNTIMES}")
        if runtime == "sql":
            qw = d.get("query_walkthrough")
            if not isinstance(qw, dict) or not qw.get("query"):
                err(rel, "query_walkthrough is required for runtime 'sql': an object with a non-empty 'query'")
            if d.get("code_walkthrough") is not None:
                err(rel, "code_walkthrough not allowed for runtime 'sql' — use query_walkthrough")
        elif runtime != "none":
            cw = d.get("code_walkthrough")
            if not isinstance(cw, dict) or not cw.get("code"):
                err(rel, "code_walkthrough is required: an object with a non-empty 'code' string")
            elif not cw.get("focus"):
                err(rel, "code_walkthrough.focus is required (the one state change to watch)")

        # challenge is OPTIONAL (Tier D) — but if present it must be well-formed.
        ch = d.get("challenge")
        if ch is not None and (not isinstance(ch, dict) or not all(ch.get(k) for k in ("title", "prompt"))):
            err(rel, "challenge, if present, needs non-empty 'title' and 'prompt'")

        # understanding_checks (Tier A) — REQUIRED: >=2 typed mental-model probes.
        uc = d.get("understanding_checks")
        if not isinstance(uc, list) or len(uc) < 2:
            err(rel, "understanding_checks is required: a list of >=2 mental-model probes")
        else:
            for i, c in enumerate(uc):
                if not isinstance(c, dict) or not all(c.get(k) for k in ("type", "question", "answer", "why")):
                    err(rel, f"understanding_checks[{i}] needs non-empty 'type', 'question', 'answer', and 'why'")
                elif c.get("type") not in CHECK_TYPES:
                    err(rel, f"understanding_checks[{i}].type must be one of {CHECK_TYPES}")

        am = d.get("aha_moment")
        if am is not None and (
            not isinstance(am, dict)
            or not all(am.get(k) for k in ("code", "prediction", "common_guess", "why"))
        ):
            err(rel, "aha_moment must have non-empty code, prediction, common_guess, and why")

        if d.get("roadmap"):
            by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))

    # Second pass: cross-reference prereq/unlock slugs within the same roadmap.
    for path, d in docs.items():
        rel = path.relative_to(ROOT.parent)
        known = by_roadmap.get(d.get("roadmap"), set())
        m = d.get("metadata") or {}
        for edge in ("prerequisites", "unlocks"):
            for slug in m.get(edge, []) or []:
                if slug not in known:
                    warn(rel, f"{edge} '{slug}' not curated yet in this roadmap")

    print(f"Checked {len(files)} topic file(s).\n")
    if warnings:
        print("Warnings (unresolved refs - fine while curating):")
        print("\n".join(warnings), "\n")
    if errors:
        print("Errors:")
        print("\n".join(errors))
        print(f"\n{len(errors)} error(s). Fix or re-prompt Gemini.")
        return 1
    print("All content valid. [OK]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
