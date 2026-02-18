# ProcessIQ — Product Strategy

This document covers two things: the reasoning behind the Phase 2 and Phase 3 roadmap, and the deployment strategy — how to host the app, instrument it for feedback, and find real users without relying on networking or social capital.

---

## The Adoption Problem for AI Analysis Tools

Most AI-powered analysis tools fail to build a user base for one of three reasons:

1. **Too much friction before value.** The user has to set things up, describe their context, wait for results — and by the time they arrive, the user has given up or lost confidence in the tool.
2. **Value stays inside the tool.** The output is useful to the person who ran the analysis, but it never reaches the stakeholder who can approve changes. It produces insights that die on a dashboard.
3. **The tool forgets you.** Every session starts from scratch. The user re-enters the same business context, re-describes their constraints, and gets recommendations that ignore everything it "learned" last time.

ProcessIQ Phase 1 addresses the core analysis quality. Phase 2 addresses all three of these failure modes.

---

## The Market Opportunity: SMBs Without Data Engineers

Enterprise process mining (Celonis, Signavio, IBM Process Mining) is mature and expensive. These tools require:
- Structured event logs extracted from ERP or BPM systems
- Data engineering resources to build and maintain connectors
- $50K–$500K annual licensing
- Months of implementation time

The result: process optimization is accessible to large enterprises with dedicated operations teams, and essentially inaccessible to everyone else.

The underserved market is large:
- A 30-person professional services firm whose client onboarding process has grown chaotic
- A mid-size manufacturer whose approval chain for equipment purchases takes three weeks
- An operations manager at a healthcare provider who wants to document and improve their referral process but has no process mining budget

These users have real processes, real bottlenecks, and real financial stakes — but no path to professional process analysis. ChatGPT gives them generic advice with no structure. Hiring a consultant costs $10K–$50K for a single engagement. Spreadsheets don't tell them anything they don't already know.

ProcessIQ's position: professional-grade process analysis, accessible from a plain-language description, calibrated to real business constraints, at zero cost.

This is not a niche. It is the majority of businesses that have any kind of operational complexity.

---

## Time-to-Value: The Most Critical Metric

In B2B tools, the relationship between time-to-value and retention is steep. Research from SaaS product analytics consistently shows that users who don't reach a meaningful outcome in their first session rarely return.

For ProcessIQ, the "aha moment" is: the agent correctly identifies a non-obvious bottleneck (not just the longest step) and generates a constraint-respecting recommendation the user hadn't considered.

Getting there currently requires:
1. Describing a process in enough detail for extraction to succeed
2. Waiting for extraction
3. Reviewing and potentially correcting the data table
4. Confirming analysis
5. Waiting for analysis
6. Reading structured results

A new user who has no process ready to describe, or who describes it too vaguely, bounces before step 6. The aha moment never arrives.

**Process templates (Phase 3)** collapse this path. A user can load "Invoice Approval," see a realistic pre-filled process immediately analyzed with real results, and then adjust it to reflect their actual situation. Time to first meaningful output drops from 5–10 minutes to under 60 seconds.

Templates are the highest-leverage investment in new-user conversion. They are deprioritized to Phase 3 only because they require content work (curating realistic template data) rather than engineering.

---

## Shareable Output: How Word-of-Mouth Works in Professional Contexts

In consumer apps, word-of-mouth happens through social sharing. In professional tools, it happens differently: one person uses a tool, gets a result they want to communicate to a colleague or manager, and the artifact they share *is* the marketing.

ProcessIQ's current export options (CSV, text, markdown) are functional for follow-up action but not shareable in the professional sense. Nobody emails a CSV to their VP of Operations.

A well-designed PDF report — process diagram, executive summary, top three issues, prioritized recommendations with ROI ranges and explicit assumptions — gets forwarded. It gets included in slide decks. It shows up in Slack with "look what this tool produced." The person who receives it asks where it came from.

This is why PDF/HTML report export (2D) is included in Phase 2 despite not being a "core" feature. It is the primary mechanism by which a single user becomes ten users.

The process visualization (2C) is a prerequisite for this. A report without a visual process flow is a wall of text. A report with a color-coded dependency graph, bottlenecks highlighted, issues annotated — that is a document worth sending.

---

## The Forgetting Problem: Memory as Product Differentiation

The current state: every session, the user re-enters their industry, company size, regulatory context, and constraints. The agent has no memory of what it recommended last time, what the user found useful, or what they explicitly rejected.

This creates a specific user experience failure. After two or three sessions, a user who has been using ProcessIQ consistently gets the same generic recommendations they got the first time. The agent has not learned that they are a healthcare company with a strict audit requirement and a no-hiring constraint. It has not remembered that they rejected automation suggestions last time because of IT budget limits.

From the user's perspective: the tool is not getting smarter. It is not worth continuing to use.

Persistent memory (2A and 2B) changes this. After the second session, the agent loads the user's historical feedback, their stored business profile, and their constraint history. Recommendations are calibrated against everything the agent has learned about this user's situation. The experience shifts from "AI chat" to "advisor who knows my business."

This is the shift from a tool people try to a tool people rely on.

---

## The Outcome Gap: Why Preference Feedback Is Not Enough

The Phase 1 feedback loop (thumbs up/down per recommendation) is valuable but incomplete. It tells the agent what the user *preferred* — but preference and effectiveness are different signals.

A user might prefer recommendations that feel familiar and safe. They might reject recommendations that feel risky even when those recommendations would have the highest actual ROI. Conversely, they might accept recommendations they never implement because they sound reasonable in the moment.

The outcome loop (Phase 3) closes this gap. When a user returns and the agent asks "you said you'd try automating the approval routing — did you implement it? What changed?" — the answer is high-quality signal. An implemented recommendation with positive outcomes is more informative than ten thumbs-up clicks.

Over time, an agent trained on outcomes learns what *works*, not just what users *like*. These are different things. An agent that distinguishes them gives better recommendations than one that only optimizes for stated preferences.

This is the transition from a feedback loop to a learning loop.

---

## Document Upload: The Professional User's Real Workflow

Most business process documentation does not live in CSV files. It lives in:
- Word documents: process SOPs, standard operating procedures
- PDFs: audit reports, compliance documentation, consulting deliverables
- PowerPoint slides: process flow presentations, operations reviews
- Scanned images: legacy process documentation

ProcessIQ's Docling integration handles all of these formats already. The parser exists. It is not exposed in the UI.

Enabling document upload (2E) opens the tool to a professional workflow that currently has no good options. An operations manager can upload their existing 40-page SOP and ask ProcessIQ to identify improvement opportunities — without transcribing it manually. A consultant can upload a client's process flow slide deck and get structured analysis in minutes.

This is low implementation effort for high user-segment value. It is prioritized in Phase 2 because the technical work is already done.

---

## What RAG Adds (and What It Doesn't Replace)

ChromaDB RAG (2F) is often described as the central Phase 2 feature. In this roadmap it is last in Phase 2, not first. The reason:

RAG retrieval is valuable when there is something worth retrieving. Before a user has run multiple analyses, has built a history of process descriptions and outcomes, and has a profile with meaningful context — there is nothing in the vector store worth retrieving. RAG on an empty database returns noise.

The correct sequencing: build the data first (2A, 2B, 2C, 2D, 2E), then retrieve it meaningfully (2F). RAG becomes genuinely useful as the system accumulates analysis history and the user's business context becomes rich enough to inform similarity search.

The value proposition when it works: "You analyzed a similar invoicing process in March — that one had a 40% rework rate at the legal approval step. This process shows the same pattern." This is meaningfully better than any single-session analysis. But it requires sessions to have happened first.

---

## Feature Decisions: What Was Ruled Out and Why

**Multi-user collaboration** is the most commonly requested feature in B2B tools and also one of the most commonly over-built. Shared analyses require authentication, permissions, conflict resolution on concurrent edits, and notification systems. This is a significant infrastructure cost for a benefit that is partially covered by the report export feature. If a user wants to share an analysis with their manager, they export a PDF. If they want their colleague to run their own analysis, the colleague uses their own session. Multi-user collaboration implies a fundamentally different product.

**Real-time web search** adds latency, cost, and unpredictability to every analysis. The value proposition is benchmark data — "how long does a typical invoicing process take in the financial services industry?" Process templates serve this need for common process types with zero external dependency. Formal benchmark comparison (Phase 3) serves it for specific industry data. Neither requires live web access.

**Email notifications and reminders** requires SMTP infrastructure, user email collection, consent management, and unsubscribe handling. The outcome tracking feature (Phase 3) achieves the same behavioral goal — prompting users to close the feedback loop — within the existing session model, with no external infrastructure.

**Fine-tuning for analysis** (as distinct from fine-tuning for extraction) is a specific anti-pattern for this type of system. The analysis path requires judgment: waste vs. core value assessment, constraint conflict resolution, pattern recognition across process types. These are reasoning tasks. Fine-tuning encodes style and format, not reasoning capability. An analysis prompt that can be read and edited in `analyze.j2` will always be more maintainable and improvable than fine-tuned weights that encode the same logic opaquely.

---

## Architecture Advantage: Why This Can Be Built Incrementally

One deliberate design decision in Phase 1 creates significant leverage for Phase 2: the UI never imports from `agent/graph.py` directly. All agent interaction goes through `agent/interface.py`.

This means:
- Every Phase 2 agent capability (memory loading, RAG retrieval, outcome injection) is added to `interface.py` and the nodes — the UI does not change
- The report export (2D) consumes the existing `AnalysisInsight` model — no new analysis path needed
- The Docling UI exposure (2E) routes through the existing `docling_parser.py` → normalizer path — only the file picker changes
- A frontend migration (Phase 3+) replaces the UI layer without touching any agent, analysis, or ingestion code

The isolation boundary between UI and agent is the primary architectural investment that makes incremental development tractable. Each Phase 2 feature can be developed and tested independently because the integration point is narrow and well-defined.

---

## Success Indicators

The roadmap succeeds if, after Phase 2:

- A returning user sees their business profile pre-populated and their historical feedback reflected in new recommendations — without re-entering anything
- A new user can load a template, get meaningful results, and share a PDF report within 5 minutes of first use
- An operations manager can upload their existing SOPs and receive a structured analysis of the process embedded in them
- The agent's recommendations for a user who has completed 10 sessions are demonstrably better-calibrated than on session 1 — not just stylistically different, but more accurately targeted to what actually works for their situation

---

## Deployment Strategy

This section covers the practical side of getting ProcessIQ in front of real users and collecting feedback that is actually useful — without cold outreach, networking events, or video calls. All approaches below are written and asynchronous.

---

### Hosting: Where to Run the App

The right hosting platform changes as the product grows. The rule is: use the simplest option that meets current requirements. Over-engineering the infrastructure before you have users is wasted effort.

#### Phase 1 Deployment: Streamlit Community Cloud

The default starting point. Connect your GitHub repo, set secrets (API keys), and the app is live at a public URL. No CLI, no Docker, no config files.

**Specifications:**
- ~1 GB RAM — adequate for a LangGraph app making API calls (no local models loaded)
- Apps sleep after 12 hours of inactivity; wake time is 5–15 seconds
- No restrictions on outbound HTTPS (OpenAI/Anthropic calls work)
- Completely free

**Limitations to watch:**
- **Ephemeral file system** — SQLite data (LangGraph `SqliteSaver` checkpoints, `user_store.py` UUID sessions) is wiped on every restart or redeploy. For Phase 1 testing this is acceptable; for real users who expect session continuity, it is not. This is the primary migration trigger, not RAM.
- **Memory pressure** — when ChromaDB is added, the in-process vector store will push toward the 1 GB ceiling. This is the secondary migration trigger.

#### Phase 2 Migration: HuggingFace Spaces

When ChromaDB is integrated, migrate to HuggingFace Spaces.

**Specifications:**
- 16 GB RAM, 2 vCPUs — the most generous free tier available
- 50 GB non-persistent disk
- Sleeps after 48 hours of inactivity
- Standard HTTPS (port 443) unrestricted — API calls work normally
- Deployment via Git push or HF CLI; secrets managed in the Space settings UI

The headroom is what matters here. 16 GB accommodates ChromaDB collections, in-memory LangGraph state, and pandas DataFrames without the memory pressure that would hit Streamlit Community Cloud.

#### If Always-On Reliability Is Required: Railway (~$5–10/mo)

Both free tiers above have sleep behavior — apps spin down and restart on the next request. For a demo or portfolio this is acceptable. For real users who expect instant response, it is not.

Railway's Hobby plan has no scale-to-zero by default. Containers stay running. Cold starts are not a problem.

**Decision rule:** If you are showing the app to people who matter (potential users, evaluators) and a 15-second cold start would undermine confidence, pay the $5–10/month and use Railway. Otherwise, stay on the free tiers until there is evidence of real usage.

---

### Instrumentation: Knowing What Users Actually Do

Do not rely on asking users what they do. Instrument the app to record it. This removes the dependency on user interviews for basic behavioral data.

#### Error Tracking: Sentry

Install first. Four lines of code, passive — no manual instrumentation required.

```python
import sentry_sdk
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    traces_sample_rate=0.1
)
```

Sentry automatically captures uncaught exceptions, LLM API failures, validation errors, and anything that crashes a LangGraph node. You get stack traces, user session context, and a timeline of what happened before the error. Free tier: 5,000 errors/month.

#### Event Analytics: PostHog

PostHog's Python SDK captures explicit events you fire at key interactions. Free tier is 1 million events/month — more than sufficient through an entire beta period.

```python
import posthog
posthog.project_api_key = settings.posthog_key
posthog.capture(st.session_state.user_id, "analysis_completed", {
    "step_count": len(process_data.steps),
    "confidence_score": metrics.confidence,
    "model_provider": settings.llm_provider,
    "had_clarification_loop": state.clarification_rounds > 0,
})
```

**Events worth tracking for ProcessIQ:**
- `process_described` — user submitted a text description
- `file_uploaded` — user uploaded a file
- `clarification_loop_entered` — agent asked for more data
- `data_confirmed` — user confirmed the extracted step table
- `analysis_completed` — full analysis produced
- `recommendation_feedback` — thumbs up/down with which recommendation
- `export_downloaded` — which format (CSV, markdown, PDF)
- `session_returned` — user opened the app in a new session (cross-session return rate)

This data tells you which features are used, where users drop off, and whether the clarification loop is triggering too often (a sign of poor extraction quality).

#### In-App Feedback: Two Layers

**Layer 1 — Quick rating (Streamlit built-in):**
Streamlit 1.33+ has `st.feedback()` — a thumbs up/down or star widget. Add it at the bottom of the results view: "Was this analysis useful?" Fire the result as a PostHog event so it is recorded alongside the session data.

**Layer 2 — Qualitative form (Tally.so):**
For users who want to say more, link a Tally.so form in the sidebar. Tally is free, clean, and requires no backend — responses land in a spreadsheet. Ask three questions:
1. What type of process were you analyzing?
2. Did the recommendations match your actual constraints?
3. What is missing that would make this more useful?

These three questions surface the issues that event analytics cannot: constraint mismatches, missing process types, and feature gaps the user encountered but did not trigger any tracked event.

---

### Finding First Users: The Introverted Approach

The core principle: **all of these channels are written and asynchronous**. None of them require video calls, in-person events, or real-time conversations. The standard advice for B2B founders ("do 50 customer discovery calls") is not the only path. It is the social path. There is a written path that works for solo builders who communicate better in text.

The framing that works everywhere: **problem-sharer, not marketer.** "I built this because I couldn't find a tool that analyzed processes while respecting operational constraints. Looking for people who've run into the same wall to tell me if I solved it right." This is honest, specific, and invites genuine responses. Marketing copy invites no response.

#### Pre-Launch: BetaList (2–3 Weeks Before Anything Else)

Submit to [betalist.com](https://betalist.com) immediately. BetaList lists pre-launch products for early adopters who specifically want to try unfinished tools and give feedback. It takes 1–2 weeks to be approved and listed.

BetaList visitors convert to email signups at 15–25% — much higher than any other channel — because they came specifically to find things to try. A small waitlist of 20–50 genuinely interested people before your first public post is worth more than 500 passive social media impressions.

This requires one submission form and a landing page. Do it before anything else.

#### Target Audience Communities (Highest Priority)

These communities contain the actual users — operations managers, Lean practitioners, business analysts.

| Community | URL | What to Post |
|---|---|---|
| r/processimprovement | reddit.com/r/processimprovement | 50K members, the most directly targeted subreddit — Lean/Six Sigma/operations people discussing exactly the problem ProcessIQ solves |
| r/operations | reddit.com/r/operations | Operations managers, supply chain, workflow — problem-sharer framing |
| r/lean | reddit.com/r/lean | Lean practitioners by definition work on process improvement |
| r/businessanalysis | reddit.com/r/businessanalysis | Business analysts who map and document processes |
| r/sixsigma | reddit.com/r/sixsigma | Data-driven process practitioners |
| Process Excellence Network | processexcellencenetwork.com | 160,000 operational excellence professionals; post as a resource, not a launch announcement |
| LinkedIn "Lean Six Sigma" Group | linkedin.com/groups | 725,000 members; written posts, async responses |
| iSixSigma | isixsigma.com | Forum + newsletter; niche but high practitioner density |
| Operations Nation (Slack) | operationsnation.com | COOs and operations leads at SMBs — harder to get into, higher signal when you do |
| APQC Community | apqc.org | American Productivity and Quality Center — where serious process professionals participate |

**Before posting in any community:** spend time reading existing posts and contributing genuine answers to 3–5 questions. This is not about karma farming — it is about understanding what these people actually struggle with and framing your post in terms they recognize.

#### Builder Communities (Product and Positioning Feedback)

These communities will not become your users, but they will give you the most honest feedback on your product framing, business model, and what you are missing. This is where you validate whether you have articulated the value correctly.

| Community | What You Get |
|---|---|
| Indie Hackers (indiehackers.com) | Founder community. Post in "Share Your Project." Direct, honest feedback on product and positioning. Text-based forum |
| r/SideProject | Weekly show-and-tell threads. Explicit self-promotion is the norm |
| r/SaaS | Product and business model feedback from other builders |
| Show HN (news.ycombinator.com) | Technical audience. High-quality comments. Permanent indexed record. Use title format: "Show HN: ProcessIQ — AI process bottleneck analyzer [link]" |

**Show HN is worth doing.** Low effort, zero cost. A single ops manager who comments and tries the tool is worth more than 100 passive views. Even modest HN traction (20–50 upvotes) generates 300–800 unique visitors in 24 hours and results in a permanent public record of the launch.

#### Later: Product Hunt

Do not launch on Product Hunt first. The Product Hunt audience is tech enthusiasts and early adopters, not operations managers or Lean practitioners. Direct customer acquisition from Product Hunt for a niche B2B process tool will be low.

What Product Hunt is useful for: generating social proof, getting indexed by AI tool directories that scrape Product Hunt listings automatically (There's An AI For That, FutureTools, etc.), and giving you a "Featured on Product Hunt" badge that adds credibility on your landing page.

Launch on Product Hunt after you have initial real users and at least a few genuine testimonials. Frame the launch around what real users found valuable.

---

### The Launch Sequence

```
Week -3 to -2
  Submit to BetaList (takes 1-2 weeks to be listed)
  Deploy stable URL on Streamlit Community Cloud
  Set up Sentry (passive, 4 lines of code)
  Set up PostHog event tracking at key interactions
  Add st.feedback() widget to results view
  Add Tally.so feedback link to sidebar

Week -1
  BetaList goes live — collect first signups
  Read 20+ posts in r/operations and r/lean to understand their language
  Draft your "problem-sharer" post — have a specific person read it before posting

Week 1 (Launch)
  Post in r/operations — problem-sharer framing
  Post in r/lean — same
  Post in r/businessanalysis
  Post "Show HN" on Hacker News
  Post on Indie Hackers "Share Your Project"
  Post in LinkedIn "Lean Six Sigma" group
  Respond to every comment, even if just to acknowledge

Weeks 2-4 (Iterate)
  Follow up with anyone who engaged via DM or email — async, no calls required
  Ask three specific questions: (1) what process type they used, (2) whether constraints were respected, (3) what was missing
  Fix the highest-friction issues first
  Post a brief "week 2 update" on Indie Hackers — what you learned, what you changed
  Changelog posts do well with the builder community

Month 2+
  Submit to AI tool directories: There's An AI For That, FutureTools, AI Tool directories
  Launch on Product Hunt — now you have users and testimonials to support the listing
  Post on Process Excellence Network as a practitioner resource
  Write a technical post about the LangGraph + Streamlit architecture for dev communities
```

---

### The B2B Feedback Problem: Getting Useful Responses Without Interviews

B2B user feedback is harder to get than consumer feedback because the person using the tool is rarely the person who decides whether the business adopts it. For ProcessIQ at this stage, the relevant user is the individual contributor — the operations analyst, the Lean coordinator, the process owner — not their manager.

**What works asynchronously:**

Email or DM follow-up after someone engages publicly. If a user posts a comment on your Show HN or Reddit post, reply with: "Thanks for trying it — would you be willing to answer three questions by email? Takes 5 minutes, no call needed." Most people who commented publicly will respond in writing. Keep it to three questions maximum.

**The three questions that extract the most signal:**
1. "What specific process were you analyzing, and what type of company?" — This tells you whether the tool is reaching the right use cases
2. "Did the recommendations respect your actual constraints, or did they suggest things that weren't realistic for your situation?" — This tests the core value proposition directly
3. "What would have to be different for you to use this regularly instead of once?" — This surfaces the retention problem, which is different from the acquisition problem

Do not ask "what did you like" or "what would you improve." These produce vague, polite answers. Ask concrete situational questions that require specific answers.

**Passive feedback from instrumentation:**
PostHog event data tells you what users do. The `clarification_loop_entered` event tells you how often the agent asks for more data — if it fires on more than 30% of sessions, extraction quality is a problem. The `export_downloaded` event tells you which output format users actually want. The absence of `session_returned` events tells you the retention problem before any user tells you in writing.

Instrumentation answers the "what" questions. User follow-up answers the "why" questions. You need both, but instrumentation is passive and requires no social interaction.

---

### Realistic Expectations

Getting the first 10 real users from a cold start with no audience takes longer than most launch guides imply. The realistic timeline:

- **Weeks 1–2:** 2–5 users from BetaList and early Reddit posts, most of whom try the app once
- **Month 1:** 10–30 total unique users if Show HN gets any traction
- **Month 2–3:** 50–100 users if you iterate visibly (changelog posts, community updates) and the process improvement communities engage

The metric that matters at this stage is not user count — it is **return session rate**. If a meaningful fraction of users run more than one analysis, the tool is providing real value. If everyone tries it once and leaves, the feedback mechanism (PostHog's `session_returned` event) will tell you before any user does.

One user who runs 10 analyses and gives specific feedback on what broke is worth more than 100 users who tried it once. Optimize first for depth of engagement with a small number of real users, not breadth of acquisition.
