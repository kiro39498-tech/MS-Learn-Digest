# Learning Engine Documentation
## MS Learn Digest

---

## Overview

The Learning Engine is a completely independent subsystem from the digest engine. It delivers structured, AI-generated learning lessons to users based on a phased curriculum of Microsoft technology tracks.

**Key separation:** The learning engine never touches `catalog_cache`, `digests`, or any digest-related tables. It has its own tables, repository, services, and scheduler job.

---

## Learning Tracks

Each track represents a complete professional learning journey for a Microsoft technology area.

### Track Structure
```
LearningTopic
├── id, name, slug, icon
├── total_modules, difficulty_range, estimated_hours
└── modules[]
    ├── sequence_number (1-based ordering)
    ├── title, description
    ├── phase_name, phase_number
    ├── skill_level (beginner|intermediate|advanced|expert)
    ├── is_milestone (True for capstone projects)
    ├── learning_objectives[]
    └── keywords[]
```

### Curriculum Source
Tracks are defined in `services/learning/curriculum.py` as Python data structures. The `seed_learning_curriculum()` function (called on startup) upserts them into the database using PostgreSQL `ON CONFLICT DO UPDATE`.

### Example Track Layout
```
Azure Administrator
├── Phase 1: Fundamentals (10 modules, beginner)
│   ├── Module 01: Introduction to Azure
│   ├── Module 02: Azure Global Infrastructure
│   ├── ...
│   └── Module 10: ★ MILESTONE — Fundamentals Capstone Project
├── Phase 2: Compute (12 modules, intermediate)
│   ├── Module 11: Virtual Machines
│   ├── ...
│   └── Module 22: ★ MILESTONE — Compute Architecture Project
├── Phase 3: Networking (12 modules, intermediate)
├── Phase 4: Storage (8 modules, intermediate)
├── Phase 5: Security (10 modules, advanced)
├── Phase 6: Monitoring (8 modules, advanced)
└── Phase 7: Governance (7 modules, expert)
```

---

## Learning Phases

Phases group related modules within a track and allow selective enrollment.

### Phase Data
Each module has:
- `phase_name`: human-readable label (e.g. `"Phase 3: Networking"`)
- `phase_number`: integer for ordering phases
- `is_milestone`: `True` for capstone/project modules at the end of a phase

### Phase API Response
```json
{
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

## Module Progression

### Full Track Mode (`is_full_track = true`)
All modules delivered in `sequence_number` order. No `user_phase_subscriptions` rows are created.

```
get_modules_for_subscription(sub):
    query LearningModule WHERE topic_id=? AND is_active=true
    ORDER BY sequence_number
```

### Custom Phase Mode (`is_full_track = false`)
Only modules in selected phases are delivered. `user_phase_subscriptions` rows define the active set.

```
get_modules_for_subscription(sub):
    selected_phases = get_subscribed_phases(sub)
    query LearningModule WHERE topic_id=? AND is_active=true
        AND phase_name IN (selected_phases)
    ORDER BY sequence_number
```

### advance_module() Logic
```python
def advance_module(sub):
    active_modules = get_modules_for_subscription(sub)  # phase-aware
    current_seqs = [m.sequence_number for m in active_modules]
    
    current_idx = index_of(sub.current_module_sequence, current_seqs)
    
    if current_idx + 1 >= len(current_seqs):
        # No more modules
        sub.status = "completed"
        sub.completed_at = now()
    else:
        sub.current_module_sequence = current_seqs[current_idx + 1]
    
    sub.last_sent_at = now()
    db.commit()
```

This correctly handles both full tracks and custom phase selections — gaps in `sequence_number` are skipped automatically.

---

## Phase Selection

### Subscribing with Phase Selection
```json
POST /api/learning/subscribe
{
  "topic_id": "uuid",
  "frequency": "weekly",
  "is_full_track": false,
  "selected_phases": ["Phase 1: Fundamentals", "Phase 3: Networking"]
}
```

Backend flow:
1. Create `UserLearningSubscription` with `is_full_track=false`
2. For each selected phase name, query `learning_modules` for distinct `(phase_name, phase_number)` rows matching that topic
3. Insert `UserPhaseSubscription` rows: `{user_id, subscription_id, topic_id, phase_name, phase_number}`
4. Set `current_module_sequence` to the `sequence_number` of the first module in the selected phases

### Editing Phase Selection (Post-Enrollment)
```json
PATCH /api/learning/subscribe/{topic_id}/phases
{
  "is_full_track": false,
  "selected_phases": ["Phase 4: Security", "Phase 5: Monitoring"]
}
```

Backend flow:
1. Update `is_full_track` on subscription
2. Delete old `user_phase_subscriptions` rows
3. Insert new ones
4. If `current_module_sequence` is no longer in the new active module list → reset to first module of new set

---

## Lesson Generation

### One-Time, Shared Cache
Lessons are generated **once per module** and cached permanently in `generated_lessons`. When 100 users subscribe to the same module, only the first delivery triggers Groq — all subsequent users receive the cached lesson.

```
generated_lessons
├── id
├── module_id (UNIQUE)    ← one cached lesson per module
├── topic_id
├── generated_content     ← rendered HTML (populated after first delivery)
├── content_json          ← structured JSON from Groq
├── resource_links        ← [{title, url, source}]
└── generation_model      ← "llama-3.3-70b-versatile"
```

### Generation Steps (on cache miss)
1. `ResourceDiscovery.discover_resources()` — DuckDuckGo + BeautifulSoup, up to 3 pages
2. `LessonGeneratorService.generate_lesson()` — Groq call with full prompt
3. `LearningRepository.save_generated_lesson()` — cache for all future users

---

## Streak Tracking

Every time a lesson is successfully delivered:

```python
def _update_streak(sub, db):
    diff = (now - sub.last_sent_at).days
    if diff <= 1:
        sub.current_streak_days += 1
    else:
        sub.current_streak_days = 1  # streak broken
    sub.longest_streak_days = max(sub.longest_streak_days, sub.current_streak_days)
    sub.total_lessons_sent += 1
```

Streak is per-subscription, not per-user. A user can have independent streaks for each track.

---

## Analytics

Every delivery writes one row to `learning_analytics`:
```
learning_analytics
├── subscription_id, user_id, topic_id, module_id
├── module_sequence
├── sent_at
├── difficulty_level, phase_name
└── is_milestone
```

`LearningRepository.get_user_analytics()` queries this table to compute:
- `lessons_last_30_days` — rows WHERE `sent_at >= now()-30d`
- `milestones_completed` — rows WHERE `is_milestone=true`
- `total_lessons_sent` — sum from `user_learning_subscriptions`
- `current_streak_days`, `longest_streak_days` — from subscriptions

---

## Weekly Reviews

The `learning_weekly_reviews` table exists in the schema (migration `g7h8i9j0k1l2`) but weekly review email delivery is **not yet implemented** in the scheduler. The table is ready for future implementation.

---

## Delivery Schedule

The learning dispatch job runs once every hour. A subscription is "due" when:
```python
def is_due(sub):
    if sub.status != "active":
        return False
    if sub.last_sent_at is None:
        return True  # never delivered — deliver immediately
    delta = {"daily": 20h, "weekly": 6d, "biweekly": 13d}[sub.frequency]
    return now() >= sub.last_sent_at + delta
```

Note: the delta is slightly less than the nominal period (20h not 24h, 6d not 7d) to handle minor scheduling drift.

---

## Subscription Status Lifecycle

```
(created)
    → status = "active"
    → Lessons delivered one by one
    → current_module_sequence advances after each delivery
    → status = "completed" when no more modules remain
```

Completed subscriptions remain in the database for analytics. Users can view them in the "Completed" tab.

---

## Database Tables (Learning Engine)

| Table | Purpose |
|---|---|
| `learning_topics` | Track catalogue (name, slug, total_modules) |
| `learning_modules` | Ordered modules per track (phase, skill_level, is_milestone) |
| `user_learning_subscriptions` | User enrollment with progress, streak, frequency, is_full_track |
| `user_phase_subscriptions` | Selected phases for custom subscriptions |
| `generated_lessons` | Cached lesson JSON + HTML per module (permanent, shared) |
| `learning_analytics` | Per-delivery audit log |
| `learning_weekly_reviews` | Planned weekly summary emails (table exists, delivery not implemented) |
