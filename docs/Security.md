# Security Documentation
## MS Learn Digest

---

## Authentication

### JWT (JSON Web Token)

| Property | Value |
|---|---|
| **Algorithm** | HS256 |
| **Expiry** | 72 hours (configurable via `JWT_EXPIRATION_HOURS`) |
| **Secret** | `JWT_SECRET_KEY` — loaded from environment variable |
| **Library** | `python-jose` |
| **Storage** | `localStorage` on the client |
| **Transport** | `Authorization: Bearer <token>` header on all API calls |

**Token payload:**
```json
{
  "sub": "<user_uuid>",
  "exp": 1720000000
}
```

**Validation dependency (`security.py`):**
```python
def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> str:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(401, "Invalid token payload")
    return user_id
```

---

### Google OAuth 2.0

- Standard OAuth 2.0 authorization code flow
- Authorization code exchanged server-side (never exposed to client)
- Google access token used only to fetch user profile — never stored
- `google_id` stored in `users` table for future logins
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are environment variables only

---

### Email Magic-Link

| Property | Value |
|---|---|
| **Token generation** | `secrets.token_hex(32)` — 256-bit cryptographically random |
| **Token format** | 64-character hex string |
| **Storage** | SHA-256 hash stored in `email_login_tokens.token_hash`; raw token never persisted |
| **Expiry** | 15 minutes (configurable via `EMAIL_LOGIN_TOKEN_EXPIRY_MINUTES`) |
| **Single-use** | `used_at` set on first verification — subsequent attempts return 401 |
| **Rate limiting** | Max 5 requests per email per hour (enforced in `EmailAuthService._check_rate_limit()`) |

**Hash function:**
```python
def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
```

**Why hash-only storage:** If the `email_login_tokens` table is compromised, attackers cannot use the stored hashes to authenticate — they need the original raw tokens which were only ever emailed.

---

## Authorization

### Protected vs. Public Endpoints

**Protected (JWT required):**
- All `/api/users/*` endpoints
- All `/api/topics/my`, `/api/topics/subscribe`, `/api/topics/onboard`
- All `/api/digests/*`
- All `/api/learning/subscribe*`, `/api/learning/my`, `/api/learning/progress/*`, `/api/learning/analytics`
- All `/api/teams/*` (except public invite preview and decline)
- Most `/api/admin/*` endpoints

**Public (no auth):**
- `GET /api/auth/providers`
- `GET /api/topics/` (flat list)
- `GET /api/topics/tree`
- `GET /api/topics/roots`
- `GET /api/topics/{id}/children`
- `GET /api/learning/topics` and `GET /api/learning/topics/*`
- `GET /api/learning/status`
- `POST /api/learning/seed`
- `GET /api/teams/invite/{token}` (preview)
- `POST /api/teams/invite/{token}/decline`
- `GET /health`

### Team Admin Authorization

Team-modifying operations check admin status explicitly:
```python
if not repo.is_admin(team_id, UUID(user_id)):
    raise HTTPException(status_code=403, detail="Only team admins can ...")
```

`TeamRepository.is_admin()`:
```python
def is_admin(self, team_id: UUID, user_id: UUID) -> bool:
    team = self.db.query(Team).filter(Team.id == team_id).first()
    return team is not None and team.admin_id == user_id
```

---

## Input Validation

All request bodies are validated by **Pydantic v2** schemas:

- `email` fields: regex-validated in `auth.py` (`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)
- `token` fields: minimum 32 characters enforced
- `delivery_time`: format `HH:MM` validated, hour/minute range checked
- `frequency`: must be one of `{daily, weekly, biweekly, monthly}` (exact set)
- `topic_ids`: typed as `List[UUID]` — non-UUID inputs rejected with 422
- `selected_phases`: typed as `List[str]` with non-empty check when `is_full_track=false`

---

## CORS Configuration

Configured in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],   # exact origin only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`settings.FRONTEND_URL` defaults to `http://localhost:5173`. In production, set this to your actual domain. **No wildcard origins.**

---

## Admin Endpoint Security

Admin endpoints are guarded by `_check_admin_enabled()`:
```python
def _check_admin_enabled():
    if settings.APP_ENV == "production" and not getattr(settings, "ADMIN_ENABLED", False):
        raise HTTPException(403, "Admin endpoints are disabled in production.")
```

To enable in production: `ADMIN_ENABLED=true` in `.env`. Default is enabled (`true`), so production deployments should explicitly set `APP_ENV=production` to activate the guard.

---

## Email Security

### SMTP
- Gmail STARTTLS (port 587) — encrypted in transit
- App Password required — not the account password
- Credentials only in environment variables — never in code

### Invitation Tokens
- `secrets.token_urlsafe(32)` — 256-bit cryptographically random, URL-safe characters
- Stored raw in `team_invitations.token` — lookup is O(1) via index
- Configurable expiry (default: 72 hours per `INVITATION_EXPIRY_HOURS`)
- Status lifecycle: `pending → accepted | declined | expired`
- Re-sending an invitation expires the old token and creates a new one

---

## Secrets Management

All secrets are environment variables:

| Secret | Environment Variable | Usage |
|---|---|---|
| Database credentials | `DATABASE_URL` | PostgreSQL connection string |
| Gmail password | `SMTP_PASSWORD` | SMTP authentication |
| Google OAuth secret | `GOOGLE_CLIENT_SECRET` | Token exchange |
| Groq API key | `GROQ_API_KEY` | AI content generation |
| JWT signing key | `JWT_SECRET_KEY` | Token signing and verification |

**Rules:**
- `.env` file is listed in `.gitignore` (not committed to source control)
- `.env.example` contains only placeholder values
- Pydantic Settings loads variables at startup — missing required values will surface immediately
- No secrets are logged — passwords are masked in admin config endpoint

---

## Database Security

- All user IDs are UUIDs (v4 random) — not sequential integers that can be guessed
- `ForeignKey(ondelete="CASCADE")` on user-owned data — deleting a user cascades all their data
- `ForeignKey(ondelete="SET NULL")` on digest references — digest history survives user deletion (for audit)
- Raw SQL is avoided in all business logic; ORM parameters are safe from SQL injection
- The one raw SQL use (`resolve_descendant_ids`) uses `sqlalchemy.text()` with UUID list construction from typed Python objects — not user-supplied strings

---

## Known Security Limitations

| Limitation | Notes |
|---|---|
| JWT in localStorage | Vulnerable to XSS if the application has XSS vulnerabilities. HTTPS + CSP headers mitigate this. |
| No token revocation | JWTs are valid until expiry (72h). There is no blocklist for compromised tokens. |
| No HTTPS enforcement | The application does not force HTTPS internally — this must be enforced at the reverse proxy / load balancer level. |
| No rate limiting on API endpoints (except magic-link) | API endpoints other than `/auth/email/request` have no rate limiting. |
| Admin endpoints accessible via JWT | Any valid JWT holder can call admin endpoints when `ADMIN_ENABLED=true` — there is no separate admin role check. |
| Invitation token stored in plain text | `team_invitations.token` is stored raw (not hashed), unlike the magic-link tokens. Acceptable risk given short expiry and URL-safe format. |
