# RetainHQ — Walkthrough / Demo Guide

How to produce a short walkthrough of the **deployed** app for the first-users push.
Goal: in ~90 seconds, land the one idea — *"log something → it tests you immediately → it schedules the next review for you."* That "prove-the-loop-in-seconds" moment is the whole pitch.

> Primary format: a **recorded screen walkthrough** (Loom/MP4) you can drop in the landing page, a DM, or an onboarding email. An optional **in-app guided tour** is sketched at the end.

---

## 0. Decide the cut you need
| Cut | Length | Use |
|---|---|---|
| **Teaser GIF** (no audio) | 8–15s | Landing page hero, tweets, DMs. Just: log → baseline review → "next review in 6 days". |
| **Core walkthrough** ⭐ | 75–120s | The default. Voiceover + the full loop. Onboarding email, "How it works". |
| **Deep demo** | 3–5 min | For someone who asked "show me everything" — adds Vault, Roadmaps, Analytics. |

Make the **Core walkthrough** first; the GIF is a trim of it.

---

## 1. Tools
- **Recording:** Loom (fastest, gives a shareable link + trim), or OBS / ScreenStudio (nicer zoom/cursor, exports MP4) if you want polish.
- **GIF:** export the MP4 and convert (ScreenStudio exports GIF directly; or `ffmpeg`/ezgif).
- **Browser:** Chrome, **incognito** (clean state, no extensions, no autofill popups).
- **Captions:** auto-caption in Loom/CapCut — most people watch muted.

---

## 2. Pre-flight checklist (do this before hitting record)
The #1 mistake is recording an **empty app**. Set the stage:

- [ ] Use a **dedicated demo Google account** (not your founder/admin email — you don't want the Admin tab showing in a public demo).
- [ ] **Seed a little history** so screens aren't empty: log ~4–5 activities and complete a couple of reviews, so Home's "Recent Captures", the Vault, and a roadmap with some progress all look alive. (Vary the **Source Type** so the Vault badges and by-source look real.)
- [ ] Leave **one fresh topic unlogged** — you'll log it live as the hero moment.
- [ ] Browser zoom **100%**, window sized clean (~1440×900). Close other tabs.
- [ ] Pre-load the **deployed URL** and confirm Google login works end-to-end (cold start: if the backend is on a free tier that sleeps, hit it once first so there's no cold-start lag on camera).
- [ ] Dark mode: pick one and stick to it (the landing page is always-dark; the app follows the Profile toggle).
- [ ] Have your **voiceover lines** (below) on a second screen.

---

## 3. The script (Core walkthrough, ~90s)

Each scene = what you click + what you say. Keep the cursor deliberate; pause ~1s on each key screen.

**Scene 1 — The promise (0:00–0:10) · Landing page**
- *Screen:* the deployed landing page (`/`), scroll once so "The learning loop, automated" + the 4 steps flash by.
- *Say:* "Most study tools track what you *did*. RetainHQ tracks what you actually **remember** — and reviews it right before you'd forget."
- Click **Get Started** → Google login → land on Home.

**Scene 2 — Capture (0:10–0:30) · Log Activity**
- *Screen:* click **Log Activity**. Fill it live: Topic ("Dictionaries"), Source Type, a tight **Key Memory** ("Stores key–value pairs, mutable"), pick a Difficulty.
- *Say:* "Logging takes seconds. The one field that matters is the **Key Memory** — the single thing you want to keep."
- Click **Log & Schedule Review** → redirected to Home.

**Scene 3 — The aha: it tests you *now* (0:30–0:55) · Reviews**
- *Screen:* Home shows the topic **due now**. Click **Start Reviews**.
- *Say:* "Here's the part that's different — it doesn't wait. You get a **baseline recall right away**."
- Type an answer in the recall box (or hit "I don't know"), click **Reveal**, then rate **Easy/Good/Hard**.
- *Say:* "You commit to an answer *before* the reveal — real recall, not recognition. And based on how it went, it schedules the next review for you."

**Scene 4 — It schedules itself (0:55–1:10) · Home / Vault**
- *Screen:* back on Home, point at the next review timing; open the **Vault**, show the captured memory with its **source badge** and "next review in N days".
- *Say:* "Every topic lives in your Vault. The spacing widens as it sticks — so you stop relearning things you already know."

**Scene 5 — Close (1:10–1:25)**
- *Screen:* quick glance at Roadmaps or Analytics (optional), then back to the clean Home.
- *Say:* "Log it once, and RetainHQ handles the rest. It's free to start — link below."

---

## 4. Do / Don't
- **Do** show the *baseline review happening immediately* — that's the differentiator; don't skip it.
- **Do** keep one genuinely empty→filled action on camera (logging the live topic) so it feels real, not staged.
- **Don't** show the **Admin** dashboard, the funnel, or other users' emails — founder-only, not for a public demo.
- **Don't** narrate the UI ("now I click the blue button") — narrate the *value* ("it tests me before I forget").
- **Don't** record on a cold backend — warm it up first so nothing spins.
- Keep total length honest to the cut; trim dead air ruthlessly.

---

## 5. Distribution
- **Landing page:** embed the GIF in/near the hero, or the Loom under "How it works".
- **Onboarding email** (sent on signup): the Core walkthrough + a one-line "reply and tell me what's confusing" (feeds the in-app feedback you already collect).
- **1:1 outreach** for the first 20: send the Loom link directly with a personal line.
- Pair every share with the **Get Started** URL.

---

## 6. Optional: an in-app guided tour (later)
If you'd rather guide users *inside* the live app than record a video:
- Lightweight: a library like **Driver.js** / **Shepherd.js** / **react-joyride** to highlight Log → Home due card → Reviews on first login (gate it on a `localStorage` "seen tour" flag).
- Or zero-dependency: a dismissible "Start here" card on Home for brand-new accounts (no activities yet) that deep-links to `/log`.
- This is post-validation polish — the recorded walkthrough is higher leverage for the first cohort.

---

## 7. Refresh cadence
Re-record when the **core loop UI** changes (Log form, Review gate, Home). Cosmetic tweaks don't need a re-shoot. Keep the master MP4 so you can re-trim the GIF without re-recording.
