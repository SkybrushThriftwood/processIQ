# ProcessIQ Conversation Flow

**Created:** 2026-02-03
**Last Updated:** 2026-02-06
**Status:** Implemented

---

## Overview

This document specifies how the chat-first UI handles conversations. The primary interaction is conversational — the agent guides users through process analysis via a state machine that manages conversation flow.

**Design Principles:**
1. **Chat-first:** Primary interaction is conversational
2. **Progressive disclosure:** Agent asks only what it needs
3. **File-friendly:** Drop files anytime, agent extracts and confirms
4. **Transparent:** User always sees and confirms extracted data
5. **Recoverable:** User can go back or restart anytime

**Visual Design:**
- Clean neutral design, white/light background
- Dark text (#1e293b) for readability
- Muted slate accent color (#475569)
- No gradients, no background images, no emojis
- Generous whitespace, clear hierarchy
- Border radius: 0.375rem (6px)

---

## Conversation States

```
                          +------------------+
                          |     WELCOME      |
                          |   (first visit)  |
                          +--------+---------+
                                   |
                    user sends message or drops file
                                   |
                                   v
+--------------------------------------------------------------+
|                        GATHERING                              |
|                                                               |
|  Agent is collecting process information.                     |
|  - Extracts from text/files via Instructor                    |
|  - Asks smart follow-up questions (never invents data)        |
|  - Builds ProcessData                                         |
|                                                               |
|  Exits when: agent has minimum viable data                    |
+----------------------------+---------------------------------+
                             |
              agent shows extracted data card
              (with targeted questions + draft analysis)
                             |
                             v
+--------------------------------------------------------------+
|                       CONFIRMING                              |
|                                                               |
|  User reviews extracted ProcessData.                          |
|  - Data displayed in editable card                            |
|  - Confidence badge + improvement suggestions                 |
|  - Three buttons: Confirm, Edit Data, Estimate Missing        |
|                                                               |
|  Exits when: user clicks "Confirm & Analyze"                  |
+----------------------------+---------------------------------+
                             |
                      user confirms
                             |
                             v
+--------------------------------------------------------------+
|                       ANALYZING                               |
|                                                               |
|  Agent runs full analysis pipeline.                           |
|  - Shows spinner: "Analyzing your process..."                 |
|  - Calculates metrics, runs LLM analysis                      |
|  - Produces AnalysisInsight                                   |
|                                                               |
|  Exits when: analysis complete or error                       |
+----------------------------+---------------------------------+
                             |
              +--------------+--------------+
              |                             |
        analysis done               needs clarification
              |                             |
              v                             v
+---------------------+       +-------------------------------+
|      RESULTS        |       |         CLARIFYING            |
|                     |       |                               |
|  Summary-first      |       |  Agent needs more info:       |
|  display:           |       |  - Low confidence             |
|  - What I Found     |       |  - Missing critical fields    |
|  - Main Issues      |       |                               |
|  - Recommendations  |       |  Shows questions in chat      |
|  - Core Value Work  |       |  User answers -> re-analyze   |
|  - Export options    |       |                               |
+----------+----------+       +-------------------------------+
           |
    user asks follow-up
           |
           v
+--------------------------------------------------------------+
|                      CONTINUING                               |
|                                                               |
|  User can:                                                    |
|  - Ask questions about results                                |
|  - Modify constraints and re-analyze                          |
|  - Start over with new process                                |
|                                                               |
+--------------------------------------------------------------+
```

---

## State Transitions

| From | Trigger | To | Agent Action |
|------|---------|----|--------------|
| WELCOME | User sends message | GATHERING | Extract info, ask follow-ups |
| WELCOME | User drops file | GATHERING | Parse file, extract data, confirm |
| GATHERING | User provides more info | GATHERING | Update partial data, check if sufficient |
| GATHERING | Agent has minimum data | CONFIRMING | Show data card with suggestions |
| CONFIRMING | User edits data | CONFIRMING | Update displayed data |
| CONFIRMING | User confirms | ANALYZING | Run analysis pipeline |
| CONFIRMING | User clicks "Estimate Missing" | GATHERING | Send synthetic estimate request to LLM |
| CONFIRMING | User says "add more info" | GATHERING | Continue collecting |
| ANALYZING | Analysis complete | RESULTS | Show summary-first results |
| ANALYZING | Confidence < 60% | CLARIFYING | Ask specific questions |
| CLARIFYING | User answers | ANALYZING | Re-run with new info |
| RESULTS | User asks follow-up | CONTINUING | Answer question |
| CONTINUING | User says "start over" | WELCOME | Reset state |
| CONTINUING | User modifies constraints | ANALYZING | Re-analyze |
| ANY | User clicks Reset | WELCOME | Clear all state |

---

## Message Types

### ChatMessage Schema

```python
class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class MessageType(str, Enum):
    TEXT = "text"
    FILE = "file"
    DATA_CARD = "data_card"
    ANALYSIS = "analysis"
    CLARIFICATION = "clarification"
    STATUS = "status"
    ERROR = "error"

@dataclass
class ChatMessage:
    role: MessageRole
    type: MessageType
    content: str
    timestamp: datetime

    # Optional structured data
    data: Any = None                       # ProcessData, AnalysisInsight, etc.
    file_name: str | None = None           # For FILE type
    questions: list[dict] | None = None    # For CLARIFICATION type
    is_editable: bool = False              # For DATA_CARD type
    analysis_insight: Any = None           # AnalysisInsight for ANALYSIS type
    draft_insight: Any = None              # Draft preview after extraction
    suggested_questions: list[str] = None  # Targeted follow-up questions
    improvement_suggestions: str = None    # Post-extraction guidance
    confidence: float = 0.0               # Data completeness score
```

---

## Agent Behavior by State

### WELCOME State

**Initial message (shown once per session):**
```
Tell me about a process you'd like to improve, or drop a file describing it.

I can analyze workflows to find bottlenecks and estimate the ROI of improvements.
```

---

### GATHERING State

**Goal:** Collect enough information to build ProcessData.

**Minimum viable data:**
- At least 2 process steps with names
- At least one metric (time, cost, or problem frequency)

**Agent behavior:**
1. Extract what it can from user input
2. If input is vague: ask smart follow-up questions (smart interviewer pattern)
3. If input is detailed enough: extract data, show data card
4. Never invent data — prefer asking over guessing

**Example dialogues:**

*Clear input (extracts immediately):*
```
User: Our invoice approval has 5 steps: submit (30min), manager review
      (1.2 hours, 5% rework), legal (2 hours), finance (45min), final
      approval (15min).

Agent: I found 5 steps in your invoice approval process:
       [DATA CARD with extracted steps]
       Review and confirm, then I'll analyze it.
```

*Vague input (asks questions):*
```
User: Our marketing campaign process is a mess.

Agent: Sounds frustrating. Walk me through a typical campaign from when
       someone has an idea to when it goes live. What are the main steps,
       and where do things usually get stuck?
```

---

### CONFIRMING State

**Goal:** User verifies extracted data before analysis.

**Data card features:**
- Shows all extracted steps in a table
- Confidence badge (data completeness score)
- Improvement suggestions ("What would help" guidance)
- Per-field estimated value markers (asterisks on AI-estimated values)
- Targeted follow-up questions based on data gaps
- Draft analysis preview (when confidence >= 50%)
- Three buttons:
  - **Confirm & Analyze** — proceed to full analysis
  - **Edit Data** — switch to expert mode for direct editing
  - **Estimate Missing** — ask LLM to fill in missing values (only shown when gaps exist)
- "I have more to add" returns to GATHERING

---

### ANALYZING State

**Goal:** Run analysis and show progress.

**Progress display:**
- Spinner with message: "Analyzing your process..."
- Analysis runs: metrics calculation -> LLM analysis via `analyze.j2` -> `AnalysisInsight`

**Implementation:**
- `analysis_pending` flag triggers analysis during render cycle
- Analysis executes in `execute_pending_analysis()` in handlers.py
- Results stored in session state as `analysis_insight`

---

### CLARIFYING State

**Goal:** Get specific missing data that affects analysis quality.

**Triggered when:**
- Confidence score < 60%
- Critical field missing (e.g., no time data at all)

**Agent behavior:**
- Explain why the question matters
- Accept "I don't know" gracefully
- Merge user responses into business profile notes
- Re-run analysis with new context

---

### RESULTS State

**Goal:** Display analysis results in summary-first layout.

**Display components (via `results_display.py`):**
1. **Process Summary** — What the LLM understood about the process
2. **Main Issues** — Problems identified with severity badges, linked to recommendations
3. **Recommendations** — Specific suggestions with feasibility, expected benefit, trade-offs
4. **Core Value Work** — Steps the LLM identified as NOT problems (e.g., creative work)
5. **Expandable sections** — Patterns, questions to consider, analysis caveats
6. **Export Options** — CSV, text, markdown

**Key design:** Issues are linked to specific recommendations. Each recommendation addresses a particular issue, not generic "automate this step" advice.

---

### CONTINUING State

**Goal:** Handle follow-up questions and modifications.

**Supported interactions:**
- "Why did you flag X as an issue?"
- "What if we can't automate that step?"
- "Re-analyze with a $5000 budget constraint"
- "Start over with a different process"

**Implementation:**
- Detects "re-analyze", "try again", "what if" keywords
- Parses constraint modifications (budget amounts, hiring restrictions)
- Detects "start over", "reset", "new process" for conversation reset

---

## File Upload Flow

Files can be dropped into the chat area at any time.

**Flow:**
```
User drops file -> Parse (Docling/pandas) -> LLM extraction -> Data card appears
```

**Supported formats:** PDF, Word, Excel, PowerPoint, HTML, images (PNG, JPG, TIFF, BMP)

**Limits:** 10MB warning threshold, 50MB hard limit.

**Error handling:**
```
Agent: I couldn't read that file. Supported formats are PDF, Word, Excel,
       PowerPoint, and images. You can also describe your process in text.
```

---

## Session State Structure

```python
class ChatState(str, Enum):
    """Conversation states."""
    WELCOME = "welcome"
    GATHERING = "gathering"
    CONFIRMING = "confirming"
    ANALYZING = "analyzing"
    CLARIFYING = "clarifying"
    RESULTS = "results"
    CONTINUING = "continuing"
```

**Key session state fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `chat_state` | ChatState | Current conversation state |
| `messages` | list[ChatMessage] | Full conversation history |
| `process_data` | ProcessData | Confirmed process data |
| `constraints` | Constraints | User-defined constraints |
| `business_profile` | BusinessProfile | Industry, company size, etc. |
| `analysis_insight` | AnalysisInsight | LLM-based analysis results (preferred) |
| `analysis_result` | AnalysisResult | Legacy algorithm-based results (fallback) |
| `confidence` | ConfidenceResult | Data completeness scoring |
| `analysis_mode` | str | Selected analysis preset |
| `expert_mode` | bool | Expert panel visibility |
| `analysis_pending` | bool | Triggers analysis on next render |
| `thread_id` | str | LangGraph persistence thread ID |
| `user_id` | str | UUID for user identification |
| `clarification_context` | list | Accumulated clarification responses |

---

## Guided vs Expert Mode

### Guided Mode (Default)
- Pure chat interface
- Agent leads conversation
- Data card appears only for confirmation
- Minimal UI chrome

### Expert Mode (Toggle in sidebar)
- Two-column layout: chat left (3), expert panel right (2)
- Persistent editable data table (`st.data_editor`)
- Confidence breakdown per category (process, constraints, context)
- Per-step field coverage indicators
- Reasoning trace display

---

## Error Handling in Chat

### Recoverable Errors
Shown as agent messages with recovery options:
```
Agent: I had trouble parsing that Excel file - it looks like the headers
       might be in an unexpected location.

       Can you try:
       - Ensuring headers are in row 1
       - Or describe the process in text instead
```

### API Errors
```
Agent: I'm having trouble connecting to the analysis service.
       This is usually temporary. Would you like me to try again?

       [Retry] [Start Over]
```

### Fatal Errors
Shown with reset option:
```
System: Something went wrong that I can't recover from.
        Your data has been preserved.

        [Download Data] [Start Over]
```

---

## Design Decisions

1. **Messages survive page refresh** via session state + SqliteSaver checkpointer.
2. **Progress messages** (not typing indicator) during analysis, for transparency about what's happening.
3. **File size limits:** 10MB warning, 50MB hard limit. Rejects oversized files with helpful message.
4. **Conversation length:** Not summarized in Phase 1. Context injection uses current table + last 3 substantive user messages to keep LLM calls efficient.
