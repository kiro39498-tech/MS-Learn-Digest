# Data Flow Diagram (DFD)
## MS Learn Digest

---

## Level 0 DFD — Context Diagram

```
                     ┌───────────────────────────────────────────┐
                     │                                           │
    ┌──────────┐     │         MS Learn Digest Platform          │     ┌─────────────────┐
    │   User   │────▶│  (topic subscriptions, learning tracks,  │────▶│    User Email   │
    │          │◀────│   digest preferences, team membership)    │     │   (newsletter)  │
    └──────────┘     │                                           │     └─────────────────┘
                     │                                           │
    ┌──────────┐     │                                           │     ┌─────────────────┐
    │  Admin   │────▶│                                           │────▶│  Member Emails  │
    │          │◀────│                                           │     │  (invitations)  │
    └──────────┘     │                                           │     └─────────────────┘
                     │                                           │
                     └─────────────┬─────────────────────────────┘
                                   │
          ┌────────────────────────┼─────────────────────────┐
          │                        │                         │
          ▼                        ▼                         ▼
  ┌──────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ MS Learn     │      │   Groq API       │      │  Google OAuth    │
  │ Catalog API  │      │ (Llama 3.3 70B)  │      │  (user auth)     │
  └──────────────┘      └──────────────────┘      └──────────────────┘
```

---

## Level 1 DFD — Major Processes

```mermaid
graph TB
    subgraph "External Entities"
        U[User]
        A[Admin]
        MS[MS Learn Catalog API]
        GR[Groq API]
        GO[Google OAuth]
        SMTP[Gmail SMTP]
        DDG[DuckDuckGo]
    end

    subgraph "Processes"
        P1["1.0\nAuthentication"]
        P2["2.0\nTopic & Preference\nManagement"]
        P3["3.0\nCatalog Sync"]
        P4["4.0\nDigest Generation\n& Delivery"]
        P5["5.0\nLearning Track\nManagement"]
        P6["6.0\nLesson Generation\n& Delivery"]
        P7["7.0\nTeam & Newsletter\nManagement"]
    end

    subgraph "Data Stores"
        D1[(users)]
        D2[(user_preferences)]
        D3[(topics / user_subscriptions)]
        D4[(catalog_cache)]
        D5[(digests / digest_items)]
        D6[(learning_topics / modules)]
        D7[(user_learning_subscriptions)]
        D8[(generated_lessons)]
        D9[(teams / members / newsletters)]
    end

    U -->|credentials / OAuth code| P1
    GO -->|user profile| P1
    P1 -->|JWT| U
    P1 -->|upsert user| D1

    U -->|topic selections, schedule| P2
    P2 -->|read topics| D3
    P2 -->|write subscriptions, preferences| D3
    P2 -->|write preferences| D2

    A -->|trigger sync| P3
    P3 -->|fetch catalog| MS
    MS -->|modules + learningPaths JSON| P3
    P3 -->|UPSERT| D4

    P4 -->|read subscriptions| D3
    P4 -->|query catalog_cache| D4
    P4 -->|generate AI content| GR
    GR -->|executive summary + item summaries| P4
    P4 -->|persist digest| D5
    P4 -->|send email| SMTP
    SMTP -->|delivered| U

    U -->|enroll / select phases| P5
    P5 -->|read topics| D6
    P5 -->|write subscription + phases| D7

    P6 -->|read due subscriptions| D7
    P6 -->|check lesson cache| D8
    P6 -->|resource search| DDG
    DDG -->|URLs| P6
    P6 -->|generate lesson| GR
    P6 -->|cache lesson| D8
    P6 -->|send lesson email| SMTP
    SMTP -->|delivered| U

    U -->|create team, invite| P7
    P7 -->|persist team + newsletter| D9
    P7 -->|send invitation| SMTP
    SMTP -->|invite email| U
```

---

## Level 2 DFD — Digest Generation Process (Process 4.0)

```mermaid
graph TB
    subgraph "Process 4.0: Digest Generation & Delivery"
        P41["4.1 Check Delivery Schedule\n(is_due: frequency × time × timezone)"]
        P42["4.2 Resolve Topics\n(resolve_descendant_ids recursive CTE)"]
        P43["4.3 Query Catalog Cache\n(last_modified >= window_start)"]
        P44["4.4 Filter by Topic Overlap\n(products ∩ products_set OR subjects ∩ subjects_set)"]
        P45["4.5 Check Dispatch Cache\n(SHA-256 cache_key)"]
        P46["4.6 Call Groq API\n(one call per unique content set)"]
        P47["4.7 Render HTML Template\n(digest_email.html Jinja2)"]
        P48["4.8 Persist Digest\n(digests + digest_items tables)"]
        P49["4.9 Send via SMTP\n(EmailClient)"]
        P410["4.10 Update Digest Status\n(sent / failed)"]
    end

    subgraph "Data Stores"
        D_PREF[(user_preferences)]
        D_SUB[(user_subscriptions)]
        D_CACHE[(catalog_cache)]
        D_DIGEST[(digests)]
    end

    subgraph "External"
        GROQ[Groq API]
        EMAIL[Gmail SMTP]
    end

    SCH[Scheduler] --> P41
    P41 --> D_PREF
    P41 -->|due| P42
    P42 --> D_SUB
    P42 --> P43
    P43 --> D_CACHE
    P43 --> P44
    P44 -->|matched items| P45
    P45 -->|cache miss| P46
    P46 --> GROQ
    GROQ --> P46
    P46 -->|cache hit or generated| P47
    P47 --> P48
    P48 --> D_DIGEST
    P48 --> P49
    P49 --> EMAIL
    EMAIL --> P410
    P410 --> D_DIGEST
```

---

## Level 2 DFD — Learning Lesson Delivery Process (Process 6.0)

```mermaid
graph TB
    subgraph "Process 6.0: Lesson Generation & Delivery"
        P61["6.1 Find Due Subscriptions\n(last_sent_at + delta <= now)"]
        P62["6.2 Get Current Module\n(phase-aware: full or selected phases)"]
        P63["6.3 Check Lesson Cache\n(generated_lessons by module_id)"]
        P64["6.4 Discover Resources\n(DuckDuckGo + BeautifulSoup)"]
        P65["6.5 Generate Lesson\n(Groq — structured JSON)"]
        P66["6.6 Cache Lesson\n(generated_lessons)"]
        P67["6.7 Render Learning Email\n(learning_email.html Jinja2)"]
        P68["6.8 Send via SMTP"]
        P69["6.9 Update Streak + Analytics\n(learning_analytics)"]
        P610["6.10 Advance Module\n(phase-aware next module)"]
    end

    SCH2[Scheduler] --> P61
    P61 --> D_LSUB[(user_learning_subscriptions)]
    P61 --> P62
    P62 --> D_MOD[(learning_modules)]
    P62 --> D_PHASE[(user_phase_subscriptions)]
    P62 --> P63
    P63 --> D_GCACHE[(generated_lessons)]
    P63 -->|miss| P64
    P64 --> DDG[DuckDuckGo]
    P64 --> P65
    P65 --> GR2[Groq API]
    P65 --> P66
    P66 --> D_GCACHE
    P63 -->|hit or generated| P67
    P67 --> P68
    P68 --> SMTP2[Gmail SMTP]
    P68 --> P69
    P69 --> D_ANA[(learning_analytics)]
    P69 --> P610
    P610 --> D_LSUB
```

---

## Level 2 DFD — Team Newsletter Flow (Process 7.0)

```mermaid
graph TB
    subgraph "Process 7.0: Team & Newsletter Management"
        P71["7.1 Create Team + Newsletter\n(atomic transaction)"]
        P72["7.2 Invite Member\n(generate token + send email)"]
        P73["7.3 Accept Invitation\n(link to user account)"]
        P74["7.4 Team Digest Dispatch\n(same content for all accepted members)"]
    end

    ADMIN[Team Admin] --> P71
    P71 --> D_TEAMS[(teams + team_newsletters)]

    ADMIN --> P72
    P72 --> D_TEAMS
    P72 --> D_INV[(team_invitations)]
    P72 --> SMTP3[Gmail SMTP]
    SMTP3 --> INVITEE[Invitee Email]

    INVITEE --> P73
    P73 --> D_INV
    P73 --> D_MEM[(team_members)]

    SCH3[Scheduler] --> P74
    P74 --> D_MEM
    P74 --> D_TEAMS
    P74 --> GR3[Groq API]
    P74 --> SMTP3
    SMTP3 --> MEM_EMAIL[All Accepted Members]
```
