# ProcessIQ Conversation Flow

## Purpose

This document describes how the current web UI conversation flow works.

It is intentionally based on the shipped Next.js frontend and FastAPI backend, not on older Streamlit behavior or future-state conversation ideas.

Important scope note:

- this document describes the current web app flow
- it does not describe every capability exposed by the backend API
- specifically, the web UI does **not** currently use `POST /continue`

## High-Level Interaction Model

The current UI is chat-first, but it is not "chat only."

The actual interaction pattern is:

1. user describes a process or uploads a file
2. backend extracts or updates structured `ProcessData`
3. user reviews and edits the extracted process in a table
4. user runs analysis
5. results appear in a split-view layout
6. user can refine the process and re-analyze, give feedback, export, or browse saved sessions

That means conversation and structured editing are intentionally combined.

## Current Frontend States

The UI does not implement a formal state machine enum, but it behaves as a small set of practical states.

### 1. Empty state

Shown before the user has entered any message and before results exist.

Visible elements:

- empty-state prompt
- chat input
- file upload action
- settings drawer access

### 2. Extraction / process-building state

Triggered after the user submits text or uploads a file.

Frontend behavior:

- sends `/extract` or `/extract-file`
- shows an extraction status chip
- appends assistant messages to the chat history
- stores returned `process_data` as the active pending process

Possible backend outcomes:

- extracted process data
- a clarification-style assistant message with `needs_input=true`
- extraction error

Important implementation detail:
Even when the backend asks for more information, it may still return updated `process_data`.

### 3. Review and edit state

Once `processData` exists, the app shows the inline process table below the chat.

The user can:

- edit extracted steps directly
- ask for more changes in chat
- upload another file to merge or refine the process
- trigger "estimate missing values" from the process table

The primary call to action at this point is:

- `Run Analysis - <process name>`

There is no separate confirmation card with multiple footer buttons in the current UI. The editable table plus the run-analysis button is the real confirmation flow.

### 4. Analysis state

Triggered when the user clicks the run-analysis button or types a short confirmation such as `run` while pending process data exists.

Frontend behavior:

- calls `POST /analyze`
- shows an analysis status chip
- appends a "Running analysis..." assistant message

If analysis succeeds:

- `insight`, `threadId`, and `graphSchema` are stored
- the reveal transition runs
- the UI shifts into the split-layout results view

### 5. Results state

After the reveal transition completes, the page becomes a two-column layout:

- left side: chat plus editable process table
- right side: results panel

The results panel currently includes these tabs:

- Overview
- Issues
- Recommendations
- Flow
- Scenarios
- Data

The user can also:

- give thumbs-up / thumbs-down recommendation feedback
- export Markdown
- export plain text
- export PDF

The current web UI does not expose CSV export.

### 6. Post-result refinement state

After results exist, the user can continue working in the chat or upload another file.

In this state the chat is used for:

- making changes to the extracted process
- supplying missing context
- refining the current process description

When new process data is returned after a previous analysis:

- the updated process becomes `pendingProcessData`
- the UI shows `Re-analyse - <process name>`

This is an important distinction:
The web app does not currently use the backend's checkpointed `/continue` path for follow-up questions. It primarily treats post-result input as new extraction or refinement against the current process model, then re-runs analysis.

## Chat Behavior

The current `ChatInterface` keeps a local message history in the browser component.

### Initial assistant prompt

On a fresh chat, the UI starts with a built-in assistant message that asks the user to:

- describe the business process
- include rough timing and dependencies
- optionally upload a file

### Message model

Messages in the current frontend are lightweight and local to the component.

Each message stores:

- `role`
- `content`
- optional error flag
- optional collapsed summary

This is simpler than the older, more elaborate message-schema drafts.

### Collapsing older messages

When the chat grows, older messages are collapsed into summaries so the active part of the conversation stays readable.

### Status indicators

The current chat status values are:

- `idle`
- `extracting`
- `analyzing`
- `needs_clarification`
- `error`

Extraction and analysis each cycle through human-readable progress text rather than showing only a spinner.

## File Upload Flow

Files can be uploaded from the chat input area at any time.

Current accepted extensions in the frontend:

- `.csv`
- `.xlsx`
- `.xls`
- `.pdf`
- `.docx`
- `.doc`
- `.ppt`
- `.pptx`
- `.html`
- `.htm`
- `.jpg`
- `.jpeg`
- `.png`
- `.bmp`
- `.tiff`

Current client-side size rule:

- reject files larger than 50 MB before upload

Current backend size rule:

- reject files larger than 50 MB

There is no separate 10 MB warning threshold in the shipped web UI.

## Settings and Conversation Context

The current conversation flow is influenced by settings stored at the page level and passed into the chat component.

The user can set:

- LLM provider
- analysis mode
- max investigation cycles
- industry
- company size
- regulatory environment
- budget limit
- timeline weeks
- no layoffs
- no new hires

These values are sent with extraction and analysis requests and affect:

- extraction context
- confidence scoring
- recommendation constraints
- investigation depth override

## Saved Sessions and Reset Behavior

Outside the chat itself, the conversation flow also interacts with two persistent UX paths.

### Library view

The left rail switches between:

- Analyze
- Library

The library loads saved sessions from `GET /sessions/{user_id}`.

### Reset my data

The settings drawer includes a destructive reset flow that:

- calls `DELETE /profile/{user_id}`
- clears the browser-stored UUID
- reloads the app

This is different from "New analysis," which only clears the current page state and keeps the saved profile/history.

## Current Backend Relationship

The web conversation flow maps to backend endpoints like this:

| UI action | Backend call |
| --- | --- |
| send text | `POST /extract` |
| upload file | `POST /extract-file` |
| run analysis | `POST /analyze` |
| load profile | `GET /profile/{user_id}` |
| save profile | `PUT /profile/{user_id}` |
| load library | `GET /sessions/{user_id}` |
| send feedback | `POST /feedback/{session_id}` |
| export PDF | `POST /export/pdf` |

The following backend capabilities exist but are not wired into the current web flow:

- `POST /continue`
- `GET /graph-schema/{thread_id}`
- `GET /export/csv/{thread_id}`

## Known Gaps

These gaps are worth keeping visible because they affect how future contributors reason about the conversation model.

### Follow-up conversation is UI-local, not fully checkpoint-driven

The backend has a persisted conversation continuation path, but the current web UI does not use it.

### Provider messaging needs to stay precise

The UI offers `ollama`, but extraction is not fully local today. Any conversation-flow documentation or UX copy needs to stay aligned with that fact.

### The current flow is strong for iterative refinement, not yet for rich conversational memory in the UI

The app supports saved sessions and backend persistence, but the visible chat experience is still primarily centered on:

- extract
- review
- analyze
- refine

rather than a fully threaded long-running assistant conversation.

## Review Notes

This document was rewritten because the previous version described several things that are no longer true in the current app, including:

- a formal chat-state model that does not exist in the current frontend
- older result layouts and button patterns
- a follow-up flow built around `/continue`
- a light-theme visual system that no longer matches the shipped UI
- file-size rules and confirmation behaviors that were draft design notes rather than implementation
