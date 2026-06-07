# RetainHQ — API Reference

Base URL: `https://<your-backend-domain>` (local: `http://localhost:8000`)

All endpoints require a valid Supabase Bearer JWT unless marked otherwise.

---

## Authentication

Every request must include:
```
Authorization: Bearer <supabase_access_token>
```

The token is an ES256 JWT issued by Supabase Auth after Google OAuth. FastAPI verifies it via JWKS (`/auth/v1/.well-known/jwks.json`).

**Error responses from auth:**

| Status | Condition |
|---|---|
| `401 Unauthorized` | Token missing, malformed, or expired |
| `403 Forbidden` | Token valid but role ≠ "authenticated" |
| `503 Service Unavailable` | JWKS endpoint unreachable (transient) |

---

## Endpoints

### Health

#### `GET /health`
No auth required.

**Response `200`:**
```json
{ "status": "ok" }
```

---

#### `GET /me`
Returns the authenticated user's identity as decoded from their JWT.

**Response `200`:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "authenticated",
  "message": "You are successfully authenticated through Supabase via FastAPI!"
}
```

---

### Activities

#### `GET /api/activities/`
Returns all of the current user's logged activities, newest first. Used by the Knowledge Vault.

**Response `200` — array of `ActivityListItem`:**
```json
[
  {
    "id": "uuid",
    "topic": "Binary Search",
    "key_memory": "Reduce search space by half each step; check mid, go left or right.",
    "notes": "Practice with rotated arrays",
    "difficulty": 3,
    "needed_hint": false,
    "mistake": "Off-by-one on the right boundary",
    "source_type": "problem",
    "created_at": "2026-06-01T10:00:00",
    "repetitions": 2,
    "next_review_at": "2026-06-07T10:00:00",
    "last_reviewed_at": "2026-06-01T10:00:00"
  }
]
```

**Notes:**
- No pagination — returns all rows. Limit queries with client-side filtering (Knowledge Vault does this).
- `repetitions`: how many SM-2 reviews completed so far. 0 = only the Day-0 baseline is pending.
- `next_review_at`: denormalized from the open `due` review's `scheduled_for`.

---

#### `POST /api/activities/`
Log a new learning activity. Automatically initializes SM-2 state and schedules a Day-0 baseline review due immediately.

**Request body:**
```json
{
  "topic": "Binary Search",
  "key_memory": "Reduce search space by half each step; check mid, go left or right.",
  "difficulty": 3,
  "needed_hint": false,
  "notes": "Practice with rotated arrays",
  "mistake": "Off-by-one on the right boundary",
  "source_type": "problem"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `topic` | string | yes | The subject being learned |
| `key_memory` | string | yes | The distilled memory to be recalled during reviews |
| `difficulty` | int (1–5) | yes | Subjective difficulty rating |
| `needed_hint` | bool | yes | Whether a hint was needed |
| `notes` | string | no | Free-form extra context |
| `mistake` | string | no | Common mistake to surface during reviews |
| `source_type` | string | no | `problem` \| `lecture` \| `video` \| `book` \| `article` \| `course` \| `project` \| `other` |

**Response `200` — `ActivityResponse`:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "track_id": null,
  "topic": "Binary Search",
  "key_memory": "Reduce search space...",
  "notes": null,
  "difficulty": 3,
  "needed_hint": false,
  "mistake": null,
  "created_at": "2026-06-07T10:00:00",
  "reviews_scheduled": 1
}
```

`reviews_scheduled: 1` confirms the Day-0 review was created and is immediately due.

---

### Reviews

#### `GET /api/reviews/due`
Returns all reviews that are due now for the current user, with the parent activity eager-loaded.

**Response `200` — array of `ReviewResponse`:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "activity_id": "uuid",
    "status": "due",
    "scheduled_for": "2026-06-07T10:00:00",
    "completed_at": null,
    "rating": null,
    "recalled": null,
    "created_at": "2026-06-07T10:00:00",
    "activity": {
      "id": "uuid",
      "topic": "Binary Search",
      "key_memory": "Reduce search space by half...",
      "difficulty": 3,
      "needed_hint": false,
      "mistake": "Off-by-one on the right boundary",
      "created_at": "2026-06-07T10:00:00",
      "reviews_scheduled": 0
    }
  }
]
```

**Notes:**
- Only reviews with `status='due'` and `scheduled_for ≤ now` are returned.
- Results are ordered by `scheduled_for ASC` (oldest overdue first).
- No pagination — returns all due reviews. A long break can produce many results.

---

#### `POST /api/reviews/{review_id}/complete`
Complete a due review. Advances the activity's SM-2 state and schedules the next review.

**Path parameter:** `review_id` — UUID of the review to complete.

**Request body:**
```json
{
  "rating": "medium",
  "recalled": true
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `rating` | `"easy"` \| `"medium"` \| `"hard"` | yes | Subjective: how hard it felt |
| `recalled` | bool | no | Objective: did they reconstruct the answer? `false` = lapse |

**SM-2 grade mapping:**

| `recalled` | `rating` | Quality (0–5) | Outcome |
|---|---|---|---|
| `false` | any | 2 | Lapse → next review in 1d, EF decreases |
| `true` / null | `"hard"` | 3 | Struggled → interval grows slowly |
| `true` / null | `"medium"` | 4 | Recalled ok → interval grows normally |
| `true` / null | `"easy"` | 5 | Effortless → interval grows faster |

**Interval ladder:**
- Rep 1 (Day-0 → first real review): +1 day
- Rep 2: +6 days
- Rep 3+: `round(previous_interval × ease_factor)`
- Lapse resets `repetitions` to 1 (next success → 6 days, not another 1-day loop)

**Response `200` — `ReviewResponse`:** Same shape as the due-review item, now with `status: "completed"`, `completed_at`, `rating`, `recalled`, and a new `due` review visible on the next `GET /api/reviews/due` call.

**Error responses:**

| Status | Condition |
|---|---|
| `400 Bad Request` | Review already completed |
| `404 Not Found` | Review not found or belongs to a different user (IDOR protection) |

---

### Dashboard

#### `GET /api/dashboard/`
Returns aggregated stats for the current user's dashboard.

**Response `200` — `DashboardStats`:**
```json
{
  "due_count": 3,
  "consistency_window": 5,
  "daily_progress": 4,
  "total_activities": 42,
  "total_reviews_completed": 87
}
```

| Field | Description |
|---|---|
| `due_count` | Reviews currently overdue |
| `consistency_window` | Distinct days with any activity or review in the last 7 days |
| `daily_progress` | Activities logged + reviews completed today |
| `total_activities` | Lifetime activities logged |
| `total_reviews_completed` | Lifetime reviews completed |

---

### Roadmaps

#### `GET /api/roadmaps/`
Lists all roadmaps with the current user's progress.

**Response `200` — array of `RoadmapListItem`:**
```json
[
  {
    "id": "uuid",
    "title": "DSA — Striver A2Z",
    "description": "Comprehensive DSA roadmap following Striver's A2Z sheet.",
    "total_nodes": 120,
    "done_nodes": 15,
    "progress_pct": 12
  }
]
```

---

#### `GET /api/roadmaps/{roadmap_id}`
Returns a roadmap's full node list with per-node progress for the current user.

**Response `200` — `RoadmapDetailOut`:**
```json
{
  "id": "uuid",
  "title": "DSA — Striver A2Z",
  "description": "...",
  "total_nodes": 120,
  "done_nodes": 15,
  "progress_pct": 12,
  "nodes": [
    {
      "id": "uuid",
      "phase": "Step 1 — Basics",
      "section": "Arrays",
      "title": "Two Sum",
      "tier": "easy",
      "order_index": 1,
      "description": "Find two indices that sum to target.",
      "parent_id": null,
      "status": "done"
    }
  ]
}
```

`status` per node is `"done"` or `"not_started"` (default). Nodes with `parent_id` set are subtopics of the parent node.

**Error responses:**

| Status | Condition |
|---|---|
| `404 Not Found` | Roadmap not found |

---

#### `PUT /api/roadmaps/nodes/{node_id}/progress`
Idempotent upsert of a node's status for the current user.

**Path parameter:** `node_id` — UUID of the roadmap node.

**Request body:**
```json
{ "status": "done" }
```

`status` must be `"done"` or `"not_started"`.

**Response `200`:**
```json
{ "node_id": "uuid", "status": "done" }
```

**Error responses:**

| Status | Condition |
|---|---|
| `400 Bad Request` | Status not `"done"` or `"not_started"` |
| `404 Not Found` | Node not found |

---

### Feedback

#### `POST /api/feedback/`
Submit a suggestion or feedback message (any authenticated user).

**Request body:**
```json
{ "message": "It would be great to filter by source type in the Vault." }
```

**Response `200`:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "message": "It would be great to...",
  "status": "new",
  "created_at": "2026-06-07T10:00:00"
}
```

---

### Admin (Founder-gated)

These endpoints require the authenticated user's email to equal `ADMIN_EMAIL`. All others receive `403 Forbidden`.

---

#### `GET /api/admin/funnel`
Activation funnel derived from all users' data.

**Response `200` — `AdminFunnel`:**
```json
{
  "summary": {
    "signups": 10,
    "logged_activity": 7,
    "completed_review": 5,
    "returned_later_day": 3,
    "pct_activated": 70.0,
    "pct_reviewed": 50.0,
    "pct_retained": 30.0
  },
  "users": [
    {
      "email": "user@example.com",
      "signed_up": "2026-05-01",
      "activities": 12,
      "reviews_done": 8,
      "last_active": "2026-06-06"
    }
  ],
  "by_source": [
    { "source_type": "problem", "activities": 30 },
    { "source_type": "lecture", "activities": 12 },
    { "source_type": "unspecified", "activities": 5 }
  ]
}
```

Funnel definitions:
- **Signups:** all users in `auth.users`
- **Logged activity:** users who have at least one activity
- **Completed review:** users who have at least one completed review
- **Returned later day:** users who had any activity or review on a date after their signup date

---

#### `GET /api/admin/feedback`
Lists all submitted feedback messages with user emails.

**Response `200` — array:**
```json
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "message": "It would be great to...",
    "status": "new",
    "created_at": "2026-06-07T10:00:00"
  }
]
```

---

## Common Error Shape

All error responses follow FastAPI's default format:
```json
{ "detail": "Human-readable error message" }
```

---

## Data Types Reference

| Type | Format |
|---|---|
| UUIDs | Standard `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| Timestamps | ISO 8601, naive UTC: `2026-06-07T10:00:00` |
| Ratings | `"easy"` \| `"medium"` \| `"hard"` |
| Source types | `"problem"` \| `"lecture"` \| `"video"` \| `"book"` \| `"article"` \| `"course"` \| `"project"` \| `"other"` |
| Node status | `"done"` \| `"not_started"` |
| Review status | `"due"` \| `"completed"` |
| Feedback status | `"new"` \| `"reviewed"` \| `"resolved"` |
