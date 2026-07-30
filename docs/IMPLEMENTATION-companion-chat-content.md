# Implementation Plan — Companion: read AI chat content, split one chat into many topics

**Status:** ready for implementation. **Owner of this doc:** Claude. **Implementer:** Sonnet.
**Depends on:** the `cloud` consent tier (already shipped), `classify_session`'s dormant
`content` parameter (already shipped), the `extra="forbid"` payload invariant (already shipped).

---

## 0. Read this before writing code: the extension currently lies

The popup consent screen says, verbatim, today, in production:

> *"Your chats are analyzed by Google's Gemini to tell learning from getting answers…"*

`extension/src/content/llm_metadata.ts` reads `document.title` and **nothing else**. There is no
code path in the shipped extension that reads a single message from a chat. Meanwhile
`docs/IMPLEMENTATION-amo-submission.md` §1 instructs the privacy policy to state the opposite —
*"specifically **not** the text of AI chats"*.

So one of the two documents is going to be false whichever way this lands. That is the actual
reason to do this work now, and it is more urgent than the feature itself:

- The over-claim is in the **safe** direction for users (we collect less than we said), but it is
  still a false statement on a consent screen, and consent obtained by describing processing that
  does not happen is not meaningful consent.
- Shipping this feature makes the consent copy true. **Do not ship the feature without also
  making the privacy policy true** (§6) — that flips the falsehood to the unsafe direction, which
  is an AMO policy violation and a plausible add-on block.

**Hard gate:** §6 ships in the same release as §2–§4. Not the release after.

---

## 1. What this buys — and the trap to avoid

A single ChatGPT/Claude session routinely covers three unrelated things: a Postgres index question,
a React re-render bug, and a bit of resume wording. Today that whole session becomes **one**
`learning_event` with one `title_sample` (the chat's title, which reflects only the *first* topic —
all three surfaces title a conversation from its opening turns and rarely rename it). The
embedding step then maps the entire session to one node, so two of the three topics vanish and the
third gets credited with the full duration.

The trap: **reading a chat is not evidence of learning.** The whole product thesis is "track what
you remember, not what you complete", and an AI chat is the single most assistance-heavy surface
that exists. Content access must make attribution *sharper*, and must not make mastery *higher*.
Concretely: more content → more topics → more accurate node attribution and a better
`assistance_level`; it must never raise `trust_tier` above `T3_observed` or produce non-zero
mastery weight. If the implementation makes chat time look like study time, it has failed even if
every test passes.

---

## 2. Extension: extract turns (content scripts)

### 2.1 New module `extension/src/content/chat_extract.ts`

```ts
export interface ChatTurn { role: 'user' | 'assistant'; text: string }
export interface ChatExtractor { surface: string; extract(): ChatTurn[] }
```

One extractor per surface, selected by hostname exactly as `llm_metadata.ts` already does.

**Selectors, verified against the live DOM on the day of implementation — do not trust these
strings from this doc, re-check each one:**

| Surface | Turn container (as of 2026-07) | Role signal |
|---|---|---|
| ChatGPT | `[data-message-author-role]` | the attribute's value |
| Claude | `[data-testid="user-message"]`, `.font-claude-response` | which selector matched |
| Gemini | `user-query`, `model-response` (custom elements) | tag name |

All three ship obfuscated utility classes; the `data-*` and custom-element hooks above are the only
semi-stable handles. **Never select on a hashed class name** — it changes per deploy and will fail
silently.

### 2.2 Extraction is user-turn-weighted

Take **user turns in full** and **assistant turns truncated to the first 300 characters**. The
user's own words say what they were trying to learn; the assistant's reply is mostly the answer
being handed over, which is exactly the thing that must not be mistaken for learning. This also
cuts payload size by roughly an order of magnitude, since assistant turns dominate chat volume.

Caps, enforced in the content script before anything crosses a message boundary:
- `MAX_TURNS = 60` (keep the most recent — the tail is what the session was actually about)
- `MAX_TOTAL_CHARS = 12_000`, truncate from the oldest end
- Skip code blocks in assistant turns entirely (`pre` descendants) — high volume, low topic signal.

### 2.3 Virtualized lists will lose you turns

ChatGPT and Gemini both virtualize long conversations: turns scrolled far out of view are removed
from the DOM. Extraction sees only what is currently mounted. **This is acceptable and must be
documented in the module header, not worked around** — do not scroll the page programmatically to
force-mount history. That is user-visible interference with a page the user is reading, and it is
the kind of behaviour AMO reviewers treat as hostile.

### 2.4 Gate: `titles` and `nano` must reach zero of this code

```ts
if (await getConsentTier() !== 'cloud') return   // first line of the extractor entry point
```

Belt and braces, both required:
1. The tier check above, because the tier is the thing the user chose.
2. The existing `optional_host_permissions` gate, which already means no injection at all without
   the origin grant.

`nano` (on-device) explicitly **does not** send content anywhere. Its copy promises "nothing leaves
your machine", and there is no on-device path implemented — so for this release **`nano` behaves
exactly like `titles`** (metadata only). Say so in the popup copy or the promise breaks in the
other direction. See §7.

### 2.5 Transport

Extend the `SEGMENT_EMIT` message with an optional `content?: string` (the flattened turns, roles
prefixed `U:` / `A:`). In `service_worker.ts`, hold content **in the buffer only** — it must be
attached to the outgoing request and must never be written into `payload`.

---

## 3. Backend: one session → many topic events

This is the structural change. `sync_sessions` currently records exactly one `LearningEvent` per
session; it must be able to record N.

### 3.1 Transport field, not a payload field

`CompanionSessionPayload` has `model_config = ConfigDict(extra="forbid")` and no content field.
**Leave it that way** — that invariant is what guarantees raw chat text cannot reach the DB. Add
content as a sibling of `payload` on the request model instead:

```python
class CompanionSessionIn(BaseModel):
    ...
    content: Optional[str] = Field(None, max_length=16_000, exclude=True,
        description="Transport only. Consumed by the classifier and discarded; never persisted.")
```

Then in `sync_sessions`, before `record_event`, add `content` to the existing `_ai_field` scrub
loop's sibling logic — i.e. assert it never entered `payload`. Add a test that a request sending
`payload.content` is **rejected 422** by `extra="forbid"`, so a future refactor cannot quietly
relax it.

### 3.2 New service `segment_session_topics`

`app/services/topic_segmentation.py`. One Gemini call, structured output:

```json
{"topics": [
  {"label": "...", "share": 0.0-1.0, "study_type": "learning|answer_seeking|mixed",
   "assistance_level": "none|hint|llm_assisted|solution_seen", "quotes_removed": true}
]}
```

- `share` values must sum to ~1.0; renormalize server-side rather than trusting the model.
- **`label` is a short topic phrase the model writes itself, never a verbatim span from the chat.**
  Say this in the prompt explicitly. It is what keeps user text out of the DB when the label is
  later stored as `title_sample`.
- Cap at **5 topics per session**; merge the tail into the largest.
- Sessions under **5 minutes** skip segmentation entirely and take the existing single-event path —
  not worth a call, and short sessions are rarely multi-topic.

### 3.3 Attribution loop

For each returned topic: run it through the existing embedding shortlist + `classify_session`
ladder (`label` in place of `title_sample`), and record one `LearningEvent` with
`duration_min = round(session.duration_min * share)`.

Non-obvious consequences, each needing a test:

- **Rate limit.** `COMPANION_MAX_SESSIONS_PER_DAY = 50` counts `LearningEvent` rows. Fan-out to 5×
  turns that into an effective cap of 10 sessions/day. **Count sessions, not events** — add a
  `session_id`-derived dedupe, or count `distinct payload->>'session_id'`.
- **Idempotency.** `session_id` is documented as the dedupe key. N events now share one
  `session_id`; whatever enforces idempotency must key on `(session_id, topic_index)`.
- **Rounding.** Five topics at `share=0.19` on a 10-minute session each round to 2 min = 10. Fine.
  But `round()` on small shares yields 0-minute events; drop any topic whose rounded duration is 0
  rather than storing a zero-length event.

### 3.4 Trust tier is unchanged — assert it

Every event from this path stays `T3_observed` with zero mastery weight, exactly as the current
docstring promises ("without inflating mastery scores"). Add an explicit test asserting the tier
and weight for a content-derived event. This is the §1 trap, encoded.

---

## 4. Cost and latency

`sync_sessions` is already synchronous over an embedding call plus a classify call, per session, in
a request that can carry 20 sessions. Adding a segmentation call per session on top makes a
worst-case batch 20 × 3 sequential Gemini calls inside one HTTP request. **This will time out on
Render.**

Do one of these — implementer's call, but pick one and say which:
- **(a)** Cap content-bearing sessions to the first 3 per batch; the rest sync metadata-only and are
  re-segmented on a later tick. Simple, ships today.
- **(b)** Segment only sessions whose `sources` include an LLM origin — most sessions are YouTube or
  LeetCode and need none of this. **Do this regardless**, it is free.
- **(c)** Move segmentation off-request into a background task. Correct, larger.

(b) + (a) is the recommended combination for v1.

---

## 5. Telemetry — this feature is unfalsifiable without it

Emit a `companion_topic_segmentation` metric per call: session duration, topic count, whether the
model returned >1 topic, and the fallback reason if it failed. Without this there is no way to
answer "is multi-topic splitting actually happening, or is the model returning one topic every
time and we've added cost for nothing?" — which is the most likely failure mode, not an
edge case. Check it after a week of dogfooding before believing the feature works.

---

## 6. Privacy and AMO — ships in the same release, no exceptions

1. **Privacy policy rewrite.** Reverse the claim in `IMPLEMENTATION-amo-submission.md` §1. It must
   now say: on the *Smart tracking* tier only, the text of AI-chat conversations is sent to
   RetainHQ's server and to Google Gemini for topic classification, is **not stored** (only the
   model-written topic label is), and the other two tiers send no chat text at all.
2. **`data_collection_permissions`.** `browsingActivity` alone no longer covers this. Chat content
   is user-authored free text and will frequently contain personal information. Check Mozilla's
   current permitted values and expect to need `personallyIdentifyingInfo` in **`required`**, not
   `optional`, for the cloud tier. This changes the install-time consent screen Firefox shows.
   **Verify against Mozilla's live docs at implementation time; do not take this doc's word.**
3. **The Gemini billing gate binds harder now.** ~~`IMPLEMENTATION-amo-submission.md` §1 already flags
   that the free Gemini tier lets Google use submitted content and lets human reviewers see it.
   That was about page titles. It is now about the user's actual chats. **If `GEMINI_API_KEY` is
   not on a billed project, this feature must not ship.** Verify before merging, not before
   submitting.~~ **RESOLVED 2026-07-27 — owner confirmed the key is on a billed project.** Keep as a
   standing condition, not a closed item: if that project's billing ever lapses, the published
   privacy policy becomes false at that moment, silently and with no code change to signal it.
4. **Re-consent.** Bump the consent copy to `copy_version: 'v2'` and re-show the choice screen to
   anyone whose stored consent is v1. A v1 user consented to a description; the processing behind
   that description is materially changing. Cheap to do, and it is the difference between a defensible
   consent record and a retroactive one.
5. **AMO reviewer note** must say which tier reads content and that the other two do not.

---

## 7. The `nano` tier problem

The popup offers "On-device AI — same understanding, running entirely inside your browser". No
on-device path exists; `nano` today is a relabelled `titles` that also requests host permissions it
does not use.

Once `cloud` genuinely reads content, `nano` becomes the *only* tier whose copy is false. Pick one
in this release:

- **(a)** Change the copy to "Titles only, on-device AI coming when your browser supports it" — honest,
  keeps the option, five minutes of work. **Recommended.**
- **(b)** Remove the tier until Chrome's built-in Prompt API path is actually implemented. Cleanest,
  but Firefox has no equivalent API at all, so on a Firefox-first release this option may never
  return.
- **(c)** Implement it. Out of scope here.

Also: `nano` currently requests the LLM origin grant (`consent.ts` treats `cloud` and `nano`
identically) while having no code that uses it. Under (a), stop requesting origins for `nano`.

---

## 8. Definition of done

- [ ] `titles` and `nano` sessions carry no `content` field — asserted by test, not by inspection
- [ ] `payload.content` is rejected 422; `extra="forbid"` untouched
- [ ] A three-topic chat produces three `LearningEvent` rows with durations summing to the session
- [ ] All content-derived events are `T3_observed`, weight 0 — asserted
- [ ] Daily rate limit counts sessions, not fanned-out events
- [ ] Privacy policy and `data_collection_permissions` updated **in the same commit**
- [ ] `GEMINI_API_KEY` confirmed on a billed project
- [ ] `copy_version` bumped to v2 and v1 users re-prompted
- [ ] `nano` copy no longer claims capability that does not exist
- [ ] Docs: SYSTEM-OVERVIEW §changelog + a DECISIONS entry for the transport-not-payload choice

## 9. Report back

1. Which §4 option was implemented, and the measured p95 of `sync_sessions` afterwards.
2. Whether Mozilla required a data category beyond `browsingActivity`.
3. From §5 telemetry after one week: what fraction of LLM sessions actually returned >1 topic. If
   it is under ~20%, the feature is not earning its cost and the honest move is to say so.
