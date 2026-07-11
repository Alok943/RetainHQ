# Claude Code workflow for RetainHQ

How to run AI sessions on this repo so knowledge lands in files (cheap, permanent) instead of chats (expensive, disposable). Grounded in Anthropic's official guidance: [Best practices](https://code.claude.com/docs/en/best-practices), [Reduce token usage](https://code.claude.com/docs/en/costs#reduce-token-usage), [Large codebases](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start).

**The one constraint everything follows from:** the context window re-bills on every message and model quality degrades as it fills. Every rule below is either "keep context small" or "make knowledge survive the chat."

---

## 0. Start here — kicking off any task

1. Pick the workstream session from the table below (create it with that name if it doesn't exist; `/clear` it if it's stale).
2. First message pattern: **context files + specific task + verification target.** Example:
   > Read docs/SYSTEM-OVERVIEW.md §5 and docs/DECISIONS.md D-004. Then implement <specific thing> in <file/area>. Verify by <test/command/screenshot> before claiming done.
3. On finish, the routing rules in CLAUDE.md fire automatically (SYSTEM-OVERVIEW same-commit, decisions → DECISIONS.md, ideas → BACKLOG.md). You review the diff and commit; say "push" only when you want Vercel+Railway to deploy.

## 1. Sessions — one workstream, one session

Chats are disposable; these named workstreams are permanent. When a session gets long or stale, **start a fresh one with the same name** — the docs carry the context forward, not the chat.

| Session name | Owns |
|---|---|
| `backend-engine` | FastAPI, FSRS scheduler, grader/LLM, migrations, DB, Railway deploy |
| `frontend-ui` | React pages/components, design-bible work, dark mode, UX polish |
| `content-pipeline` | Lesson JSON, `validate.py`, `PROMPT-*.md` contracts, Antigravity critique |
| `dsa-viz` | Trace generators, `compile.js`, renderers, the Player |
| `school-b2b` | Physics 9-10, school pitch, Gorakhpur research |
| `growth-marketing` | SEO, launch, funnel, analytics, emails |
| `product-decisions` | Architecture/roadmap thinking; writes `DECISIONS.md` |
| `bugs` | Quick cross-cutting fixes; `/clear` between unrelated bugs |

Rules:
- **Never mix concerns.** A UI question mid-backend-session → new line in `BACKLOG.md` or ask it in `frontend-ui`.
- **Don't resume old long chats to "remind" Claude.** Resuming re-sends the whole history every message. Extract anything valuable into a doc, then abandon the chat.
- **Milestone framing:** a session works on one scoped task from SYSTEM-OVERVIEW §5 (plans), not "build RetainHQ."

## 2. Session start ritual

1. CLAUDE.md loads automatically (now lean — rules + routing).
2. Point Claude at the *specific* docs for the task: `Read docs/SYSTEM-OVERVIEW.md §X and docs/DECISIONS.md, then …`
3. Never say "remember what we discussed" — if it isn't in a file, it doesn't exist.

## 3. Session end ritual (before closing or when a task ships)

- Routing rules in CLAUDE.md fire: SYSTEM-OVERVIEW updated same commit, decision → `DECISIONS.md`, stray ideas → `BACKLOG.md`.
- If a research session produced reusable findings, write them to a `docs/` file (like `jd-research-run*.md`) — **one file per durable topic, not per chat**.

## 4. Research → plan → implement

- **Separate exploration from execution.** Use plan mode (Shift+Tab) for multi-file or unfamiliar work; skip it when you could describe the diff in one sentence.
- **Subagents for heavy reading.** "Use a subagent to investigate how X works" — the file-reading happens in a separate context and only a summary returns. Same for verbose ops (test runs, log digging).
- **Big features: spec first, fresh session second.** Have Claude interview you, write the spec to a doc, then implement in a clean session reading only the spec.
- **Adversarial review:** before calling something done, have a fresh subagent/`/code-review` check the diff — a fresh context isn't biased toward code it just wrote.

## 5. Token discipline (from Anthropic's cost docs)

- **`/clear` between unrelated tasks** — the single highest-ROI habit. `/rename` first so you can `/resume` later.
- **Two failed corrections → `/clear`** and re-prompt with what you learned. A clean session with a better prompt beats a long session full of failed attempts.
- **Specific prompts.** "Fix login" triggers a codebase scan; "users report login fails after session timeout — check token refresh in `src/auth/`, write a failing test first" doesn't.
- **Give a verification target** (test case, expected output, screenshot) so Claude closes its own loop instead of you being the checker.
- **Esc early** when direction is wrong; `/rewind` to checkpoints instead of arguing forward.
- **`/compact <focus>`** when you need continuity but the session is heavy; `/context` and `/usage` to see what's eating space.
- **CLI over MCP** where possible (`gh`, etc. — no per-tool schema cost). Disable unused MCP servers.
- **Model choice:** Sonnet for rubric/mechanical work (e.g. the lesson critic — see memory), stronger models for architecture.

## 6. CLAUDE.md hygiene

- CLAUDE.md is loaded before every message of every session — every line is a recurring tax. Keep it rules-only; for each line ask *"would removing this cause mistakes?"*
- No status, no history, no build log (that's what killed the old 450-line version — archived at `CLAUDE-ARCHIVE-2026-07.md`).
- Review it when Claude misbehaves: ignored rules usually mean the file is too long, not that the rule needs more emphasis.

## 7. Failure patterns to catch yourself in

| Pattern | Fix |
|---|---|
| Kitchen-sink session (UI → DB → SEO → pricing in one chat) | `/clear`; route to the right workstream |
| Correcting the same mistake 3+ times | `/clear` + better initial prompt |
| "Investigate X" with no scope → 200 files read | Scope it, or delegate to a subagent |
| Plausible code, unverified | Demand test output / screenshot as evidence |
| Old mega-chat as the source of truth | Extract to docs, abandon the chat |
