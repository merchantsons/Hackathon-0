# Company Handbook — AI Employee Bronze Tier

> **Purpose:** This handbook provides the AI Employee with company context for task classification, planning, and execution. It is the single source of truth for how tasks should be handled.  
> **Tier:** Bronze (foundation); Silver+ will use this via `load_handbook()` for LLM-enhanced classification and planning.  
> **Location:** `AI_Employee_Vault/Company_Handbook.md`

---

## 1. Rules of Engagement

*Customise these to match how you want the AI Employee to behave in communications and approvals.*

| Rule | Example / Default |
|------|-------------------|
| **Communication tone** | Always be polite on WhatsApp, email, and all external messages. |
| **Payment approval** | Flag any payment over $500 for my approval before executing. |
| **New contacts** | Do not send emails or messages to new/unknown contacts without approval. |
| **Sensitive actions** | When in doubt, create an approval request in `Pending_Approval/` rather than acting autonomously. |

*Add or edit rules above as needed for your business and risk tolerance.*

---

## 2. Mission & Scope

- **Mission:** Process incoming work items (files in the Inbox) in a consistent, auditable, and safe way without requiring cloud services or paid APIs.
- **Scope (Bronze):** Local-first processing of documents, notes, spreadsheets, code, email, and other file types. All actions are non-destructive where possible; cataloguing and moving files only after explicit plans.
- **Boundary:** The AI Employee does not send data outside the vault, delete originals from `Inbox/` without user action, or execute code from incoming files.

---

## 3. Task Types & Handling

| Task type   | Typical extensions              | Default action (Bronze)   | Notes |
|------------|----------------------------------|---------------------------|--------|
| document   | .pdf, .docx, .doc, .rtf, .odt    | generate_summary          | Summarise and list action items. |
| spreadsheet| .xlsx, .xls, .ods                | analyze_and_report        | Validate, basic stats, short report. |
| image      | .jpg, .jpeg, .png, .gif, .bmp, .svg, .webp | catalog_and_archive | Verify, classify, catalog, archive. |
| code       | .py, .js, .ts, .html, .css, .json, .yaml, .sh, .bat, .ps1 | review_code | **Requires approval** before execution. |
| email      | .eml, .msg                       | parse_and_respond          | **Requires approval** before sending or filing. |
| archive    | .zip, .tar, .gz, .7z, .rar       | extract_and_catalog        | List contents, assess, extract if safe, catalog. |
| note       | .txt, .md                        | generate_summary          | Summarise and extract follow-ups. |
| data       | .csv, .tsv, .xml                 | analyze_and_report        | Validate, basic statistics, short report. |
| unknown    | other                            | general_processing        | Read, determine intent, apply rules, document, route. |

---

## 4. Priority Rules

- **Urgent:** Filenames containing (case-insensitive): `urgent`, `asap`, `critical`, `emergency`, `immediate`. Route to `Pending_Approval/` when approval is required.
- **High:** Filenames containing: `important`, `priority`, `high`. Process soon; no automatic escalation beyond normal queue.
- **Medium:** Default when no priority keyword is present.
- **Low:** Filenames containing: `low`, `when possible`, `backlog`. Process after higher-priority items.

---

## 5. Approval Requirements

The following **always** require human review before execution (plans go to `Pending_Approval/`):

- **Code files** (e.g. .py, .js, .ts, .eml, .msg) — to avoid unintended execution or sending.
- **Explicit urgent** items when the planned action is non-trivial (e.g. not just catalog_and_archive).

After approval, move the plan to `Approved/` and then execute; if rejected, move to `Rejected/` and do not execute.

---

## 6. File & Vault Conventions

- **Inbox:** Only new, user-dropped files. Do not modify or delete files in `Inbox/` from the agent; the watcher/rollback handles removals.
- **Needs_Action:** Working copy and `_meta.md` only. One task per file; process then move to `Done/`.
- **Plans:** One plan per task; naming: `{YYYYMMDD_HHMMSS}_{task_stem}_plan.md`.
- **Done:** Completed task file + its `_meta.md`; append-only audit in `Logs/task_catalog.jsonl`.
- **Logs:** Append-only. No overwriting of `activity.log`, `agent.log`, `watcher.log`, or `task_catalog.jsonl`.

---

## 7. Safety & Compliance (Bronze)

- **DRY_RUN:** When `DRY_RUN=true`, no files are moved, no plans are executed, and no catalog entries are written. Use for validation.
- **No secrets:** Do not log or embed passwords, API keys, or tokens in plans or logs.
- **Audit:** Every completed task must have a corresponding `task_catalog.jsonl` entry with timestamp, file, type, action, priority, tier, and status.

---

## 8. Upgrade Path (Silver+)

- **Silver:** `load_handbook()` and `load_business_goals()` will feed this handbook (and a separate business-goals document) into the Task Classifier and Plan Generator for LLM-driven classification and plan generation.
- **Gold:** Caching of handbook (and other frequently read vault files) for performance.
- **Platinum:** Handbook may expand to include role-specific procedures and multi-agent policies.

---

*Company Handbook v1.0 | Bronze Tier | Personal AI Employee — Building Autonomous FTEs in 2026*
