# Lesson images — RetainHQ theme + one-at-a-time DELEGATION PROMPT

> Workflow: images are generated **one by one** in ChatGPT (GPT Image 2) or Gemini (Nano Banana Pro),
> with the model keeping the session context so the SET stays consistent. Consistency comes from two
> things: (1) a **locked style preamble** pasted verbatim into every prompt, and (2) a **style anchor**
> image you generate ONCE and then reference on every later image. Paste this file in, then work one
> image at a time.

---

## THE RETAINHQ ILLUSTRATION THEME (the brand — every image obeys it)

Mood: **calm, precise, editorial — "modern technical textbook," not cartoon, not corporate clip-art.**
It should feel like a quiet, confident diagram in a well-designed CS book. (This is a starting theme —
Alok owns visual design and can tune the palette/feel; keep it locked once set so the catalog matches.)

### Locked STYLE PREAMBLE — paste this VERBATIM at the top of EVERY image prompt
```
RetainHQ illustration style: flat 2D vector diagram, transparent background, 4:3 aspect ratio.
Clean modern technical-textbook look — thin uniform slate (#475569) outlines, rounded corners,
generous whitespace, ONE clear focal idea, nothing busy. Accent palette, use only 2–3 per image:
cyan #0891B2, teal #0F766E, violet #7C3AED, amber #B45309; fills are light tints of those accents;
red #B91C1C ONLY for errors/warnings. Clean geometric sans-serif labels (Inter-like), sentence case,
minimal text, every label spelled exactly as specified. NO 3D, NO photorealism, NO heavy gradients,
NO drop shadows, NO glow, NO clip-art, NO hand-drawn doodle, NO isometric, NO background scenery.
Calm, precise, editorial.
```

### Visual vocabulary (draw these the SAME way every time — this is what makes the set cohere)
| Concept | Always drawn as |
|---|---|
| Document / source | An upright page glyph with a folded top-right corner, slate outline, faint text lines |
| Chunk | A rounded rectangle, one accent tint, optionally numbered |
| Vector / embedding | A small filled dot with a short arrow from the origin (a point in space) |
| Vector store / DB | A loose field of dots, or a slim cylinder; never a 3D barrel |
| LLM / model | A rounded "chip" rectangle in violet (#7C3AED), labeled |
| User / query | A cyan (#0891B2) circle or a speech bubble |
| Tool / function | A labeled rounded square with a small gear/wrench mark |
| Prompt | A bracketed/rounded text panel, slate outline |

Keep sizes and stroke weight consistent across images so two figures from different lessons look like
siblings.

---

## ONE-IMAGE-AT-A-TIME WORKFLOW

**Step 0 — generate the STYLE ANCHOR first (do this once for the whole catalog).**
Generate a single simple figure that exercises the theme — recommended: `chunking-strategies / overlap`
(a document sliced into 4 overlapping chunks). Tune until it looks right. **This image is now your
canonical look.** Save it; you'll attach it as a reference to every future generation.

**Step 1 — for each new image, prompt = PREAMBLE + "match the anchor" + the scene.**
In the same ChatGPT/Gemini session (or by attaching the anchor image), say:
> [paste STYLE PREAMBLE] — Match the style, palette, stroke weight, and label style of the attached
> reference image EXACTLY, so this belongs in the same set. Now draw: [the specific scene, using the
> visual vocabulary above].

**Step 2 — verify before accepting** (see checklist rules below). Regenerate if any item fails.

**Step 3 — name + upload** to the Supabase bucket at the exact path (below).

---

## WHAT GETS AN IMAGE (be stingy — many lessons get zero)
Only when a **static picture builds intuition prose can't**:
- ✅ a metaphor made concrete (RAG = open-book exam; embedding = GPS coordinate for meaning)
- ✅ a **structure** you'd whiteboard (B-tree, star schema, transformer block layers, chunk overlap)
- ✅ a **before/after or state** snapshot (delimited untrusted input in a prompt)

NOT for:
- ❌ a **process/flow** (RAG pipeline, handshake, agent loop, streaming) → that's the lesson's
  programmatic ANIMATION (`sequence`/`cycle`/`vector-space`), interactive + themeable. Don't duplicate it.
- ❌ the embed/retrieve **cluster geometry** specifically → that's the `vector-space` animation, not an image.
- ❌ prose, definitions, code, or decoration.

**1–2 images per lesson, max 3.**

---

## OUTPUT — one image spec at a time (not a batch)
For the image you're working on, return ONE JSON object:
```json
{
  "lesson_slug": "chunking-strategies",
  "roadmap": "ai-engineering",
  "visual_id": "overlap",
  "filename": "ai-engineering/chunking-strategies/overlap.png",
  "where": "beside the paragraph explaining chunk overlap",
  "generation_prompt": "<STYLE PREAMBLE> Match the attached reference exactly. Draw: a long horizontal document bar (slate page glyph, folded corner) sliced into FOUR equal rounded-rectangle chunks — chunk 1 cyan, chunk 2 teal, chunk 3 violet, chunk 4 amber. Adjacent chunks OVERLAP ~15% at their edges; show each overlap as a hatched band labeled 'overlap'. Labels 'Chunk 1'..'Chunk 4'.",
  "alt": "A document split into four overlapping chunks, the shared overlap regions highlighted",
  "verify_checklist": [
    "Looks like it belongs in the same set as the style anchor (palette, stroke, label style)",
    "Exactly 4 chunks, labeled Chunk 1–4, spelled correctly",
    "Adjacent chunks actually OVERLAP (shared band), not just touching or gapped",
    "Overlap band highlighted + labeled 'overlap'",
    "Transparent background; flat; no 3D/photoreal/gradient; no invented extra text"
  ]
}
```

## VERIFICATION (the point of one-by-one)
**99% character accuracy ≠ 99% conceptual accuracy** — a model can spell every label and still draw the
arrow backwards or the wrong count. Check each image against its `verify_checklist` AND "does it sit in
the same family as the anchor?" If any item fails, regenerate restating the failed item. The image
illustrates intuition only — it must not introduce a claim that isn't in the lesson.

## STORAGE (no DB migration — this is object storage, not Postgres)
- Supabase **public** bucket `lesson-images` (create once: Storage → New bucket → Public). Alembic is NOT involved.
- Upload each file at its `filename` path. Public URL:
  `https://<project-ref>.supabase.co/storage/v1/object/public/lesson-images/<filename>`
- The lesson JSON later references only `{ "asset": "<filename>", "alt": "<alt>" }`. Keep filenames EXACT.
