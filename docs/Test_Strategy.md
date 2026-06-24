# Test Strategy and Manual Test Cases
## MS Learn Digest

---

## Overview

No automated test suite is currently configured. This document provides:
1. The recommended test strategy for implementing tests
2. Comprehensive manual test cases covering all major flows
3. Expected results and failure scenarios

---

## Recommended Test Strategy

### Unit Tests (Recommended Framework: pytest + pytest-asyncio)

**Priority modules to unit test:**

| Module | Key Functions to Test |
|---|---|
| `core/security.py` | `create_access_token()`, `decode_token()`, expired token rejection |
| `services/email_auth_service.py` | `_check_rate_limit()`, `_hash_token()`, token expiry logic |
| `services/digest/generator.py` | `_is_due()`, `_compute_cache_key()`, `_match_topics()`, `_lookback()` |
| `repositories/topic_repository.py` | `resolve_descendant_ids()`, `seed_system_topics()` |
| `repositories/learning_repository.py` | `advance_module()`, `is_due()`, `get_modules_for_subscription()` |
| `services/ingestion/sync.py` | `_parse_ts()`, URL validation, UPSERT logic |

**Setup:**
```bash
pip install pytest pytest-asyncio httpx
# For DB tests:
pip install pytest-postgresql
```

---

### Integration Tests (Recommended: TestClient + SQLite/PostgreSQL test DB)

FastAPI's `TestClient` (built on Starlette) allows full request/response testing against a real database.

**Priority flows:**
1. Auth: Google code exchange → JWT
2. Auth: Magic-link request → verify → JWT
3. Topic subscription: subscribe → verify in DB → GET /topics/my
4. Digest: mock catalog_cache rows → trigger dispatch → verify digest created
5. Learning: subscribe → mock advance → verify progress

---

### Manual Test Cases

The following manual test cases can be run against a running local instance.

---

## Manual Test Cases

### TC-01: Google Login

| Step | Action | Expected Result |
|---|---|---|
| 1 | Open `http://localhost:5173` | Landing page loads with Google and Email login buttons |
| 2 | Click "Continue with Google" | Browser redirects to Google OAuth consent screen |
| 3 | Select a Google account and approve | Browser redirects to `/auth/callback` |
| 4 | Wait for redirect | App navigates to `/onboarding` (first time) or `/dashboard` (returning user) |
| **Pass** | JWT stored in localStorage, user profile loaded | ✅ |
| **Fail** | "Invalid Google OAuth code" or redirect loops | Check `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, redirect URI in Google Console |

---

### TC-02: Email Magic-Link Login

| Step | Action | Expected Result |
|---|---|---|
| 1 | Click "Continue with Email", enter email | Form submits |
| 2 | Check inbox | Email arrives within 30 seconds with "Sign in" button |
| 3 | Click the sign-in button | Browser opens app at `/auth/email/callback?token=...` |
| 4 | Wait for redirect | App navigates to `/onboarding` or `/dashboard` |
| **Pass** | Authenticated, JWT stored | ✅ |
| **Fail-expired** | Try clicking same link again after 15 min | Returns "This login link has expired" |
| **Fail-reuse** | Click same link twice immediately | Second attempt returns "already been used" |
| **Fail-rate-limit** | Request 6 times in 1 hour | 6th request returns 429 |

---

### TC-03: Topic Subscription and Onboarding

| Step | Action | Expected Result |
|---|---|---|
| 1 | Complete Google/email login as new user | Redirected to `/onboarding` |
| 2 | On Step 1: click "Azure" root card | Card highlighted with blue border |
| 3 | Click "Security" root card | Both Azure and Security are selected |
| 4 | Search for "Fabric" | Topic card grid filters to show only Fabric-related cards |
| 5 | Select "Fabric Fundamentals" subtopic | Parent "Microsoft Fabric" card shows "1 subtopics selected" badge |
| 6 | Click "Next: Schedule" | Progresses to Step 2 |
| 7 | Set frequency = Weekly, Day = Monday, Time = 9:00 AM | Schedule form shows correct values |
| 8 | Click "Complete Setup" | Loading spinner, then redirect to `/dashboard` |
| **Pass** | `GET /api/users/me` returns `is_onboarded: true`, `GET /api/topics/my` returns selected topics | ✅ |

---

### TC-04: Catalog Sync

| Step | Action | Expected Result |
|---|---|---|
| 1 | `GET /api/admin/catalog-cache/stats` | Check `total_cached` value |
| 2 | `POST /api/admin/catalog-sync` | Response after 2-5 minutes: `{status: "completed", fetched: N, upserted: N}` |
| 3 | `GET /api/admin/catalog-cache/stats` | `total_cached > 0`, `last_sync_status: "success"` |
| **Pass** | Catalog populated with 10,000+ items | ✅ |
| **Fail** | `fetched: 0` | Check internet connectivity and MS Learn API availability |

---

### TC-05: Digest Generation (Admin Test)

Prerequisites: TC-03 complete (user has subscriptions), TC-04 complete (catalog populated)

| Step | Action | Expected Result |
|---|---|---|
| 1 | `POST /api/admin/test/send-my-digest` | Returns `{status: "sent", recipient: "your@email.com", digest_id: "uuid"}` |
| 2 | Check inbox | Digest email arrives with personalised content |
| 3 | `GET /api/digests/` | Shows new digest with `status: "sent"` |
| 4 | Click digest in dashboard | Full HTML newsletter renders |
| **Fail: no_content** | `status: "no_content"` | Check `diagnostic.catalog_items_matched` — if 0, run catalog sync first |
| **Fail: smtp** | `smtp_status: "failed"` | Check SMTP config — run `GET /api/admin/smtp-check` |

---

### TC-06: Learning Track Enrollment

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to `/learning` | Learning Center loads, tracks visible |
| 2 | Click "Preview curriculum" on Azure Administrator | Phases and module list appear |
| 3 | Click "Enrol in Track" | PhaseSelector modal opens |
| 4 | Select "Select Phases" mode | Phase cards appear |
| 5 | Check "Phase 1: Fundamentals" and "Phase 3: Networking" | 2 phases selected, summary shows correct module count |
| 6 | Select "Weekly" frequency | Frequency button highlighted |
| 7 | Click "Start Learning" | Modal closes, success toast shows, tab switches to "My Learning" |
| **Pass** | Track appears in "My Learning" with correct module count and "2 phases selected" badge | ✅ |

---

### TC-07: Phase Edit on Active Track

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to "My Learning" tab | Active track shows phase badge |
| 2 | Click "Edit phases" | PhaseSelector opens pre-populated with current selection |
| 3 | Add "Phase 5: Security", remove "Phase 1: Fundamentals" | Selection updated |
| 4 | Click "Start Learning" | Modal closes, success toast |
| **Pass** | Track card shows updated phase count | ✅ |

---

### TC-08: Team Creation and Member Invitation

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to `/teams` | Teams page loads |
| 2 | Click "Create Team", fill in name, select topics, set weekly schedule | Form submits |
| 3 | Team appears in list | ✅ |
| 4 | Click "Invite Member", enter an email address | Invitation sent message appears |
| 5 | Check invited email's inbox | Invitation email with Accept/Decline links |
| 6 | Click "Accept" (as invitee) | Invitation preview page shows team details |
| 7 | Log in and accept | Member status shows "accepted" in admin view |
| **Pass** | Member appears with `status: accepted` | ✅ |
| **Fail: expired** | Try accepting after 72 hours | Returns "invitation has expired" |

---

### TC-09: Team Newsletter Digest

Prerequisites: Team created with accepted members, catalog populated

| Step | Action | Expected Result |
|---|---|---|
| 1 | `POST /api/admin/teams/{team_id}/test-digest` | Response: `{status: "sent", newsletter: "...", digest_id: "uuid"}` |
| 2 | Check accepted members' inboxes | All accepted members receive identical newsletter |
| **Pass** | All members receive email, one digest record created | ✅ |
| **Fail: no members** | `status: "no_content"` if no accepted members | Ensure at least one accepted member |

---

### TC-10: SMTP Configuration Test

| Step | Action | Expected Result |
|---|---|---|
| 1 | `GET /api/admin/smtp-check` | `smtp_connection: "success"` |
| 2 | `POST /api/admin/send-test-email {"email": "you@example.com"}` | Test email received |
| **Fail: AUTH_FAIL** | `smtp_connection: "failed"` with "authentication failed" | Use App Password not account password |
| **Fail: TIMEOUT** | Connection timeout | Port 587 blocked — check firewall |

---

### TC-11: Digest Preview

| Step | Action | Expected Result |
|---|---|---|
| 1 | Open `http://localhost:8000/api/admin/preview-digest` in browser | Full digest HTML renders in browser |
| **Pass** | Newsletter layout visible with sample content | ✅ |

---

## Failure Scenarios and Expected Behaviour

| Scenario | Expected System Behaviour |
|---|---|
| Groq API down during digest generation | Fallback `ai_result` used from catalog summaries — digest still sent with lower-quality summaries |
| Groq API down during lesson generation | Fallback lesson returned — lesson email still sent |
| SMTP authentication failure | Digest/lesson marked `failed` in DB — user doesn't receive email, error logged |
| MS Learn Catalog API timeout | `catalog_sync_job` fails — `sync_metadata.status="failed"` — previous cache snapshot used for next digest run |
| Database connection lost mid-job | Exception caught — job logs error — `db.close()` called in finally — next job run works normally if DB recovers |
| User subscribes to a topic but catalog has no matching content | Digest generated with `status="no_content"` — no email sent — recorded in digest history for audit |
| Magic-link clicked after expiry | 401 returned — user must request a new link |
| Team invitation token reused | Second accept attempt returns `410 Gone` |
| Learning module sequence gap (phases skipped) | `advance_module()` correctly skips to next module in active list |
| User unsubscribes from learning track mid-progress | Subscription row deleted (CASCADE deletes phase subscriptions and analytics) |
