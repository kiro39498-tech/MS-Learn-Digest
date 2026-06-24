# User Manual
## MS Learn Digest

---

## Getting Started

### Logging In

**Option 1: Google Sign-In**
1. Go to the MS Learn Digest homepage
2. Click **Continue with Google**
3. Select your Google account and approve the permissions
4. You'll be automatically redirected to the platform

**Option 2: Email Magic-Link**
1. Click **Continue with Email**
2. Enter your email address and click **Send Login Link**
3. Check your inbox for an email from MS Learn Digest
4. Click the **Sign in to MS Learn Digest** button in the email
5. The link is valid for 15 minutes and can only be used once

> **Note:** If you don't see the email, check your spam/junk folder.

---

## Onboarding Wizard

First-time users are guided through a 2-step setup:

### Step 1: Choose Your Topics

You'll see a card grid of Microsoft technology areas:

| Category | Topics Included |
|---|---|
| ☁️ Azure | Azure Fundamentals, Compute, Networking, Storage, Security, Identity, Monitoring, DevOps, AI, etc. |
| 🗄️ Microsoft Fabric | Fabric Fundamentals, Data Engineering, Data Science, Data Warehouse, Real-Time Analytics, etc. |
| ⚡ Power Platform | Power Apps, Power Automate, Power BI, Power Pages, Copilot Studio |
| 🏢 Microsoft 365 | Teams, SharePoint, Exchange, M365 Security, Microsoft Copilot |
| 🛡️ Security | Microsoft Defender, Sentinel, Entra ID, Security Copilot |
| 🐙 GitHub | GitHub Actions, GitHub Copilot, GitHub Advanced Security |
| 🤖 AI Engineering | Generative AI, Responsible AI |
| 🔀 DevOps | Azure DevOps, GitHub Actions |
| 💼 Dynamics 365 | Sales, Finance, Supply Chain |

**To select a topic:**
- Click a **root topic card** to subscribe to the entire category (includes all subtopics)
- Click **Show subtopics** on any card to expand individual subtopics and select only the ones you want
- Use the **search bar** to find specific topics
- Use the **category filter chips** (All, Cloud, Data, AI, Security, DevOps, M365) to narrow the list

Selected cards show a highlighted border and a checkmark. You can select multiple topics.

> **Tip:** Selecting a root topic like "Azure" covers everything under it — Networking, Security, Compute, etc. You don't need to select each subtopic individually.

### Step 2: Configure Your Schedule

| Setting | Options | Description |
|---|---|---|
| **Frequency** | Daily, Weekly, Bi-weekly, Monthly | How often you receive digests |
| **Day of Week** | Mon–Sun | Which day to receive (not applicable for Daily) |
| **Delivery Time** | 6 AM – 6 PM | What time to receive (your local time) |

Click **Complete Setup** to finish. You'll be redirected to your Dashboard.

---

## Dashboard

The Dashboard shows your digest history — all newsletters that have been generated and sent to you.

### What you see:
- **Status indicators** — `sent` (delivered), `no_content` (nothing new this period), `failed` (delivery error)
- **Topic pills** — which topics the digest covered
- **Date and frequency** — when it was sent
- **Click any digest** to view the full newsletter content

---

## Preferences

Access via the **Settings** link in the sidebar.

### Topics of Interest
Update which topics you receive digests for — uses the same card grid as onboarding. Changes take effect on your next scheduled digest.

### Delivery Schedule
Change your frequency, day, and time. Click **Save Preferences** to apply.

---

## Learning Center

Access via the **Learning** link in the sidebar.

### Browsing Tracks

The **Browse Tracks** tab shows available learning tracks. Each card shows:
- Track name and icon
- Total lesson count and estimated hours
- Difficulty range (Beginner → Expert)

Click **Preview curriculum** to see the phases and module list before enrolling.

### Enrolling in a Track

1. Click **Enrol in Track** on any track card
2. The **Phase Selection** panel opens
3. Choose your track mode:

**Full Track:** All phases delivered in sequence — the complete learning journey from Beginner to Expert.

**Select Phases:** Choose only the phases you need. Useful if you already know the fundamentals and want to jump to advanced topics.

4. Select your delivery frequency (Daily / Weekly / Bi-weekly)
5. Click **Start Learning**

### Your Active Tracks

The **My Learning** tab shows all your enrolled tracks with:
- **Progress bar** — % complete
- **Phase indicator** — which phase you're currently in
- **Streak counter** — consecutive learning days
- **Phase badge** — shows if you're on a custom phase selection
- **Edit phases** — click to update your phase selection at any time
- **Delivery frequency** — change how often you receive lessons
- **View Curriculum** — see all modules grouped by phase, with done/current/upcoming indicators

### Viewing Completed Tracks

The **Completed** tab shows tracks you've finished, with total lessons received and completion date.

### What's in a Lesson Email?

Each learning email contains:
- **Today's Goal** — what you'll be able to do after this lesson
- **Why It Matters** — real enterprise context
- **Deep Explanation** — technical depth appropriate for your skill level
- **Architecture Diagram** — Mermaid-syntax visual diagram
- **Key Concepts** — glossary of important terms
- **Real-World Example** — a named company/scenario applying the technology
- **Hands-On Exercise** — step-by-step practical activity
- **Common Mistakes** — what to avoid and why
- **Quiz** — 5-8 multiple choice questions with explanations
- **Key Takeaways** — summary bullets
- **Further Reading** — official Microsoft documentation links

---

## Teams

Access via the **Teams** link in the sidebar.

### Creating a Team

1. Click **Create Team**
2. Enter a team name and description
3. Select topics for the team newsletter
4. Set the delivery schedule (frequency, day, time)
5. Click **Create**

Your team is created with a newsletter automatically. You are the team admin.

### Inviting Members

1. Click **Invite Member**
2. Enter the member's email address
3. Click **Send Invitation**

The member receives an email with an Accept/Decline link. The link is valid for 72 hours.

### Managing Members

As team admin you can:
- **Resend invitation** to a pending member
- **Remove member** (removes an accepted member or cancels a pending invite)

### Configuring the Newsletter

In the **Newsletter** section:
- **Update Topics** — replace the topic list
- **Update Schedule** — change frequency, day, and time
- **Pause/Resume** — temporarily stop sending the newsletter

### Digest History

The team page shows the last 20 team newsletter digests with status and recipient count.

---

## Managing Your Account

### Changing Preferences
Go to **Settings → Preferences** to update topics, frequency, and delivery time.

### Viewing Digest History
Go to the **Dashboard** to see all your digests. Click any entry to read the full newsletter.

### Logout
Click your profile picture or name in the sidebar, then **Sign out**.

---

## Frequently Asked Questions

**Q: I'm not receiving any digest emails. What should I do?**  
A: Make sure you have at least one topic selected in Preferences. Also ask your admin to run a catalog sync (`POST /api/admin/catalog-sync`) — if the catalog is empty, no digests can be generated.

**Q: My learning lessons stopped. Why?**  
A: Check the Learning Center — if the track shows `completed`, all lessons have been delivered. Otherwise, verify SMTP is working.

**Q: Can I change my phases after enrolling?**  
A: Yes. Go to **My Learning**, find the track, and click **Edit phases** in the phase badge row.

**Q: How often are new topics added to the catalog?**  
A: The MS Learn Catalog is synced once daily. New content added by Microsoft appears in your next digest after the sync.

**Q: Can I be in multiple learning tracks simultaneously?**  
A: Yes. You can enrol in as many tracks as you want with independent schedules.
