# Email Delivery Testing Guide

Complete end-to-end verification workflow for the MS Learn Digest email pipeline.

---

## Prerequisites

### 1. Gmail App Password Setup

**CRITICAL:** Gmail blocks regular passwords when sending via SMTP. You **must** use an App Password.

#### Steps to generate an App Password:

1. Go to https://myaccount.google.com/
2. Click **Security** in the left sidebar
3. Enable **2-Step Verification** (required for App Passwords)
4. Once 2FA is enabled, search for **"App passwords"** in the security page
5. Generate a new App Password:
   - Name: `MS Learn Digest`
   - Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)
6. Paste this password into your `.env` file

#### Common Gmail SMTP Issues:

| Error | Cause | Fix |
|-------|-------|-----|
| `smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')` | Using account password instead of App Password | Generate App Password (see steps above) |
| `smtplib.SMTPConnectError` | Port 587 blocked by firewall | Check firewall rules / try different network |
| `socket.timeout` | No response from smtp.gmail.com | Check internet connectivity |
| `smtplib.SMTPRecipientsRefused` | Invalid recipient email | Verify email address is correct |

---

## Environment Configuration

### Required `.env` Variables

```bash
# ── SMTP (Gmail) ──
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password  # NOT your Google account password!

# ── Frontend ──
FRONTEND_URL=http://localhost:5173

# ── Application ──
APP_ENV=development
ADMIN_ENABLED=true
```

**Restart the backend** after changing `.env`:
```bash
# Terminal 1 — stop and restart backend
cd backend
uvicorn app.main:app --reload
```

---

## Testing Workflow

### Step 1: Start the Application

```bash
# Terminal 1 — Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Interactive API Docs: http://localhost:8000/docs
- Admin Testing Panel: http://localhost:5173/admin/testing

---

### Step 2: Navigate to Admin Testing Panel

1. Open your browser: http://localhost:5173
2. **Log in via Google OAuth** (required to access protected routes)
3. Click **"Admin Testing"** in the left sidebar
4. You should see 6 test sections:
   - SMTP Configuration
   - Test SMTP Connection
   - Send Plain Test Email
   - Generate Test Digest
   - Preview Digest HTML
   - Send Full Test Digest

---

### Step 3: Verify SMTP Configuration

**Action:** Click **"Load Config"**

**Expected Result:**
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_email": "your-email@gmail.com",
  "smtp_password": "xxxx************",
  "app_env": "development",
  "frontend_url": "http://localhost:5173"
}
```

**What to Check:**
- ✅ `smtp_email` shows your Gmail address
- ✅ `smtp_password` shows `(set)` or partially redacted value
- ❌ If `smtp_password` shows `(not set)`, check your `.env` file

---

### Step 4: Test SMTP Connection

**Action:** Click **"Test Connection"**

**Expected Result:**
```json
{
  "smtp_connection": "success",
  "message": "SMTP connection and authentication succeeded.",
  "detail": "server=smtp.gmail.com:587 user=your-email@gmail.com",
  "config": {
    "server": "smtp.gmail.com",
    "port": 587,
    "email": "your-email@gmail.com"
  }
}
```

**What This Tests:**
- Opens TCP connection to `smtp.gmail.com:587`
- Sends `EHLO` handshake
- Negotiates `STARTTLS` encryption
- Authenticates with your App Password
- **Does NOT send any email**

**Backend Logs:**
```
[timestamp] SMTP_TEST | START | server=smtp.gmail.com:587 user=your-email@gmail.com
[timestamp] SMTP_TEST | EHLO OK
[timestamp] SMTP_TEST | STARTTLS OK
[timestamp] SMTP_TEST | AUTH OK | user=your-email@gmail.com
[timestamp] SMTP_TEST | SUCCESS
```

#### If This Fails:

**Error: Authentication failed**
- Cause: Using Google account password instead of App Password
- Fix: Generate an App Password at https://myaccount.google.com/apppasswords

**Error: Connection timeout**
- Cause: Port 587 blocked or no internet connectivity
- Fix: Check firewall / try a different network

---

### Step 5: Send Plain Test Email

**Action:**
1. Enter your email in **"Recipient Email"** field
2. Click **"Send Test Email"**

**Expected Result:**
```json
{
  "status": "sent",
  "recipient": "your-email@gmail.com",
  "message": "Email delivered to your-email@gmail.com.",
  "sent_at": "2026-06-03T14:23:45.678Z"
}
```

**Check Your Gmail Inbox:**
- Subject: `✅ MS Learn Digest — SMTP Test Email`
- Body: Confirms SMTP connection, authentication, and delivery all succeeded
- Sender: `MS Learn Digest <your-email@gmail.com>`

**Backend Logs:**
```
[timestamp] EMAIL_SEND | START | to=your-email@gmail.com subject='✅ MS Learn Digest — SMTP Test Email'
[timestamp] EMAIL_SEND | SUCCESS | to=your-email@gmail.com
```

**What This Tests:**
- End-to-end SMTP delivery
- HTML rendering in Gmail
- Sender/recipient headers

---

### Step 6: Generate Test Digest

**Action:** Click **"Generate Digest"**

**Expected Result:**
```json
{
  "status": "generated",
  "digest_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Test Digest — MS Learn Weekly Update",
  "item_count": 3,
  "preview_url": "http://localhost:5173/digest/550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-06-03T14:25:12.345Z"
}
```

**What This Does:**
- Generates a digest using hardcoded sample content:
  - "Build Multi-Agent Applications Using Azure AI Foundry"
  - "Implement Real-Time Data Pipelines with Microsoft Fabric"
  - "Secure Your Cloud Environment with Microsoft Copilot for Security"
- Persists the digest in PostgreSQL (`digests` table)
- Returns the `digest_id` for retrieval

**Database Verification:**
```sql
SELECT id, title, digest_type, status, created_at
FROM digests
WHERE title LIKE '%Test Digest%'
ORDER BY created_at DESC
LIMIT 1;
```

**Click the "View Digest in Dashboard" link** to see the digest in the UI.

---

### Step 7: Preview Digest HTML

**Action:** Click **"Preview in Browser"**

**Expected Result:**
- Opens a new browser tab
- Displays a beautiful HTML newsletter with:
  - Blue gradient header: "Your Weekly MS Learn Digest — Test"
  - Topic pills: Azure AI Foundry, Microsoft Fabric, Copilot, Security
  - 2 sections:
    - **New Modules** (2 items)
    - **Learning Paths** (1 item)
  - Each item shows:
    - Title (clickable link to Microsoft Learn)
    - Difficulty badge (Beginner/Intermediate/Advanced)
    - Topic badges
    - Duration
    - Summary
    - "Why it matters" callout box
    - Key takeaways bullet list
    - Audience tags
    - "Read Full Module" CTA button
  - Footer with "Manage Preferences" link

**What This Tests:**
- Jinja2 template rendering
- HTML email structure
- Visual layout and responsive design
- Production-quality newsletter appearance

---

### Step 8: Send Full Test Digest

**Action:**
1. Enter your email in **"Recipient Email"** field
2. (Optional) Change **"User Name"** to personalize greeting
3. Click **"Send Full Digest"**

**Expected Result:**
```json
{
  "status": "sent",
  "recipient": "your-email@gmail.com",
  "digest_id": "660e9511-f30c-52e5-b827-557766551111",
  "message": "Email delivered to your-email@gmail.com.",
  "sent_at": "2026-06-03T14:28:33.456Z"
}
```

**Check Your Gmail Inbox:**
- Subject: `📚 MS Learn Digest — Your Weekly Learning Update (Test)`
- Body: Full HTML newsletter identical to the preview
- Sender: `MS Learn Digest <your-email@gmail.com>`

**Backend Logs:**
```
[timestamp] EMAIL_SEND | START | to=your-email@gmail.com subject='📚 MS Learn Digest — Your Weekly Learning Update (Test)'
[timestamp] EMAIL_SEND | SUCCESS | to=your-email@gmail.com
[timestamp] ADMIN | send-test-digest | SUCCESS | digest_id=660e9511-... to=your-email@gmail.com
```

**Database Verification:**
```sql
SELECT id, title, status, sent_at, recipient_count
FROM digests
WHERE status = 'sent'
ORDER BY sent_at DESC
LIMIT 1;
```

Should show:
- `status = 'sent'`
- `sent_at` = recent timestamp
- `recipient_count = 1`

---

### Step 9: View Digest History

**Action:**
1. Navigate to **Dashboard** (left sidebar)
2. Scroll to **"Digest History"** section

**Expected Result:**
- All generated and sent test digests appear in chronological order
- Each digest shows:
  - Title
  - Date sent
  - Number of items
  - Status badge (generated, sent, failed)
  - Click the 📄 icon to view full digest content

**Click a Digest:**
- Navigates to `/digest/{digest_id}`
- Displays the complete HTML newsletter in an iframe
- Shows metadata: digest type, sent date, topic tags

---

## Success Criteria Checklist

Use this checklist to confirm the entire pipeline works end-to-end:

- [ ] **Step 3:** SMTP config shows credentials loaded correctly
- [ ] **Step 4:** "Test Connection" returns `smtp_connection: success`
- [ ] **Step 5:** Plain test email arrives in Gmail inbox within 30 seconds
- [ ] **Step 6:** Test digest persists in database with `status=generated`
- [ ] **Step 7:** Preview shows a production-quality HTML newsletter
- [ ] **Step 8:** Full digest email arrives in Gmail inbox within 30 seconds
- [ ] **Step 9:** All digests appear in Dashboard history
- [ ] **Database:** `digests` table contains test records with `status=sent`
- [ ] **Logs:** Backend shows `EMAIL_SEND | SUCCESS` for all sent emails

---

## API Endpoints Reference

All admin endpoints are available at `/api/admin/*`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/config` | Show SMTP config (password redacted) |
| `GET` | `/api/admin/smtp-check` | Test SMTP connection + auth (no email sent) |
| `POST` | `/api/admin/send-test-email` | Send plain confirmation email |
| `POST` | `/api/admin/generate-test-digest` | Generate + persist sample digest |
| `POST` | `/api/admin/send-test-digest` | Generate + email + persist digest |
| `GET` | `/api/admin/preview-digest` | Render digest HTML in browser |

### Example cURL Commands

**Test SMTP Connection:**
```bash
curl http://localhost:8000/api/admin/smtp-check
```

**Send Test Email:**
```bash
curl -X POST http://localhost:8000/api/admin/send-test-email \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@gmail.com"}'
```

**Send Full Digest:**
```bash
curl -X POST http://localhost:8000/api/admin/send-test-digest \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@gmail.com", "user_name": "Learner"}'
```

---

## Troubleshooting

### Gmail Blocks Email Delivery

**Symptom:** `SMTPAuthenticationError: Username and Password not accepted`

**Cause:** Using Google account password instead of App Password.

**Fix:**
1. Go to https://myaccount.google.com/apppasswords
2. Generate a new App Password
3. Update `SMTP_PASSWORD` in `.env`
4. Restart backend

---

### Email Never Arrives

**Symptom:** API returns success but email doesn't appear in inbox.

**Check:**
1. **Gmail Spam folder** — test emails may be flagged
2. **Gmail "All Mail"** — sometimes emails skip inbox
3. **Backend logs** — confirm `EMAIL_SEND | SUCCESS` appears
4. **Wait 2 minutes** — delivery can be delayed

**Gmail Delivery Delays:**
- First email from a new sender: 30-120 seconds
- Subsequent emails: 5-30 seconds

---

### SMTP Connection Timeout

**Symptom:** `socket.timeout: timed out`

**Cause:** Port 587 blocked by firewall or no internet.

**Fix:**
1. Check firewall allows outbound connections to `smtp.gmail.com:587`
2. Verify internet connectivity: `ping smtp.gmail.com`
3. Try a different network (corporate firewalls often block SMTP)

---

### "Admin endpoints are disabled"

**Symptom:** HTTP 403 Forbidden on `/api/admin/*`

**Cause:** `ADMIN_ENABLED=false` or `APP_ENV=production` in `.env`.

**Fix:**
```bash
# .env
APP_ENV=development
ADMIN_ENABLED=true
```

Restart backend.

---

## Security Notice

**⚠️ WARNING:** The `/api/admin/*` endpoints are intentionally unauthenticated for local development convenience.

### In Production:

1. **Option 1 (Recommended):** Disable admin endpoints entirely
   ```bash
   ADMIN_ENABLED=false
   ```

2. **Option 2:** Protect with an API key
   ```python
   from fastapi import Header, HTTPException
   
   def verify_admin_key(x_admin_key: str = Header(...)):
       if x_admin_key != settings.ADMIN_API_KEY:
           raise HTTPException(status_code=401, detail="Invalid admin key")
   ```

3. **Option 3:** Remove `/api/admin/*` routes entirely from production builds

---

## Next Steps

Once all tests pass:

1. **Test with Real Content:**
   - Run the catalog sync job: triggers automatically at 2 AM UTC
   - Or manually trigger via scheduler
   - Verify content appears in `content` table

2. **Test User Digest Generation:**
   - Create a user account
   - Subscribe to topics in Preferences
   - Configure delivery schedule
   - Wait for scheduled digest or manually invoke `generate_and_send_for_user()`

3. **Test Team Newsletter:**
   - Create a team
   - Invite members
   - Configure newsletter with topics
   - Wait for scheduled delivery

4. **Monitor Production Logs:**
   ```bash
   tail -f backend/logs/app.log | grep EMAIL_SEND
   ```

---

## Support

If you encounter issues not covered in this guide:

1. Check backend logs for detailed error traces
2. Verify all environment variables are set correctly
3. Confirm Gmail App Password is correct (not account password)
4. Test SMTP connection independently using `telnet`:
   ```bash
   telnet smtp.gmail.com 587
   EHLO localhost
   STARTTLS
   ```

For Gmail-specific issues, refer to:
- https://support.google.com/accounts/answer/185833 (App Passwords)
- https://support.google.com/mail/answer/7126229 (SMTP settings)
