# Sequence Diagrams
## MS Learn Digest

---

## 1. Google Login Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant GO as Google OAuth
    participant BE as FastAPI Backend
    participant DB as PostgreSQL

    User->>FE: Click "Sign in with Google"
    FE->>GO: Redirect to OAuth consent screen\n(client_id, scope, redirect_uri)
    GO-->>User: Show consent screen
    User->>GO: Approve
    GO->>FE: Redirect to /auth/callback?code=<auth_code>
    FE->>BE: POST /api/auth/google {code, redirect_uri}
    BE->>GO: POST https://oauth2.googleapis.com/token\n{code, client_id, client_secret, redirect_uri}
    GO-->>BE: {access_token, ...}
    BE->>GO: GET https://www.googleapis.com/oauth2/v2/userinfo\nAuthorization: Bearer <access_token>
    GO-->>BE: {id, email, name, picture}
    BE->>DB: SELECT * FROM users WHERE google_id=? OR email=?
    alt New user
        BE->>DB: INSERT INTO users (google_id, email, name, avatar_url)
    else Existing user
        BE->>DB: UPDATE users SET name=?, avatar_url=?
    end
    BE-->>FE: {access_token: "<JWT>", token_type: "bearer"}
    FE->>FE: localStorage.setItem("token", JWT)
    FE->>BE: GET /api/users/me (Authorization: Bearer JWT)
    BE-->>FE: UserResponse {is_onboarded, preferences, ...}
    alt is_onboarded = false
        FE->>FE: Navigate to /onboarding
    else is_onboarded = true
        FE->>FE: Navigate to /dashboard
    end
```

---

## 2. Email Magic-Link Login Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant DB as PostgreSQL
    participant SMTP as Gmail SMTP

    User->>FE: Enter email address
    FE->>BE: POST /api/auth/email/request {email}
    BE->>DB: COUNT tokens WHERE email=? AND created_at >= now()-1h
    alt Rate limit exceeded (>= 5)
        BE-->>FE: 429 Too Many Requests
    else Within limit
        BE->>BE: raw_token = secrets.token_hex(32)
        BE->>BE: token_hash = SHA256(raw_token)
        BE->>DB: INSERT INTO email_login_tokens\n{email, token_hash, expires_at=now()+15min}
        BE->>SMTP: Send HTML email with link:\n{FRONTEND_URL}/auth/email/callback?token=<raw>
        SMTP-->>User: Magic link email
        BE-->>FE: {status: "sent", message: "..."}
    end

    User->>FE: Click link in email
    FE->>FE: Extract token from URL query param
    FE->>BE: POST /api/auth/email/verify {token}
    BE->>BE: token_hash = SHA256(token)
    BE->>DB: SELECT * FROM email_login_tokens WHERE token_hash=?
    alt Token not found
        BE-->>FE: 401 Invalid or expired login link
    else Token already used
        BE-->>FE: 401 Already used
    else Token expired
        BE-->>FE: 401 Expired
    else Valid
        BE->>DB: UPDATE email_login_tokens SET used_at=now()
        BE->>DB: SELECT * FROM users WHERE email=?
        alt New user
            BE->>DB: INSERT INTO users {email, name, auth_provider="email", email_verified=true}
        else Existing user
            BE->>DB: UPDATE users SET email_verified=true, last_login=now()
        end
        BE->>BE: JWT = create_access_token({sub: user_id})
        BE-->>FE: {access_token: JWT, token_type: "bearer"}
        FE->>FE: localStorage.setItem("token", JWT)
        FE->>FE: Navigate to /dashboard or /onboarding
    end
```

---

## 3. Topic Subscription Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant DB as PostgreSQL

    User->>FE: Opens Preferences or Onboarding
    FE->>BE: GET /api/topics/tree (no auth)
    BE->>DB: SELECT * FROM topics WHERE is_active=true ORDER BY level, name
    DB-->>BE: Flat list of all topics
    BE->>BE: Build nested tree (Python _build_tree())
    BE-->>FE: [{id, name, slug, children: [...], ...}]
    FE->>FE: Render TopicCardGrid component

    User->>FE: Select / deselect topic cards
    FE->>FE: selectedTopics state updated

    User->>FE: Click "Save" / "Complete Setup"
    FE->>BE: POST /api/topics/subscribe {topic_ids: [...]}
    BE->>DB: DELETE FROM user_subscriptions WHERE user_id=?
    loop Each topic_id
        BE->>DB: INSERT INTO user_subscriptions {user_id, topic_id}
    end
    BE->>DB: UPDATE users SET is_onboarded=true (if onboarding)
    BE-->>FE: [{id, user_id, topic_id, created_at, topic}...]
```

---

## 4. Digest Generation Flow

```mermaid
sequenceDiagram
    participant SCH as APScheduler (every 15 min)
    participant DG as DigestGenerator
    participant TR as TopicRepository
    participant DB as PostgreSQL
    participant GR as Groq API
    participant ES as EmailClient
    participant SMTP as Gmail SMTP

    SCH->>DB: Query users with subscriptions + preferences
    loop Each user with subscriptions
        DG->>DG: _is_due(frequency, delivery_day, utc_hour, current_time)
        alt Not due
            DG->>DG: Skip user
        else Due
            DG->>DB: Get user's UserSubscription rows
            DG->>TR: resolve_descendant_ids(topic_ids) — recursive CTE
            DB-->>DG: Expanded topic ID set
            DG->>DB: Build products_set + subjects_set from Topic.catalog_products/subjects
            DG->>DG: _lookback(frequency) → window_start datetime
            DG->>DB: SELECT * FROM catalog_cache\nWHERE last_modified >= window_start\nORDER BY last_modified DESC LIMIT 200
            DB-->>DG: Candidate items
            DG->>DG: Filter: keep items where products ∩ products_set OR subjects ∩ subjects_set
            alt No matching items
                DG->>DB: INSERT digest {status: "no_content"}
                DG->>DG: Skip email
            else Items matched
                DG->>DG: cache_key = SHA256(topic_slugs + freq + sorted_uids)[:16]
                alt cache_key in dispatch_cache
                    DG->>DG: Reuse Groq result (no API call)
                else Cache miss
                    DG->>GR: generate_digest(items, topic_names, frequency)
                    GR-->>DG: {executive_summary, items[{uid,summary,why_it_matters,key_takeaways}]}
                    DG->>DG: Store in dispatch_cache[cache_key]
                end
                DG->>DG: _render() — Jinja2 digest_email.html
                DG->>DB: INSERT digest + digest_items
                DG->>ES: send_email(recipient, subject, html)
                ES->>SMTP: STARTTLS + AUTH + SENDMAIL
                SMTP-->>ES: OK / Error
                ES-->>DG: True / False
                alt Sent
                    DG->>DB: UPDATE digest SET status="sent", sent_at=now()
                else Failed
                    DG->>DB: UPDATE digest SET status="failed"
                end
            end
        end
    end
```

---

## 5. Learning Track Enrollment Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant DB as PostgreSQL

    User->>FE: Opens Learning Center → click "Enrol in Track"
    FE->>BE: GET /api/learning/topics/{topic_id}/phases
    BE->>DB: SELECT DISTINCT phase_name, phase_number, COUNT(*) FROM learning_modules\nWHERE topic_id=? GROUP BY phase_name, phase_number
    DB-->>BE: [{phase_name, phase_number, module_count, difficulty_levels}]
    BE-->>FE: {topic_id, topic_name, phases: [...]}
    FE->>FE: Show PhaseSelector modal

    alt User selects "Full Track"
        User->>FE: Select "Full Track" + frequency → click Start
        FE->>BE: POST /api/learning/subscribe\n{topic_id, frequency, is_full_track: true, selected_phases: []}
    else User selects specific phases
        User->>FE: Select phases + frequency → click Start
        FE->>BE: POST /api/learning/subscribe\n{topic_id, frequency, is_full_track: false, selected_phases: ["Phase 1: Fundamentals", "Phase 3: Networking"]}
    end

    BE->>DB: SELECT FROM user_learning_subscriptions WHERE user_id=? AND topic_id=?
    alt No existing subscription
        BE->>DB: INSERT INTO user_learning_subscriptions\n{user_id, topic_id, frequency, is_full_track, current_module_sequence=1}
    else Existing subscription
        BE->>DB: UPDATE user_learning_subscriptions SET frequency=?, is_full_track=?
    end
    alt is_full_track = false
        BE->>DB: DELETE FROM user_phase_subscriptions WHERE subscription_id=?
        loop Each selected phase
            BE->>DB: INSERT INTO user_phase_subscriptions\n{subscription_id, phase_name, phase_number}
        end
        BE->>DB: Get first module in selected phases
        BE->>DB: UPDATE subscription SET current_module_sequence = first_module.seq
    end
    BE-->>FE: LearningProgressResponse {topic_id, total_modules, progress_pct, ...}
    FE->>FE: Navigate to "My Learning" tab, show success toast
```

---

## 6. Lesson Generation Flow

```mermaid
sequenceDiagram
    participant SCH as APScheduler (every 30 min)
    participant LNG as LearningNewsletterGenerator
    participant RD as ResourceDiscovery
    participant LS as LessonGeneratorService
    participant DB as PostgreSQL
    participant DDG as DuckDuckGo
    participant GR as Groq API
    participant SMTP as Gmail SMTP

    SCH->>DB: get_all_due_subscriptions()\n(status=active AND last_sent_at + delta <= now)
    loop Each due subscription
        LNG->>DB: get_modules_for_subscription(sub)\n(phase-aware: filters by user_phase_subscriptions)
        LNG->>DB: get_generated_lesson(module_id)
        alt Lesson cached
            DB-->>LNG: {content_json, resource_links}
        else Cache miss
            LNG->>RD: discover_resources(topic_name, module_title, keywords)
            RD->>DDG: Search: "{module_title} {topic} Microsoft Learn"
            DDG-->>RD: List of URLs (sorted by domain priority)
            loop Up to 3 priority URLs
                RD->>RD: requests.get(url, timeout=10s)
                RD->>RD: BeautifulSoup extract main content
                RD-->>LNG: [{url, content: "...", source}]
            end
            LNG->>LS: generate_lesson(topic, module, objectives, resources)
            LS->>GR: chat.completions.create\n(Llama 3.3 70B, temp=0.3, json_object)
            GR-->>LS: Structured JSON lesson\n(explanation, diagram, quiz, exercise...)
            LS-->>LNG: {content_json, resource_links}
            LNG->>DB: save_generated_lesson(module_id, content_json)
        end
        LNG->>LNG: Render learning_email.html (Jinja2)
        LNG->>SMTP: send_email(user_email, subject, HTML)
        SMTP-->>LNG: OK / Error
        alt Sent successfully
            LNG->>DB: update_streak(sub)
            LNG->>DB: INSERT INTO learning_analytics
            LNG->>DB: advance_module(sub) → next seq or status=completed
        else Failed
            LNG->>DB: mark_sent(sub) — update last_sent_at
        end
    end
```

---

## 7. Newsletter Delivery Flow (Individual Digest)

See Diagram 4 above. The individual and team newsletter flows share the same `DigestGenerator` — the team variant calls `generate_and_send_for_newsletter(newsletter)` instead of `generate_and_send_for_user(user)`, using the newsletter's topic list and sending to all `status=accepted` members.

---

## 8. Team Newsletter Invitation Flow

```mermaid
sequenceDiagram
    actor Admin
    actor Invitee
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant DB as PostgreSQL
    participant SMTP as Gmail SMTP

    Admin->>FE: Click "Invite Member", enter email
    FE->>BE: POST /api/teams/{team_id}/invite {email, role}
    BE->>BE: Verify requester is team admin
    BE->>DB: SELECT FROM team_members WHERE team_id=? AND email=?
    alt Member already accepted
        BE-->>FE: 409 Conflict
    else New or re-inviting
        BE->>DB: UPSERT team_members {status="pending"}
        BE->>BE: token = secrets.token_urlsafe(32)
        BE->>DB: INSERT INTO team_invitations\n{token, expires_at=now()+72h, status="pending"}
        BE->>BE: Render invitation_email.html\n(accept_url, decline_url, topics, schedule)
        BE->>SMTP: send_email(invitee_email, "You're invited...")
        SMTP-->>Invitee: Invitation email
        BE-->>FE: {member, invitation_token, invite_url, email_sent}
    end

    Invitee->>FE: Click "Accept" link in email → /team-invite/{token}
    FE->>BE: GET /api/teams/invite/{token}
    BE->>DB: SELECT invitation + team + topics
    alt Expired
        BE-->>FE: 410 Gone
    else Already responded
        BE-->>FE: 409 Conflict
    else Valid
        BE-->>FE: InvitePreviewResponse {team_name, topics, schedule_label, ...}
        FE->>FE: Show invitation preview page
    end

    Invitee->>FE: Click "Accept" button (after login)
    FE->>BE: POST /api/teams/invite/{token}/accept\n(Authorization: Bearer JWT)
    BE->>DB: SELECT invitation WHERE token=?
    BE->>DB: UPDATE team_invitations SET status="accepted", accepted_at=now()
    BE->>DB: UPDATE team_members SET status="accepted", joined_at=now(), user_id=?
    BE-->>FE: TeamMemberResponse {status: "accepted"}
```
