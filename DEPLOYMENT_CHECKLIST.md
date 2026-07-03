# 🚀 MS Learn Digest — Complete Deployment Checklist

This checklist covers **everything** you need to deploy MS Learn Digest from scratch to **Render (backend)** and **Vercel (frontend)**, with **zero hardcoded URLs** in source code.

---

## ✅ Prerequisites

Before you start:

- [ ] GitHub repository with your project code
- [ ] Google account (for OAuth setup)
- [ ] Gmail account with App Password enabled (for SMTP)
- [ ] Groq API key ([console.groq.com](https://console.groq.com))
- [ ] PostgreSQL database (Render, Neon, or other hosted provider)
- [ ] Render account ([render.com](https://render.com))
- [ ] Vercel account ([vercel.com](https://vercel.com))

---

## 🗄 Step 1: Database Setup (Neon / Render PostgreSQL)

### Option A: Neon (Recommended — Free Tier + Generous Limits)

1. Go to [neon.tech](https://neon.tech) and create a project
2. Copy the connection string (format: `postgresql://user:password@host/database?sslmode=require`)
3. Save it as `DATABASE_URL`

### Option B: Render PostgreSQL

1. Go to Render Dashboard → New → PostgreSQL
2. Pick a name, region, and plan (Free tier available)
3. Once created, copy the **External Database URL**
4. Save it as `DATABASE_URL`

---

## 🔐 Step 2: Google OAuth 2.0 Setup

### 2.1 Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to: **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Name: `MS Learn Digest`

### 2.2 Configure Authorized JavaScript Origins

Add **both** local and production frontend URLs:

```
http://localhost:5173
https://ms-learn-digest-git-learnings-kiro9898.vercel.app
```

### 2.3 Configure Authorized Redirect URIs

Add **both** local and production backend callback URLs:

```
http://localhost:8000/auth/google/callback
https://ms-learn-digest.onrender.com/auth/google/callback
```

### 2.4 Save Credentials

- Copy the **Client ID** → save as `GOOGLE_CLIENT_ID`
- Copy the **Client Secret** → save as `GOOGLE_CLIENT_SECRET`

---

## 📧 Step 3: Gmail SMTP Setup

1. Enable **2-Factor Authentication** on your Gmail account
2. Go to [Google Account → App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new App Password:
   - App: Mail
   - Device: Custom (enter "MS Learn Digest")
4. Copy the **16-character code** (ignore spaces) → save as `SMTP_PASSWORD`
5. Save your Gmail address → `SMTP_EMAIL`

---

## 🤖 Step 4: Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up / log in
3. Navigate to **API Keys**
4. Create a new key → copy it → save as `GROQ_API_KEY`

---

## 🔧 Step 5: Backend Deployment (Render)

### 5.1 Create a New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New → Web Service**
3. Connect your GitHub repository
4. Select **MS-Learn-Digest** repo

### 5.2 Configure Build Settings

| Field | Value |
|---|---|
| **Name** | `ms-learn-digest` (or your choice) |
| **Region** | Choose closest to your users |
| **Branch** | `main` (or `master`) |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && alembic upgrade head` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free (or paid for production) |

### 5.3 Set Environment Variables

Go to **Environment** tab and add **all** of these:

#### Required Variables

| Variable | Example Value | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | From Step 1 (Neon / Render Postgres) |
| `GOOGLE_CLIENT_ID` | `123456.apps.googleusercontent.com` | From Step 2 |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-abcd1234...` | From Step 2 |
| `GOOGLE_REDIRECT_URI` | `https://ms-learn-digest.onrender.com/auth/google/callback` | ⚠️ **MUST** match Render service URL |
| `FRONTEND_URL` | `https://ms-learn-digest-git-learnings-kiro9898.vercel.app` | ⚠️ Vercel deployment URL (get from Step 6) |
| `ALLOWED_ORIGINS` | `https://ms-learn-digest-git-learnings-kiro9898.vercel.app` | Same as FRONTEND_URL, or comma-separated for multi-origin |
| `SMTP_SERVER` | `smtp.gmail.com` | Gmail SMTP |
| `SMTP_PORT` | `587` | Gmail SMTP port |
| `SMTP_EMAIL` | `youremail@gmail.com` | From Step 3 |
| `SMTP_PASSWORD` | `abcd efgh ijkl mnop` | Gmail App Password (no spaces) |
| `GROQ_API_KEY` | `gsk_...` | From Step 4 |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `JWT_SECRET_KEY` | (generate a random 32+ char string) | Use a password generator |
| `JWT_ALGORITHM` | `HS256` | Signing algorithm |
| `JWT_EXPIRATION_HOURS` | `72` | Token lifetime |
| `APP_NAME` | `MS Learn Digest` | App name for logs |
| `APP_ENV` | `production` | ⚠️ **Set to production** |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `ADMIN_ENABLED` | `false` | ⚠️ **Disable admin panel in prod** |

### 5.4 Deploy

1. Click **Create Web Service**
2. Wait for the first deploy to complete (~3-5 minutes)
3. Render will show you the service URL: `https://ms-learn-digest.onrender.com`
4. **Copy this URL** — you'll need it for frontend and Google OAuth config

### 5.5 Verify Backend is Running

Visit: `https://ms-learn-digest.onrender.com/health`

Expected response:
```json
{
  "status": "ok",
  "env": "production",
  "frontend_url": "https://ms-learn-digest-git-learnings-kiro9898.vercel.app"
}
```

---

## 🎨 Step 6: Frontend Deployment (Vercel)

### 6.1 Import Project to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New → Project**
3. Import your GitHub repository
4. Select **MS-Learn-Digest** repo

### 6.2 Configure Build Settings

| Field | Value |
|---|---|
| **Framework Preset** | Vite |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` (auto-detected) |
| **Output Directory** | `dist` (auto-detected) |
| **Install Command** | `npm install` (auto-detected) |

### 6.3 Set Environment Variables

Click **Environment Variables** and add:

| Variable | Value | Notes |
|---|---|---|
| `VITE_API_URL` | `https://ms-learn-digest.onrender.com` | ⚠️ **MUST** be your Render backend URL from Step 5 |
| `VITE_GOOGLE_CLIENT_ID` | `123456.apps.googleusercontent.com` | Same as backend `GOOGLE_CLIENT_ID` |

### 6.4 Deploy

1. Click **Deploy**
2. Wait for build to complete (~2-3 minutes)
3. Vercel assigns a URL: `https://ms-learn-digest-git-learnings-kiro9898.vercel.app`
4. **Copy this URL**

### 6.5 Update Backend Environment Variables

Go back to **Render** → your backend service → **Environment** tab:

1. Update `FRONTEND_URL` to your Vercel URL:
   ```
   FRONTEND_URL=https://ms-learn-digest-git-learnings-kiro9898.vercel.app
   ```

2. Update `ALLOWED_ORIGINS` to your Vercel URL:
   ```
   ALLOWED_ORIGINS=https://ms-learn-digest-git-learnings-kiro9898.vercel.app
   ```

3. Click **Save Changes** → Render will auto-redeploy the backend

---

## 🔄 Step 7: Update Google OAuth with Final URLs

Go back to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials):

### 7.1 Authorized JavaScript Origins

Ensure **both** are present:
```
http://localhost:5173
https://ms-learn-digest-git-learnings-kiro9898.vercel.app
```

### 7.2 Authorized Redirect URIs

Ensure **both** are present:
```
http://localhost:8000/auth/google/callback
https://ms-learn-digest.onrender.com/auth/google/callback
```

Click **Save**.

---

## 🧪 Step 8: Test the Deployment

### 8.1 Frontend Health Check

Visit: `https://ms-learn-digest-git-learnings-kiro9898.vercel.app`

- [ ] Landing page loads
- [ ] Google Sign-In button visible
- [ ] Email Sign-In form visible
- [ ] No console errors in browser DevTools

### 8.2 Backend Health Check

Visit: `https://ms-learn-digest.onrender.com/health`

- [ ] Returns `{"status": "ok", "env": "production"}`

### 8.3 Google OAuth Flow

1. Click **Continue with Google**
2. Complete Google sign-in
3. You should be redirected to `/onboarding` or `/dashboard`
4. Check browser DevTools → Network tab:
   - [ ] `POST /api/auth/google` → 200 OK
   - [ ] `GET /api/users/me` → 200 OK

### 8.4 Email Magic-Link Flow

1. Click **Continue with Email**
2. Enter your email address
3. Check your inbox for the magic link
4. Click the link
5. You should be signed in and redirected to dashboard

### 8.5 Core Features

- [ ] Topic selection works
- [ ] Preferences can be updated
- [ ] Digest history loads (if any exist)
- [ ] Teams page loads
- [ ] Learning Center page loads

### 8.6 Test Email Delivery (Admin Panel)

**⚠️ Only if ADMIN_ENABLED=true:**

1. Visit: `https://ms-learn-digest.onrender.com/docs`
2. Use the `/api/admin/send-test-email` endpoint
3. Check your inbox for the test email

---

## 📊 Step 9: Monitoring & Logs

### Render Logs

- Go to Render Dashboard → your service → **Logs** tab
- Check for startup errors, CORS issues, or missing env vars

### Vercel Logs

- Go to Vercel Dashboard → your project → **Deployments** → latest → **Logs**
- Check build logs for errors

### Browser Console

- Open DevTools → Console tab
- Look for:
  - ✅ `[API Client] baseURL=https://ms-learn-digest.onrender.com`
  - ✅ `✅ Google OAuth configuration loaded successfully.`
  - ❌ Any `VITE_*` missing errors → add them in Vercel

---

## 🔁 Step 10: Local Development After Deployment

Your local `.env` should look like this for **local dev**:

```bash
# Local Development Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/mslearndigest
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173
VITE_API_URL=http://localhost:8000

# (All other vars same as production)
```

**Never change source code** when switching between local and production.  
Only environment variables change.

---

## 📝 Summary: Environment Variables by Service

### Backend (Render)

| Variable | Local | Production |
|---|---|---|
| `DATABASE_URL` | `postgresql://...@localhost...` | `postgresql://...@neon.tech...` |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/auth/google/callback` | `https://ms-learn-digest.onrender.com/auth/google/callback` |
| `FRONTEND_URL` | `http://localhost:5173` | `https://ms-learn-digest-git-learnings-kiro9898.vercel.app` |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | `https://ms-learn-digest-git-learnings-kiro9898.vercel.app` |
| `APP_ENV` | `development` | `production` |
| `ADMIN_ENABLED` | `true` | `false` |

### Frontend (Vercel)

| Variable | Local | Production |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | `https://ms-learn-digest.onrender.com` |
| `VITE_GOOGLE_CLIENT_ID` | (same in both) | (same in both) |

---

## 🐛 Troubleshooting

### Issue: "VITE_API_URL is not set" error in browser console

**Fix:** Add `VITE_API_URL` to Vercel environment variables and redeploy.

### Issue: CORS error (blocked by CORS policy)

**Fix:** Ensure `ALLOWED_ORIGINS` on Render backend includes your Vercel frontend URL **exactly** (no trailing slash).

### Issue: Google OAuth callback fails with redirect_uri_mismatch

**Fix:** Double-check that **both** these URLs are registered in Google Cloud Console:
- `http://localhost:8000/auth/google/callback`
- `https://ms-learn-digest.onrender.com/auth/google/callback`

### Issue: Magic-link email not received

**Fix:**
1. Check Render logs for SMTP errors
2. Verify `SMTP_PASSWORD` is the Gmail App Password (not account password)
3. Test SMTP connection: `https://ms-learn-digest.onrender.com/api/admin/smtp-check`

### Issue: Database connection fails on Render

**Fix:**
1. Check `DATABASE_URL` format includes `?sslmode=require` for Neon
2. Verify database is publicly accessible (not firewalled)
3. Check Render logs for connection error details

### Issue: Scheduler not running (no digests sent)

**Fix:**
1. Check Render logs for scheduler startup messages
2. Ensure at least one user has subscribed to topics
3. Verify `GROQ_API_KEY` is valid

---

## ✅ Final Verification Checklist

- [ ] Backend health endpoint returns 200 OK
- [ ] Frontend loads without console errors
- [ ] Google OAuth sign-in works end-to-end
- [ ] Email magic-link sign-in works end-to-end
- [ ] User can select topics and update preferences
- [ ] Test digest email is received
- [ ] CORS allows frontend → backend communication
- [ ] No hardcoded URLs remain in source code
- [ ] All secrets are in environment variables, not committed to git
- [ ] `.env` is in `.gitignore`
- [ ] `ADMIN_ENABLED=false` in production

---

## 🎉 Deployment Complete!

Your application is now live at:

- **Frontend:** https://ms-learn-digest-git-learnings-kiro9898.vercel.app
- **Backend API:** https://ms-learn-digest.onrender.com
- **API Docs:** https://ms-learn-digest.onrender.com/docs

No source code changes are needed between local and production — only environment variables.

**Next Steps:**
- Set up custom domains (optional)
- Enable auto-deploy on git push
- Monitor Render and Vercel logs
- Set up uptime monitoring (e.g., UptimeRobot)
- Add error tracking (e.g., Sentry)
