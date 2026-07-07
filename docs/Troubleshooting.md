# Troubleshooting Guide
## MS Learn Digest

---

## SMTP / Email Issues

### Symptom: SMTP authentication failed
```
EMAIL_SEND | AUTH_FAIL | to=user@example.com
```

**Cause:** Wrong SMTP password — Gmail requires an App Password, not your account password.

**Fix:**
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Enable 2-Factor Authentication if not already enabled
3. Create a new App Password → select "Mail" → "Other" → enter any name
4. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`, no spaces)
5. Set `SMTP_PASSWORD=xxxxxxxxxxxxxxxxx` (without spaces) in `.env`
6. Restart backend
7. Test: `GET /api/admin/smtp-check`

---

### Symptom: SMTP connection timeout
```
SMTP_TEST | TIMEOUT
```

**Cause:** Port 587 is blocked by a firewall or ISP.

**Fix:** Verify port 587 is accessible:
```bash
telnet smtp.gmail.com 587
```
If blocked, contact your network admin or use a different network.

---

### Symptom: Users not receiving emails
**Diagnosis checklist:**
1. Check `GET /api/admin/smtp-check` → must return `smtp_connection: "success"`
2. Check spam/junk folder in recipient's email client
3. Check digest status in database: look for `status="failed"` in `digests` table
4. Look for `EMAIL_SEND | FAIL` in backend logs
5. Verify recipient email address is correct

---

### Symptom: Magic-link emails not arriving
**Causes and fixes:**
- SMTP not configured → `SMTP_EMAIL` and `SMTP_PASSWORD` must be set
- Email in spam → check junk folder
- Rate limited → max 5 attempts per hour per email address
- Token already used → request a new link

---

## OAuth Issues

### Symptom: "Invalid Google OAuth code"
```
Google token exchange failed: ...
```

**Causes:**
1. Authorization code already used (codes are single-use)
2. `redirect_uri` in the request doesn't match what's configured in Google Console
3. `GOOGLE_CLIENT_ID` or `GOOGLE_CLIENT_SECRET` is wrong

**Fix:**
1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` match Google Console
2. In Google Console → OAuth 2.0 → Authorized redirect URIs: add `http://localhost:8000/auth/google/callback`
3. In frontend `.env`: verify `VITE_GOOGLE_CLIENT_ID` matches backend `GOOGLE_CLIENT_ID`

---

### Symptom: "Failed to fetch Google profile"
**Cause:** Google access token exchange succeeded but profile fetch failed.

**Fix:** Usually transient — retry. If persistent, check Google OAuth API status.

---

### Symptom: Google login works but user not redirected after callback
**Check:** `AuthCallback.jsx` — the callback page should exchange the code and redirect.
- Verify `VITE_GOOGLE_CLIENT_ID` is set in `frontend/.env`
- Check browser console for errors
- Check backend logs for `POST /api/auth/google` errors

---

## Groq / AI Failures

### Symptom: Digests sent but AI summaries are generic
```
DIGEST | user=... | GROQ FALLBACK | Groq failed (...). Generating newsletter from catalog summaries only.
```

**Cause:** Groq API call failed — rate limit, timeout, or invalid API key.

**Fix:**
1. Verify `GROQ_API_KEY` is set in `.env`
2. Check [console.groq.com](https://console.groq.com) for API key validity and rate limits
3. Check `GROQ_MODEL=llama-3.3-70b-versatile` is a valid model name

**Note:** The fallback works — users still receive digests. Content quality is lower but delivery is unblocked.

---

### Symptom: Learning lessons not generating
```
LESSON_GEN | FAILED | topic=... module=... | ...
```

**Check:**
1. `GROQ_API_KEY` is set
2. Module exists in `learning_modules` (run `/api/learning/seed` if needed)
3. Look for `LESSON_GEN | FAILED` in logs with `exc_info=True` for the actual exception

**Note:** Fallback lessons are delivered when Groq fails — users still receive something.

---

## Database Errors

### Symptom: `alembic upgrade head` fails
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Fix:**
1. Verify PostgreSQL is running
2. Check `DATABASE_URL` in `.env` — format: `postgresql://user:pass@host:port/dbname`
3. Verify the database exists: `psql -l | grep mslearndigest`
4. Create if missing: `createdb mslearndigest`

---

### Symptom: `alembic upgrade head` runs but tables still missing
**Fix:** Alembic uses `sqlalchemy.url` from `alembic.ini` during direct CLI calls. Make sure your `DATABASE_URL` environment variable is exported or the `alembic.ini` is updated.

```bash
# Option 1: Export env var
export DATABASE_URL=postgresql://user:pass@localhost:5432/mslearndigest
alembic upgrade head

# Option 2: Run with env file (if python-dotenv installed)
```

---

### Symptom: `relation "catalog_cache" does not exist`
**Cause:** Migration not applied.

**Fix:**
```bash
cd backend
alembic upgrade head
```

---

### Symptom: `relation "user_phase_subscriptions" does not exist`
**Cause:** Migration `h8i9j0k1l2m3` not applied.

**Fix:**
```bash
alembic upgrade head
```

---

## Digest Issues

### Symptom: No digests generated — `status: "no_content"` for all users

**Diagnosis:**
```bash
GET /api/admin/catalog-cache/stats
```

If `total_cached = 0`:
```bash
POST /api/admin/catalog-sync
```

If `total_cached > 0` but no matches:
```bash
POST /api/admin/catalog-cache/preview
{"topic_slugs": ["azure"], "frequency": "weekly"}
```

**Common causes:**
1. `catalog_cache` is empty — run sync first
2. User's topic subscriptions don't match any catalog products/subjects
3. Frequency window too narrow — try a wider window (`monthly` to test)
4. Catalog data is old — items were last modified before the frequency window

---

### Symptom: Digest not sent on expected day/time

**Check:**
```bash
GET /api/admin/debug/onboarding
```

Verify `preferences_exist: true` and `can_receive_digest: true`.

**Common causes:**
1. `is_onboarded = false` — auto-healed by the debug endpoint
2. Timezone mismatch — delivery time stored in user's timezone, converted to UTC
3. Delivery day mismatch — `delivery_day` is 0=Monday … 6=Sunday
4. `catalog_cache` was empty at the time of dispatch

---

### Symptom: Team newsletter not sent

**Check:**
1. Is the newsletter active? `GET /api/teams/{id}/newsletter` → `is_active: true`
2. Are there accepted members? → `members` array with `status: "accepted"`
3. Is `catalog_cache` populated?

---

## Scheduler Issues

### Symptom: Jobs not running
**Check:** Verify APScheduler started successfully in logs:
```
Scheduler started: catalog_sync daily at 02:00 UTC, digest_dispatch hourly, learning_dispatch hourly.
```

If not seen, check for startup exceptions in logs.

**Note:** APScheduler runs in-process. If the backend process crashes, all jobs stop. Monitor the process and restart as needed.

---

### Symptom: Catalog sync failing intermittently
```
CATALOG | ReadTimeout fetching modules
```

**Cause:** MS Learn Catalog API is slow (the full catalog is 40MB+ for unfiltered requests).

**Fix:** The application uses filtered requests (`?type=modules` and `?type=learningPaths` separately) which are much smaller. If still timing out, the `httpx` timeout is set at 120 seconds — try increasing or check network conditions.

---

## Learning Engine Issues

### Symptom: Learning Center shows "Setup Required" banner
**Cause:** `learning_topics` table is empty.

**Fix:**
```bash
POST /api/learning/seed
```

Or call `GET /api/learning/status` — it auto-seeds if empty.

---

### Symptom: Phase selection not working — all modules delivered
**Check:** Verify `user_phase_subscriptions` rows exist:
```sql
SELECT * FROM user_phase_subscriptions WHERE user_id = '<user_uuid>';
```

If empty but `is_full_track=false`, try resubscribing via `PATCH /api/learning/subscribe/{topic_id}/phases`.

---

### Symptom: Learning lessons stopped advancing
**Check `user_learning_subscriptions`:**
```sql
SELECT current_module_sequence, total_lessons_sent, status, last_sent_at
FROM user_learning_subscriptions
WHERE user_id = '<user_uuid>';
```

- `status = "completed"` → track is finished
- `status = "active"` + `last_sent_at` very recent → not yet due (check frequency delta)
- `current_module_sequence > total_modules` → data inconsistency, try resubscribing

---

## Frontend Build Failures

### Symptom: `npm run build` fails with module not found

**Fix:**
```bash
cd frontend
npm install
npm run build
```

### Symptom: Google login button missing / non-functional
**Check `frontend/.env`:**
```
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

The console will show `❌ Google OAuth configuration is MISSING` if not set.

### Symptom: API calls fail with CORS errors
**Check:**
1. `FRONTEND_URL=http://localhost:5173` in backend `.env`
2. `VITE_API_URL=http://localhost:8000` in `frontend/.env`
3. Backend is running on port 8000

---

## General Debugging Tips

1. **Check logs first** — all significant events are logged to stdout with structured format
2. **Use admin endpoints** — the admin panel covers most diagnostic scenarios
3. **Check `sync_metadata`** — the `GET /api/admin/catalog-cache/stats` endpoint shows the last sync result
4. **Verify environment** — most issues trace back to a missing or incorrect `.env` variable
5. **Test in isolation** — use `POST /api/admin/test/send-my-digest` to test the full digest pipeline for your account
