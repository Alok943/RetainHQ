# Deep-research prompt — Gorakhpur private-school CENSUS (local pitch targets)

> Paste from "ROLE" down into Gemini Deep Research. This is a **narrow enumeration task** — a
> directory of pitch-target schools, NOT a market analysis and NOT a regional study. Run it
> SEPARATELY from `PROMPT-school-b2b-research.md` (the national industry analysis).
>
> **Why this prompt is shaped this way:** a prior run drifted into a Gorakhpur *geography/history*
> report (demographics, expressways, Buddhist tourism, weather). The guards below exist to stop
> that. If the output starts describing the region instead of listing schools, the run failed.

---

## ⛔ SCOPE GUARD — read first
Your ONLY subject is **private schools in and around Gorakhpur city (Uttar Pradesh) as sales
targets for an education product.** You must NOT write about: the region's history, mythology,
Koshal/Kushinagar, demographics, population growth, literacy statistics, weather/monsoon, air
quality, tourism, Buddhist sites, expressways, industrial corridors, or infrastructure. Zero
paragraphs of regional profile. If you cannot find data for a field, write "not found" — do NOT
substitute general facts about the region to fill space. The deliverable is a **school list +
buyer facts**, nothing else.

## ROLE
You are a sales-operations researcher building a target list of private schools in Gorakhpur city
for an EdTech pitch. Be concrete: names, boards, fee tiers, contact/decision-maker where public.
Cite sources; where a fact isn't publicly available, say "not found" rather than guessing.

## CONTEXT (one line — do not expand on it)
Product = pre-built interactive Physics (Class 9-10) lessons for classroom + student use, sold to
schools. We need to know which local private schools are plausible buyers and how they buy.

## WHAT TO PRODUCE

### 1. School list (the core deliverable — a table)
Enumerate private schools in Gorakhpur city + immediate periphery. For EACH:
| School name | Board (CBSE/ICSE/UP) | Approx. annual fee tier (budget <₹30k / mid ₹30k-₹1L / premium >₹1L) | Classes offered (does it cover 9-10?) | Est. size (sections/strength if findable) | Known tech/smart-class use | Public contact (site/phone) | Source |
- Prioritize schools that (a) run Classes 9-10 and (b) are CBSE/ICSE (more likely to pay for
  supplementary content than fee-capped budget schools).
- Aim for as complete a list as public sources allow (school directories, board affiliation
  lists, JustDial/Sulekha, school websites). Note how many you found vs. estimated total.

### 2. Tier segmentation
Group the found schools into budget / mid / premium and state which tier is the realistic first
target for a paid pilot (with reasoning tied to ability-to-pay + likely tech-openness).

### 3. Buyer mechanics (local, concrete — not national generalities)
- Who decides at these schools (owner/trust chairman vs principal vs academic coordinator)?
- Any evidence of existing smart-class/edtech vendors already selling into Gorakhpur schools
  (Extramarks, LEAD, Next Education, local resellers)? Name them if found.
- Typical procurement timing (school year start, budget cycles) if discoverable.

### 4. CBSE/ICSE affiliation anchors
List the largest / best-known private schools in Gorakhpur by reputation (the "lighthouse"
accounts — landing one makes others follow). 5-10 names with why they're influential locally.

## OUTPUT FORMAT
Tables first (school list is the centerpiece), then the short segmentation + buyer notes. End with
**"Target shortlist": the 8-10 schools to approach first**, ranked, each with a one-line reason.
No regional profile, no executive essay. Sources list at the end (directories + school sites).
