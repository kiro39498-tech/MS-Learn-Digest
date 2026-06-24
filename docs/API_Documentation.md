# API Documentation
## MS Learn Digest

**Base URL:** `http://localhost:8000/api`  
**Authentication:** `Authorization: Bearer <JWT>` on all protected endpoints  
**Content-Type:** `application/json`  

---

## Authentication (`/api/auth`)

### POST /api/auth/google
Exchange a Google OAuth authorization code for a JWT.

**Auth Required:** No

**Request:**
```json
{
  "code": "4/0AY0e-g7...",
  "redirect_uri": "http://localhost:8000/auth/google/callback"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Error Codes:** `401` — invalid code or failed Google profile fetch

---

### POST /api/auth/email/request
Request a magic-link login email. Token expires in 15 minutes. Rate limited to 5 per email per hour.

**Auth Required:** No

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response 200:**
```json
{
  "status": "sent",
  "message": "Login link sent. Check your email.",
  "email": "user@example.com"
}
```

**Error Codes:** `429` — rate limited, `502` — email send failure

---

### POST /api/auth/email/verify
Verify a magic-link token and receive a JWT.

**Auth Required:** No

**Request:**
```json
{
  "token": "a3f2c1d4e5..."
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Error Codes:** `401` — invalid, expired, or already-used token

---

### GET /api/auth/providers
List available authentication providers.

**Auth Required:** No

**Response 200:**
```json
{
  "providers": [
    {"id": "google", "name": "Continue with Google", "type": "oauth", "available": true},
    {"id": "email", "name": "Continue with Email", "type": "magic_link", "available": true}
  ]
}
```

---

## Users (`/api/users`)

### GET /api/users/me
Get current user profile including preferences. Auto-heals `is_onboarded` if subscriptions exist.

**Auth Required:** Yes

**Response 200:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "Jane Smith",
  "avatar_url": "https://...",
  "role": "individual",
  "is_onboarded": true,
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-10T08:00:00Z",
  "preferences": {
    "id": "uuid",
    "user_id": "uuid",
    "frequency": "weekly",
    "delivery_time": "08:00",
    "delivery_day": 0,
    "timezone": "Asia/Kolkata"
  }
}
```

---

### PUT /api/users/me/preferences
Create or update delivery preferences.

**Auth Required:** Yes

**Request:**
```json
{
  "frequency": "weekly",
  "delivery_time": "08:00:00",
  "delivery_day": 0,
  "timezone": "Asia/Kolkata"
}
```

**Response 200:** `UserPreferenceResponse`

**Notes:** `delivery_day`: 0=Monday … 6=Sunday. `frequency`: `daily | weekly | biweekly | monthly`.

---

## Topics (`/api/topics`)

### GET /api/topics/
Flat list of all active topics.

**Auth Required:** No

**Response 200:** `TopicFlat[]`
```json
[
  {
    "id": "uuid",
    "name": "Azure",
    "slug": "azure",
    "description": "Microsoft Azure cloud platform",
    "icon": "cloud",
    "level": 0,
    "parent_topic_id": null,
    "catalog_products": ["azure"],
    "catalog_subjects": ["azure"],
    "is_active": true,
    "created_at": "2026-06-01T00:00:00Z"
  }
]
```

---

### GET /api/topics/tree
Full nested topic tree.

**Auth Required:** No

**Response 200:** `TopicNode[]` — each node has a `children: TopicNode[]` array.

---

### GET /api/topics/roots
Root-level topics only (level = 0).

**Auth Required:** No  
**Response 200:** `TopicFlat[]`

---

### GET /api/topics/{topic_id}/children
Direct children of a specific topic.

**Auth Required:** No  
**Response 200:** `TopicFlat[]`  
**Error Codes:** `404`

---

### GET /api/topics/my
Topics the current user is subscribed to.

**Auth Required:** Yes  
**Response 200:** `TopicFlat[]`

---

### POST /api/topics/subscribe
Replace user's topic subscriptions (atomic). Sets `is_onboarded=true` if ≥1 topic selected.

**Auth Required:** Yes

**Request:**
```json
{
  "topic_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

**Response 200:** `UserSubscriptionResponse[]`

---

### POST /api/topics/onboard
Complete onboarding — saves subscriptions and sets `is_onboarded=true`.

**Auth Required:** Yes

**Request:** Same as `/subscribe`

**Response 200:**
```json
{
  "status": "onboarded",
  "is_onboarded": true
}
```

---

## Digests (`/api/digests`)

### GET /api/digests/
List most recent 20 digests for the current user.

**Auth Required:** Yes

**Response 200:** `DigestResponse[]`
```json
[
  {
    "id": "uuid",
    "title": "Your Weekly MS Learn Digest",
    "digest_type": "individual",
    "topic_names": ["Azure", "Fabric"],
    "period_start": "2026-06-03T02:00:00Z",
    "period_end": "2026-06-10T08:00:00Z",
    "sent_at": "2026-06-10T08:05:00Z",
    "status": "sent",
    "recipient_count": 1,
    "created_at": "2026-06-10T08:04:00Z",
    "items": [
      {
        "id": "uuid",
        "position": 0,
        "section": "ms_learn_updates",
        "uid": "learn.wwl.module-name",
        "title": "Module Title",
        "url": "https://learn.microsoft.com/...",
        "content_type": "module"
      }
    ]
  }
]
```

---

### GET /api/digests/{digest_id}
Get full digest content including rendered HTML.

**Auth Required:** Yes

**Response 200:** `DigestDetailResponse` — extends `DigestResponse` with `content_html: string` and `content_json: object`

**Error Codes:** `404`

---

## Learning (`/api/learning`)

### GET /api/learning/topics
All available learning track topics.

**Auth Required:** No

**Response 200:** `LearningTopicResponse[]`
```json
[
  {
    "id": "uuid",
    "name": "Azure Administrator",
    "slug": "azure-administrator",
    "description": "...",
    "icon": "☁️",
    "total_modules": 75,
    "difficulty_range": "Beginner → Expert",
    "estimated_hours": 120,
    "is_active": true
  }
]
```

---

### GET /api/learning/topics/{topic_id}
Single learning topic details.

**Auth Required:** No  
**Response 200:** `LearningTopicResponse`  
**Error Codes:** `404`

---

### GET /api/learning/topics/{topic_id}/modules
All modules for a topic in sequence order.

**Auth Required:** No

**Response 200:** `LearningModuleResponse[]`
```json
[
  {
    "id": "uuid",
    "topic_id": "uuid",
    "sequence_number": 1,
    "title": "Introduction to Azure",
    "difficulty_level": "beginner",
    "phase_name": "Phase 1: Fundamentals",
    "phase_number": 1,
    "is_milestone": false,
    "skill_level": "beginner"
  }
]
```

---

### GET /api/learning/topics/{topic_id}/phases
Distinct phases for a topic with module counts and difficulty ranges.

**Auth Required:** No

**Response 200:**
```json
{
  "topic_id": "uuid",
  "topic_name": "Azure Administrator",
  "phases": [
    {
      "phase_name": "Phase 1: Fundamentals",
      "phase_number": 1,
      "module_count": 10,
      "difficulty_levels": ["beginner"]
    },
    {
      "phase_name": "Phase 3: Networking",
      "phase_number": 3,
      "module_count": 12,
      "difficulty_levels": ["intermediate"]
    }
  ]
}
```

---

### POST /api/learning/subscribe
Subscribe to a learning track — full track or selected phases. Idempotent (updates existing subscription).

**Auth Required:** Yes

**Request:**
```json
{
  "topic_id": "uuid",
  "frequency": "weekly",
  "is_full_track": false,
  "selected_phases": ["Phase 1: Fundamentals", "Phase 3: Networking"]
}
```

**Response 200:** `LearningProgressResponse`
```json
{
  "topic_id": "uuid",
  "topic_name": "Azure Administrator",
  "topic_icon": "☁️",
  "current_module_sequence": 1,
  "total_modules": 22,
  "progress_pct": 0,
  "status": "active",
  "frequency": "weekly",
  "skill_level": "beginner",
  "current_streak_days": 0,
  "longest_streak_days": 0,
  "total_lessons_sent": 0,
  "modules_completed": 0,
  "modules_remaining": 22,
  "current_phase_name": "Phase 1: Fundamentals",
  "current_phase_number": 1,
  "is_full_track": false,
  "selected_phases": ["Phase 1: Fundamentals", "Phase 3: Networking"]
}
```

**Validation:** `frequency` must be `daily | weekly | biweekly`. If `is_full_track=false`, `selected_phases` must not be empty.

---

### DELETE /api/learning/subscribe/{topic_id}
Unsubscribe from a learning track.

**Auth Required:** Yes  
**Response 200:** `{"status": "unsubscribed", "topic_id": "uuid"}`  
**Error Codes:** `404`

---

### PATCH /api/learning/subscribe/{topic_id}/frequency
Update delivery frequency.

**Auth Required:** Yes

**Request:** `{"frequency": "daily"}`  
**Response 200:** `LearningProgressResponse`

---

### PATCH /api/learning/subscribe/{topic_id}/phases
Update phase selection for an existing subscription.

**Auth Required:** Yes

**Request:**
```json
{
  "is_full_track": false,
  "selected_phases": ["Phase 4: Security", "Phase 5: Monitoring"]
}
```

**Response 200:** `LearningProgressResponse`

---

### GET /api/learning/my
All learning subscriptions with progress for the current user.

**Auth Required:** Yes  
**Response 200:** `LearningProgressResponse[]`

---

### GET /api/learning/progress/{topic_id}
Detailed progress for one learning track.

**Auth Required:** Yes  
**Response 200:** `LearningProgressResponse`  
**Error Codes:** `404`

---

### GET /api/learning/completed
Completed learning tracks.

**Auth Required:** Yes  
**Response 200:** `LearningProgressResponse[]` (status=completed only)

---

### GET /api/learning/analytics
Learning metrics for the last 30 days.

**Auth Required:** Yes

**Response 200:** `LearningAnalyticsResponse`
```json
{
  "lessons_last_30_days": 12,
  "total_lessons_sent": 45,
  "milestones_completed": 3,
  "current_streak_days": 5,
  "longest_streak_days": 14,
  "lessons_by_topic": {"<topic_uuid>": 12},
  "active_tracks": 2,
  "completed_tracks": 1
}
```

---

### GET /api/learning/status
Learning engine health — checks table existence and seed status.

**Auth Required:** No  
**Response 200:** `{status, topics, modules, topic_list}`

---

### POST /api/learning/seed
Manually seed the learning curriculum (idempotent).

**Auth Required:** No  
**Response 200:** `{status, inserted, total_topics, topics}`

---

## Teams (`/api/teams`)

### GET /api/teams/
List teams where the current user is admin or accepted member.

**Auth Required:** Yes  
**Response 200:** `TeamResponse[]`

---

### POST /api/teams/
Create a team and its newsletter atomically.

**Auth Required:** Yes

**Request:**
```json
{
  "name": "Platform Engineering",
  "description": "Azure + Kubernetes team",
  "topic_ids": ["uuid-1", "uuid-2"],
  "frequency": "weekly",
  "delivery_time": "09:00",
  "delivery_day": 0
}
```

**Response 200:** `TeamResponse`  
**Validation:** At least one `topic_id` required.

---

### GET /api/teams/{team_id}
Get team details including members and newsletter.

**Auth Required:** Yes  
**Response 200:** `TeamResponse`  
**Error Codes:** `404`

---

### PATCH /api/teams/{team_id}
Update team name/description. Admin only.

**Auth Required:** Yes (admin)  
**Request:** `{"name": "New Name", "description": "..."}`  
**Response 200:** `TeamResponse`  
**Error Codes:** `403`, `404`

---

### DELETE /api/teams/{team_id}
Delete team and all associated data (cascade). Admin only.

**Auth Required:** Yes (admin)  
**Response 200:** `{"status": "deleted", "team_id": "uuid"}`  
**Error Codes:** `403`, `404`

---

### GET /api/teams/{team_id}/newsletter
Get team newsletter configuration.

**Auth Required:** Yes  
**Response 200:** `TeamNewsletterResponse`  
**Error Codes:** `404`

---

### PATCH /api/teams/{team_id}/newsletter/topics
Replace newsletter topic list. Admin only.

**Auth Required:** Yes (admin)  
**Request:** `{"topic_ids": ["uuid-1", "uuid-2"]}`  
**Response 200:** `TeamNewsletterResponse`

---

### PATCH /api/teams/{team_id}/newsletter/schedule
Update newsletter delivery schedule. Admin only. Timezone is always fixed to Asia/Kolkata.

**Auth Required:** Yes (admin)  
**Request:** `{"frequency": "weekly", "delivery_time": "09:00", "delivery_day": 0}`  
**Response 200:** `TeamNewsletterResponse`

---

### PATCH /api/teams/{team_id}/newsletter/toggle
Pause or resume the newsletter. Admin only.

**Auth Required:** Yes (admin)  
**Response 200:** `{"is_active": false, "team_id": "uuid"}`

---

### POST /api/teams/{team_id}/invite
Invite a member by email. Sends invitation email. Admin only.

**Auth Required:** Yes (admin)

**Request:** `{"email": "member@example.com", "role": "member"}`

**Response 200:** `InviteResult`
```json
{
  "member": {"id": "uuid", "email": "...", "status": "pending"},
  "invitation_token": "abc123...",
  "invitation_expires_at": "2026-06-13T10:00:00Z",
  "invite_url": "http://localhost:5173/team-invite/abc123...",
  "email_sent": true
}
```

**Error Codes:** `403`, `404`, `409` (already accepted)

---

### POST /api/teams/{team_id}/members/{member_id}/resend
Resend invitation to a pending/declined/expired member.

**Auth Required:** Yes (admin)  
**Response 200:** `InviteResult`

---

### DELETE /api/teams/{team_id}/members/{member_id}
Remove accepted member or cancel pending invitation.

**Auth Required:** Yes (admin)  
**Response 200:** `{"status": "removed"}`

---

### GET /api/teams/invite/{token}
Public endpoint — preview invitation details before accepting.

**Auth Required:** No  
**Response 200:** `InvitePreviewResponse`  
**Error Codes:** `404`, `409` (already responded), `410` (expired)

---

### POST /api/teams/invite/{token}/accept
Accept invitation. Links membership to authenticated user account.

**Auth Required:** Yes  
**Response 200:** `TeamMemberResponse`  
**Error Codes:** `401`, `410`

---

### POST /api/teams/invite/{token}/decline
Decline invitation. No auth required.

**Auth Required:** No  
**Response 200:** `{"status": "declined"}`  
**Error Codes:** `410`

---

### GET /api/teams/{team_id}/digests
Recent 20 digests for a team.

**Auth Required:** Yes  
**Response 200:** `TeamDigestSummary[]`

---

## Newsletters (`/api/newsletters`)

### GET /api/newsletters/
List newsletters for teams where the current user is admin.

**Auth Required:** Yes  
**Response 200:** `TeamNewsletterResponse[]`

---

## Admin (`/api/admin`)

All admin endpoints require `ADMIN_ENABLED=true`. Disabled in production by default.

### GET /api/admin/config
Show SMTP configuration (password masked).

**Auth Required:** Yes

---

### GET /api/admin/smtp-check
Test SMTP connection. Does not send an email.

**Auth Required:** Yes  
**Response 200:** `{smtp_connection, message, config}`  
**Error Codes:** `502` — connection failed

---

### POST /api/admin/send-test-email
Send a test email.

**Auth Required:** Yes  
**Request:** `{"email": "test@example.com"}`

---

### POST /api/admin/send-test-digest
Send a sample digest email with hardcoded content.

**Auth Required:** Yes  
**Request:** `{"email": "test@example.com", "user_name": "Learner"}`

---

### GET /api/admin/preview-digest
Return digest HTML in browser.

**Auth Required:** Yes  
**Response:** `text/html`

---

### POST /api/admin/catalog-sync
Trigger a full catalog sync (modules + learningPaths). Same as the scheduled job.

**Auth Required:** Yes  
**Response 200:** `{status, fetched, upserted, total_cached, duration_seconds, next_scheduled_sync}`

---

### GET /api/admin/catalog-cache/stats
Catalog cache health statistics.

**Auth Required:** Yes  
**Response 200:** `{total_cached, modules, learning_paths, latest_last_modified, last_sync_status, sync_needed}`

---

### POST /api/admin/catalog-cache/preview
Preview matched items for given topic slugs.

**Auth Required:** Yes  
**Request:** `{"topic_slugs": ["azure", "fabric"], "frequency": "weekly"}`  
**Response 200:** `{matched_count, items[]}`

---

### POST /api/admin/test/send-my-digest
Generate and send a real digest for the authenticated user. Reads from catalog_cache.

**Auth Required:** Yes  
**Response 200:** `{status, recipient, digest_id, smtp_status, diagnostic}`

---

### GET /api/admin/debug/onboarding
Onboarding state check with auto-heal.

**Auth Required:** Yes  
**Response 200:** `{is_onboarded, subscription_count, preferences, verdict}`

---

### GET /api/admin/learning/status
Learning engine status (tables + seed state).

**Auth Required:** Yes

---

### POST /api/admin/learning/send-lesson
Send a learning lesson to the authenticated user immediately.

**Auth Required:** Yes

---

### POST /api/admin/teams/test-create
Create a test team for the authenticated user.

**Auth Required:** Yes

---

### POST /api/admin/teams/{team_id}/test-invite
Invite an email to a test team and send the invitation.

**Auth Required:** Yes

---

### POST /api/admin/teams/invite/{token}/accept
Accept an invitation without requiring the invitee to be logged in (admin testing only).

**Auth Required:** No (admin-only path)

---

### POST /api/admin/teams/{team_id}/test-digest
Generate and send a team newsletter for testing.

**Auth Required:** Yes (admin)

---

### GET /api/admin/teams/{team_id}/delivery-status
Get delivery status for a team.

**Auth Required:** Yes (admin)

---

## Misc

### GET /health
Health check — no auth required.

**Response 200:** `{"status": "ok", "env": "development"}`
