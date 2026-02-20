# 🤖 Personal AI Employee — Bronze Tier

> **Hackathon:** Personal AI Employee — Building Autonomous FTEs in 2026 </br>
> **Tier:** Bronze (Minimum Viable Local AI Employee Foundation) </br>
> **Architecture:** Perception → Reasoning → Action </br>
> **Status:** Production-ready </br>
> # **BY (MERCHANTSONS) GIAIC ROLL # 00037391**

---

## Table of Contents

1. [What This Is](#what-this-is)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Setup Guide](#setup-guide)
6. [Running the System](#running-the-system)
7. [How Claude Code Uses the Vault](#how-claude-code-uses-the-vault)
8. [Agent Skills Reference](#agent-skills-reference)
9. [Example Test Scenario](#example-test-scenario)
10. [Expected Outputs](#expected-outputs)
11. [Troubleshooting](#troubleshooting)
12. [Upgrade Path](#upgrade-path)

---

## What This Is

A **local-first, privacy-preserving AI Employee** that:

- **Watches** your `Inbox/` folder for new files
- **Classifies** each file (type, priority, required action)
- **Plans** an execution checklist in `Plans/`
- **Processes** tasks through a safe, auditable pipeline
- **Moves** completed tasks to `Done/`
- **Updates** a live `Dashboard.md` you can open in Obsidian

No cloud services. No paid APIs. No data leaving your machine. Pure Python + local files.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PERCEPTION LAYER                          │
│                                                             │
│  watcher.py  ──watches──  Inbox/                            │
│      │                                                      │
│      └── detects new file                                   │
│      └── copies to Needs_Action/                            │
│      └── writes {timestamp}_meta.md                        │
└──────────────────────────────┬──────────────────────────────┘
                               │ (files appear in Needs_Action/)
┌──────────────────────────────▼──────────────────────────────┐
│                    REASONING LAYER                           │
│                                                             │
│  claude_agent.py                                            │
│      │                                                      │
│      ├── VaultReader.scan_needs_action()                    │
│      ├── TaskClassifier.classify()                          │
│      └── PlanGenerator.generate()  ──writes──  Plans/       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    ACTION LAYER                              │
│                                                             │
│  claude_agent.py                                            │
│      │                                                      │
│      ├── requires_approval? ──→  Pending_Approval/          │
│      ├── safe execution    ──→  Logs/task_catalog.jsonl      │
│      ├── FileMover.move()  ──→  Done/                       │
│      └── DashboardUpdater  ──→  Dashboard.md                │
└─────────────────────────────────────────────────────────────┘
```

### The Vault as Memory

The `AI_Employee_Vault/` folder is the AI Employee's **persistent memory**.
Every file, plan, log, and decision lives here — readable in Obsidian or any
text editor. No hidden state, no black boxes.

---

## Project Structure

```
Hackathon - 0 - New/
│
├── watcher.py              ← Perception: filesystem event monitor
├── claude_agent.py         ← Reasoning + Action: task processor
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variable template
├── setup.bat               ← One-time setup (Windows)
├── run_watcher.bat         ← Launch watcher (Windows)
├── run_agent.bat           ← Launch agent (Windows)
├── run_rollback.bat        ← Roll back artifacts for deleted Inbox file (Windows)
│
└── AI_Employee_Vault/
    │
    ├── Dashboard.md        ← Live system dashboard (auto-updated)
    │
    ├── Inbox/              ← Drop new files here
    ├── Needs_Action/       ← Watcher routes files here + meta.md
    ├── Done/               ← Completed tasks archived here
    │
    ├── Plans/              ← Agent-generated execution plans
    ├── Pending_Approval/   ← Awaiting human review
    ├── Approved/           ← Human-approved plans
    ├── Rejected/           ← Human-rejected plans
    │
    ├── Logs/
    │   ├── activity.log        ← Human-readable activity
    │   ├── watcher.log         ← Watcher structured log
    │   ├── agent.log           ← Agent structured log
    │   └── task_catalog.jsonl  ← Append-only audit trail
    │
    └── Skills/
        ├── INDEX.md            ← Skills registry
        ├── vault_reader.md     ← Skill 1: Read vault files
        ├── vault_writer.md     ← Skill 2: Write vault files
        ├── task_classifier.md  ← Skill 3: Classify tasks
        ├── plan_generator.md   ← Skill 4: Generate plans
        ├── file_mover.md       ← Skill 5: Move files safely
        ├── action_processor.md ← Skill 6: Orchestrate pipeline
        └── dashboard_updater.md← Skill 7: Update dashboard
```

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.10+ | `python --version` |
| pip | any | `pip --version` |
| watchdog | 4.0+ | installed via pip |
| Obsidian | any | optional (for vault viewing) |

**Operating System:** Windows, macOS, or Linux
**Disk Space:** < 10 MB for the vault and scripts

---

## Setup Guide

### Step 1 — Clone / Download

Ensure you have these files in one folder:
```
watcher.py
claude_agent.py
requirements.txt
.env.example
run_watcher.bat
run_agent.bat
run_rollback.bat
setup.bat
AI_Employee_Vault/  (already created)
```

### Step 2 — Run Setup (Windows)

```batch
setup.bat
```

**Or manually:**

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env     # macOS/Linux
copy .env.example .env   # Windows

# Verify vault structure
python -c "from claude_agent import DashboardUpdater; DashboardUpdater.update()"
```

### Step 3 — Verify Installation

```bash
# Test watcher imports
python -c "from watchdog.observers import Observer; print('watchdog OK')"

# Test agent
python claude_agent.py --scan
```

Expected output:
```
Pending tasks in Needs_Action/ (0 found):
```

### Step 4 — First Dry Run

Always validate with DRY_RUN before going live:

```bash
# Watcher dry run
DRY_RUN=true python watcher.py    # macOS/Linux
run_watcher.bat --dry              # Windows

# Agent dry run
DRY_RUN=true python claude_agent.py  # macOS/Linux
run_agent.bat --dry                   # Windows
```

### Step 5 — Open Vault in Obsidian (Recommended)

1. Open Obsidian
2. "Open folder as vault"
3. Select `AI_Employee_Vault/`
4. Open `Dashboard.md` as your home note

---

## Running the System

### Terminal 1 — Start the Watcher

```bash
python watcher.py
```
or Windows:
```batch
run_watcher.bat
```

The watcher runs **continuously** until you press `Ctrl+C`.
It monitors `Inbox/` and routes new files to `Needs_Action/`.

### Terminal 2 — Run the Agent

After dropping a file into `Inbox/`:

```bash
python claude_agent.py
```
or Windows:
```batch
run_agent.bat
```

The agent processes all items in `Needs_Action/` and exits.
Run it manually, or schedule it (see below).

### .env (Bronze Tier)

Entry points load `.env` for configuration. Bronze tier only uses:

- **DRY_RUN** — `watcher.py` and `claude_agent.py` read `DRY_RUN=true` from `.env` if set (no files modified when true).

### Scheduling the Agent (Optional)

**Windows Task Scheduler:**
```
Action: Start a program
Program: python
Arguments: claude_agent.py
Start in: C:\path\to\Hackathon - 0 - New
Trigger: Every 5 minutes
```

**macOS/Linux cron:**
```cron
*/5 * * * * cd /path/to/hackathon && python claude_agent.py >> AI_Employee_Vault/Logs/cron.log 2>&1
```

### CLI Reference

```bash
# Process all pending tasks (standard mode)
python claude_agent.py

# Simulate — no filesystem changes
python claude_agent.py --dry-run

# Refresh Dashboard.md without processing
python claude_agent.py --update-dashboard

# List pending tasks without processing
python claude_agent.py --scan
```

---

## How Claude Code Uses the Vault

When Claude Code (Cursor) opens this workspace, it can:

### Read Tasks
```
Read AI_Employee_Vault/Needs_Action/ to find pending tasks
Read each _meta.md file to understand context
```

### Generate Plans
```
Write a new Plan.md to AI_Employee_Vault/Plans/
```

### Process Files
```python
# Claude can invoke the agent directly:
python claude_agent.py

# Or update just the dashboard:
python claude_agent.py --update-dashboard
```

### Invoke Skills Directly
```python
# In a Cursor terminal or Python REPL:
from claude_agent import VaultReader, TaskClassifier, PlanGenerator

tasks = VaultReader.scan_needs_action()
for task in tasks:
    classified = TaskClassifier.classify(task)
    plan = PlanGenerator.generate(classified)
    print(plan[:500])
```

### Add Custom Skills
1. Read `AI_Employee_Vault/Skills/INDEX.md` to understand the skill contract
2. Implement a new class in `claude_agent.py`
3. Add skill definition `.md` to `Skills/`
4. Register in `Skills/INDEX.md`

---

## Agent Skills Reference

| Skill | Class | Purpose |
|-------|-------|---------|
| Vault Reader | `VaultReader` | Read files and list directories |
| Vault Writer | `VaultWriter` | Write and append vault files |
| Task Classifier | `TaskClassifier` | Classify by type/priority/action |
| Plan Generator | `PlanGenerator` | Generate step-by-step plans |
| File Mover | `FileMover` | Safe copy-verify-delete moves |
| Action Processor | `ActionProcessor` | Orchestrate full pipeline |
| Dashboard Updater | `DashboardUpdater` | Refresh Dashboard.md |

Full documentation in `AI_Employee_Vault/Skills/`.

---

## Example Test Scenario

### Scenario: Drop a quarterly report for processing

**Step 1 — Start the watcher** (Terminal 1)
```bash
python watcher.py
```

**Step 2 — Create a test file**
```bash
echo "Q1 2026 Revenue: $2.4M. Action items: Review expenses, approve headcount." > "AI_Employee_Vault/Inbox/quarterly_report.txt"
```
Or simply drag any file into the `AI_Employee_Vault/Inbox/` folder.

**Step 3 — Watch the watcher output**
```
2026-02-19 12:00:01 [INFO    ] VaultWatcher: ▶ New file detected: quarterly_report.txt
2026-02-19 12:00:01 [INFO    ] VaultWatcher:   ✔ Copied  → Needs_Action/20260219_120001_quarterly_report.txt
2026-02-19 12:00:01 [INFO    ] VaultWatcher:   ✔ Metadata → Needs_Action/20260219_120001_quarterly_report_meta.md
2026-02-19 12:00:01 [INFO    ] VaultWatcher:   ✅ Done | quarterly_report.txt → Needs_Action/20260219_120001_quarterly_report.txt [72 bytes]
```

**Step 4 — Run the agent** (Terminal 2)
```bash
python claude_agent.py
```

**Step 5 — Watch the agent output**
```
2026-02-19 12:00:10 [INFO    ] ClaudeAgent: ▶ Processing: 20260219_120001_quarterly_report.txt
2026-02-19 12:00:10 [INFO    ] ClaudeAgent:   type=note  priority=medium  action=generate_summary  approval=False
2026-02-19 12:00:10 [INFO    ] ClaudeAgent:   ✔ Plan → Plans/20260219_120010_20260219_120001_quarterly_report_plan.md
2026-02-19 12:00:10 [INFO    ] ClaudeAgent:   ⚙ Executing: generate_summary on note file
2026-02-19 12:00:10 [INFO    ] ClaudeAgent:   ✔ Done → Done/20260219_120010_20260219_120001_quarterly_report.txt
2026-02-19 12:00:10 [INFO    ] ClaudeAgent:   ✅ 20260219_120001_quarterly_report.txt complete
```

---

## Expected Outputs

After running the full scenario:

### `AI_Employee_Vault/Needs_Action/` — Empty (files moved to Done)

### `AI_Employee_Vault/Plans/` — New Plan file
```markdown
# Plan: 20260219_120001_quarterly_report.txt

| Field | Value |
|-------|-------|
| Type | Note |
| Priority | MEDIUM |
| Action | Generate Summary |

## Execution Checklist
- [ ] Read the full document
- [ ] Identify main topics and key findings
...
```

### `AI_Employee_Vault/Done/` — Task + metadata files
```
20260219_120010_20260219_120001_quarterly_report.txt
20260219_120010_20260219_120001_quarterly_report_meta.md
```

### `AI_Employee_Vault/Dashboard.md` — Updated
```markdown
| ✅ Completed Today | 1 |
| 📁 Total Done | 1 |
```

### `AI_Employee_Vault/Logs/task_catalog.jsonl` — Audit entry
```json
{"timestamp":"2026-02-19T12:00:10","file":"20260219_quarterly_report.txt","type":"note","action":"generate_summary","priority":"medium","tier":"bronze","status":"completed","dry_run":false}
```

---

## Troubleshooting

### "watchdog not found" or "No module named watchdog"
```bash
pip install watchdog
# or
pip install -r requirements.txt
```

### Watcher detects file but nothing happens
- Check `AI_Employee_Vault/Logs/watcher.log` for error messages
- Ensure the file is not a temp file (`.tmp`, `.part` extensions are ignored)
- Try with a `.txt` file first

### Agent finds no tasks
```bash
python claude_agent.py --scan
# Should list files in Needs_Action/
# If empty: watcher may not have run, or files are all _meta.md
```

### Files stuck in Needs_Action
- Check `AI_Employee_Vault/Logs/agent.log` for errors
- Run with `--dry-run` to see what would happen without making changes
- Verify Python has write permissions to the vault directory

### Dashboard.md not updating
```bash
python claude_agent.py --update-dashboard
# If error: check write permissions on AI_Employee_Vault/Dashboard.md
```

### DRY_RUN mode is active but I want live mode
```bash
# Check your .env file
# Ensure: DRY_RUN=false
# Or: unset DRY_RUN  (macOS/Linux)
# Or: run without the --dry-run flag
```

### Urgent file not going to Pending_Approval
- Rename the file to include "urgent" in the filename
  e.g. `urgent_contract_review.pdf`
- Or files ending in `.eml` or `.py` automatically require approval

### Task ran but I need to undo it
- **Roll back:** Delete the original file from `Inbox/`. While the watcher is running, it will detect the deletion and automatically remove all related artifacts. If the watcher was not running, use: `run_rollback.bat "filename.txt"` (Windows) or `python -c "from watcher import rollback_for_deleted_inbox_file; rollback_for_deleted_inbox_file('filename.txt')"` to remove Needs_Action, Done, Plans, Pending_Approval, and task_catalog.jsonl entries, then refresh the Dashboard.
- Alternatively, move the file back to `Inbox/` manually to reprocess. All original `Inbox/` files are preserved until you delete them.

---

## Upgrade Path

### Bronze → Silver
1. Install `anthropic` library: `pip install anthropic`
2. Set `ANTHROPIC_API_KEY` in `.env`
3. Replace `[LLM_HOOK]` sections in `claude_agent.py` with real LLM calls
4. Add MCP server connections for enhanced tool use (e.g. email/Gmail integration)
5. Dashboard gains AI-powered per-task summaries

### Silver → Gold
1. Implement Ralph Wiggum continuous monitoring loop `[RW_HOOK]`
2. Add multi-agent task delegation
3. Connect calendar/project management via MCP
4. `ActionProcessor.run()` becomes a continuous background process

### Gold → Platinum
1. Full autonomous FTE replacement for defined workflow types
2. Self-improving skill library
3. Cross-system integrations
4. Multi-agent orchestration with specialised sub-agents

---

## Safety Checklist

Before deploying:
- [ ] Tested with `DRY_RUN=true` and output looks correct
- [ ] `AI_Employee_Vault/` is outside any synced/shared folder
- [ ] No sensitive files (passwords, keys) in `Inbox/`
- [ ] `Logs/` directory has write permissions
- [ ] `.env` file created and reviewed
- [ ] Verified `Done/` gets populated correctly

---

*AI Employee — Bronze Tier | Personal AI Employee Hackathon 2026*
*Architecture: Perception → Reasoning → Action | Local-first | Privacy-preserving*
