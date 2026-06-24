# Component Diagram
## MS Learn Digest

---

## Frontend Components

```mermaid
graph TB
    subgraph "Pages"
        LP[LandingPage\nGoogle + Email login buttons]
        AC[AuthCallback\nHandles Google OAuth code]
        EAC[EmailAuthCallback\nHandles magic-link token]
        OB[Onboarding\n2-step wizard]
        DASH[Dashboard\nDigest history list]
        PREF[Preferences\nTopics + schedule settings]
        LC[LearningCenter\nBrowse + active + completed tracks]
        TEAMS[Teams\nCreate / manage teams + newsletters]
        DD[DigestDetail\nFull digest HTML viewer]
        TI[TeamInvite\nPublic invite accept/decline]
        AT[AdminTesting\nSMTP test, sync, digest test]
    end

    subgraph "Components"
        LAY[Layout\nSidebar navigation + Outlet]
        TCG[TopicCardGrid\nCard-based topic selector\n• Search bar\n• Category filter chips\n• Expandable subtopics\n• Recommended section]
        TT[TopicTree\nTree view (unused in production,\navailable as fallback)]
        PS[PhaseSelector\nPhase enrollment modal\n• Full Track mode\n• Custom Phases mode\n• Frequency picker\n• Summary preview]
    end

    subgraph "Context"
        AUTH[AuthContext\nuseAuth hook\nJWT state management\nrefreshUser()]
    end

    subgraph "Services"
        API[api.js\nAxios instance\n• baseURL from VITE_API_URL\n• JWT interceptor\n• 401 auto-logout]
    end

    OB --> TCG
    PREF --> TCG
    LC --> PS
    DASH --> LAY
    PREF --> LAY
    LC --> LAY
    TEAMS --> LAY
    DD --> LAY
    AT --> LAY
    OB --> AUTH
    DASH --> AUTH
    API --> AUTH
    TCG --> API
    PS --> API
    LC --> API
    TEAMS --> API
```

---

## Backend Modules

```mermaid
graph TB
    subgraph "API Layer (app/api/)"
        R_AUTH[auth.py\nGoogle OAuth + Magic-Link\nEndpoints: /google, /email/request, /email/verify, /providers]
        R_USERS[users.py\nProfile + Preferences\nEndpoints: /me, /me/preferences]
        R_TOPICS[topics.py\nTopic tree + subscriptions\nEndpoints: /, /tree, /roots, /my, /subscribe, /onboard]
        R_DIGESTS[digests.py\nDigest history\nEndpoints: /, /{id}]
        R_LEARNING[learning.py\nTracks + phases + progress\nEndpoints: /topics, /subscribe, /my, /progress, /phases]
        R_TEAMS[teams.py\nTeam + newsletter management\nAll team + invite endpoints]
        R_NL[newsletters.py\nRead-only newsletter list\nEndpoints: /]
        R_ADMIN[admin.py\nAdmin testing + diagnostics\n14 endpoints]
    end

    subgraph "Core (app/core/)"
        CFG[config.py\nSettings — Pydantic Settings v2\n23 environment variables]
        SEC[security.py\ncreate_access_token()\ndecode_token()\nget_current_user_id() dependency]
        SCH[scheduler.py\nAPScheduler setup\n5 jobs: sync, digest, learning, seed_topics, seed_curriculum]
        DB[database.py\nSessionLocal\nget_db() dependency]
        LOG[logging.py\nsetup_logging()\nStructured stdout format]
    end

    subgraph "Models (app/models/)"
        M_USER[user.py → User]
        M_PREF[user_preference.py → UserPreference]
        M_AUTH[auth.py → EmailLoginToken]
        M_TOPIC[topic.py → Topic, UserSubscription]
        M_CATALOG[catalog_cache.py → CatalogCache]
        M_DIGEST[digest.py → Digest, DigestItem]
        M_TEAM[team.py → Team, TeamMember, TeamInvitation, TeamNewsletter, NewsletterTopic, SyncMetadata]
        M_LEARN[learning.py → LearningTopic, LearningModule, UserLearningSubscription, UserPhaseSubscription, GeneratedLesson, LearningAnalytics, LearningWeeklyReview]
    end
```

---

## Repositories

```mermaid
graph TB
    subgraph "Repositories (app/repositories/)"
        UR["UserRepository\n• get_by_id(), get_by_email()\n• mark_onboarded()\n• ensure_onboarded_if_subscribed()\n• upsert_preferences()"]

        TR["TopicRepository\n• seed_system_topics() — 9 roots + 50+ subtopics\n• get_all(), get_roots(), get_tree()\n• get_children(), get_by_id(), get_by_slug()\n• resolve_descendant_ids() — recursive CTE\n• replace_user_subscriptions()"]

        DR["DigestRepository\n• create_digest()\n• add_item()\n• mark_sent(), mark_failed()\n• get_user_digests()\n• get_digest_by_id()"]

        LR["LearningRepository\n• get_all_topics(), get_topic_by_id()\n• get_modules_for_topic()\n• get_modules_for_subscription() — phase-aware\n• create_subscription(), get_subscription()\n• advance_module() — phase-aware\n• create_phase_subscriptions()\n• get_subscribed_phases()\n• get_all_due_subscriptions()\n• save_generated_lesson()\n• get_user_analytics()"]

        TMR["TeamRepository\n• create_team_with_newsletter() — atomic\n• get_by_id(), get_teams_for_user()\n• update_topics(), update_schedule()\n• invite_member(), resend_invitation()\n• accept_invitation(), decline_invitation()\n• remove_member(), cancel_invitation()\n• get_all_active_newsletters()"]
    end
```

---

## Services

```mermaid
graph TB
    subgraph "Services (app/services/)"
        subgraph "auth/"
            AS["AuthService\nexchange_google_code()\nGoogle OAuth token exchange + user upsert"]
            EAS["EmailAuthService\nrequest_login() — rate-limit + token generation + email\nverify_token() — hash lookup + JWT issue"]
        end

        subgraph "ai/"
            GC["GroqClient\ngenerate_digest(items, topics, frequency)\nSingle Groq call per digest\nStructured JSON output with executive_summary + items[]"]
        end

        subgraph "digest/"
            DG["DigestGenerator\ngenerate_and_send_for_user()\ngenerate_and_send_for_newsletter()\n_get_or_generate() — dispatch_cache check\n_render() — Jinja2 template\n_build_filter_sets() — topic→products/subjects\n_query_catalog() — time-windowed cache query"]
        end

        subgraph "email/"
            EC["EmailClient\ntest_connection()\nsend_email() → bool\nsend_email_with_result() → SMTPResult\nsmtplib STARTTLS port 587"]
        end

        subgraph "ingestion/"
            CC["CatalogClient\nfetch_by_type('modules')\nfetch_by_type('learningPaths')\nfetch_catalog() — compat wrapper"]
            CSS["CatalogSyncService\nsync_catalog() — filtered fetch + batch UPSERT\n_upsert_items() — pg_insert ON CONFLICT"]
        end

        subgraph "learning/"
            LGS["LessonGeneratorService\ngenerate_lesson(module_data, resources)\nSenior MCT persona prompt\nGroq llama-3.3-70b, temp=0.3, json_object\n_fallback_lesson() on error"]
            LNG["LearningNewsletterGenerator\ndeliver(subscription)\nOrchestrates: resource_discovery → lesson_generate\n→ render → send → streak → analytics → advance"]
            RD["ResourceDiscovery\ndiscover_resources(topic, module, keywords)\nDuckDuckGo search (priority-sorted)\nBeautifulSoup page extraction\nUp to 3 pages, max 4000 chars each"]
            SEED["seed_learning_curriculum(db)\nBatch UPSERT from curriculum.py\nIdempotent ON CONFLICT DO UPDATE"]
        end
    end
```

---

## Scheduler Jobs

```mermaid
graph LR
    subgraph "APScheduler (AsyncIOScheduler)"
        J1["catalog_sync_job\nCronTrigger: daily at CATALOG_SYNC_HOUR:MINUTE UTC\nDefault: 02:00 UTC\nmisfire_grace_time: 3600s\nrun_catalog_sync()"]

        J2["digest_dispatch_job\nCronTrigger: minute=0,15,30,45\nmisfire_grace_time: 300s\nrun_digest_dispatch()"]

        J3["learning_dispatch_job\nCronTrigger: minute=0,30\nmisfire_grace_time: 300s\nrun_learning_dispatch()"]

        J4["seed_topics_job\nDateTrigger: once on startup\nseed_topics()"]

        J5["seed_learning_job\nDateTrigger: once on startup\nseed_learning_curriculum_job()"]
    end
```

---

## Email Templates

```mermaid
graph LR
    subgraph "Templates (app/templates/)"
        T1["digest_email.html\nJinja2 template\nVariables: digest_title, user_name, topic_names,\nexecutive_summary, items[], freq, item_count,\nfrontend_url, generated_at\nSections: Header, Stats, Exec Summary,\nLearning Content, Highlights, Resources, Footer\nOutlook-compatible table layout"]

        T2["learning_email.html\nJinja2 template\nVariables: topic_name, module_title, explanation,\narchitecture_diagram, key_concepts, real_world_example,\npractical_exercise, quiz, summary, resource_links\nSections: Header, Progress, Goal, Explanation,\nDiagram, Concepts, Example, Exercise, Quiz, Footer"]

        T3["invitation_email.html\nJinja2 template\nVariables: team_name, invited_by_email,\naccept_url, decline_url, expires_at, topics, schedule_label\nSections: Header, Body, Accept button, Footer"]
    end
```
