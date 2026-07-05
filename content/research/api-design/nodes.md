# API Design & Distributed APIs — node-derivation research (audit trail)

Source: Gemini Deep Research, 2026-07-04. Target roles: Backend Engineer / Backend SDE, India,
0–4 yrs. Scope: FOUNDATIONAL SLICE (3 phases). Prompt: `content/research/api-design-foundational.prompt.md`.
Seeded by: `backend/seed_api_design.py` (UUID e0e0e0e0, slug api-design).

This is the audit trail — WHY the roadmap looks the way it does. The `NODES` themselves live in
the seed. Keep the excluded list + validation; they justify the scope.

## Node list (21 nodes, 5 phases) — see seed_api_design.py for the tuples
Phases 1-3 = the Gemini research run (14 nodes). Phases 4-5 = Claude additions (7 nodes) to lift
it past beginner-only and earn the "Distributed APIs" title; NOT from the research run, so
lower-confidence on frequency — validate against a JD/interview sweep when the full research run
for API Design happens.
- REST Fundamentals (8): GET vs POST · PUT vs PATCH · Idempotency · Noun-based URIs · HTTP status
  codes · Pagination & filtering · **Error response design** · **CORS & preflight**
- Auth & Authorization (5): AuthN vs AuthZ · JWT structure · Access vs refresh tokens · Token
  storage & XSS · BOLA/IDOR
- Versioning & Evolution (3): URI vs header versioning · Backward compatibility · Endpoint deprecation
- **Protocol Choice & Interop (2):** REST vs gRPC vs GraphQL · OpenAPI/Swagger
- **Resilience & Distributed Contract (3):** Rate limiting & 429 · Idempotency keys · Webhooks & signatures

Boundary note for the new resilience nodes: they cover the CLIENT-FACING contract (429/Retry-After,
Idempotency-Key header, webhook HMAC) — NOT the infra that implements it (token-bucket algorithm,
gateway) which stays in System Design. "Rate limiting & 429" ≠ the excluded "gateway rate limiting".

## Excluded list (proves scope discipline)
| Excluded item | Reason | Note |
|---|---|---|
| HATEOAS constraints | canon-only | Central to Fielding's REST but zero practical early-career expectation across Razorpay/Meesho/Flipkart JDs. The textbook-vs-interview gap. |
| API gateway internals (routing, token/leaky bucket rate limiting, LB) | belongs-in-System-Design | Infra concern; this roadmap governs the contract, not the routing layer. |
| OAuth 2.0 PKCE / OIDC broker deep-dive | senior-only | IAM specialist / Staff work. Early-career must *consume + validate* JWTs, not build the auth server. |
| Framework-specific annotations (@RestController, app.get, Pydantic) | belongs-in-Backend | Implementation syntax; interviews probe protocol semantics, not framework. |
| GraphQL vs REST trade-offs / federation | out-of-scope | Distinct protocol paradigm; dilutes HTTP-verb / resource focus. (Belongs in FULL roadmap later as a *contrast* node, not foundational.) |
| Distributed tracing & observability (Zipkin, Sleuth, Prometheus) | belongs-in-System-Design | Telemetry is operational readiness, not contract. |
| Redis caching strategies (write/read-through, cache-aside) | belongs-in-System-Design | Data-retrieval optimization, not resource contract. |
| SOAP & XML payloads | low-frequency | Legacy banking/telecom only; modern product cos are REST/gRPC over JSON/Protobuf. |
| Service mesh (Istio/Envoy, mTLS, circuit breaking) | senior-only | Platform/DevOps advanced topic. |

## Validation (8 real interview questions → nodes)
1. Chargebee — "stop a client retrying a successful payment" → **Idempotency mechanisms**
2. Netomi — "PUT vs PATCH" → **PUT vs PATCH updates**
3. Fynd (Mumbai) — "GET vs POST; can we write in a GET?" → **GET vs POST semantics**
4. (LLD) — "design schema + REST API for vehicle search/filter" → **Noun-based URI design + Pagination & filtering**
5. Zeta/Directi SDE2 — "JWT elements + signature significance" → **JWT statelessness & structure**
6. Amazon — "exploit an IDOR, then protect against it" → **BOLA/IDOR + AuthN vs AuthZ**
7. (frontend/backend bridge) — "JWT in localStorage vs cookies" → **Token storage & XSS**
8. Publicis Sapient — "breaking changes with un-updatable mobile clients" → **URI vs header versioning + Backward compatibility + Endpoint deprecation**

### Validation gaps (Claude review, not in the Gemini output)
- **HTTP status codes** and **Access vs refresh tokens** map to NO question in the sample. Both
  KEPT — status codes are asked constantly, access/refresh is bread-and-butter; this is a gap in
  the 8-question *sample*, not orphan nodes. The report should have flagged these per its own
  rules — a reminder the auto-validation isn't airtight; a human coverage check still matters.

### Phase "so that" objectives
- REST Fundamentals — *so that* you map business operations to the right verb/status code and
  design idempotent endpoints on the job.
- Auth & Authorization — *so that* you pass identity between services and prevent unauthorized
  data access.
- Versioning & Evolution — *so that* you ship changes to slow-updating mobile clients without
  breaking them.

## Sources
**JD:** Jumeau Capital (wellfound 4391233) · Razorpay (instahyre 418911) · Meesho (instahyre
413919) · Flipkart SDE4 (instahyre 416786) · B2C startup Pune (wellfound 4287687)
**Interviews:** Chargebee (leetcode discuss 5461584) · Zeta/Directi (leetcode 1607028) · Fynd
(leetcode 6024407) · Publicis Sapient (leetcode 7509276) · Netomi (GfG) · Amazon SecEng (reddit
r/cybersecurity 1iuk0a4) · JWT-in-localStorage (reddit r/webdev 1ny9t08) · API updates (reddit
r/ExperiencedDevs 1i4bjwr)
**Canon:** OWASP API Security Top 10 2023 (owasp.org/www-chapter-bangkok)

## NEXT — to complete the full roadmap (research these, MERGE, seed once)
Rate-limit *design* (client-facing 429/Retry-After semantics, not gateway infra) · API security
beyond BOLA (OWASP top items: broken auth, mass assignment, injection) · gRPC & GraphQL as
*contrast* nodes · Webhooks + idempotency keys · OpenAPI/Swagger contract-first. Re-seeding wipes
progress — don't promote API Design to prod until merged.
