"""
claude_agent.py — AI Employee Claude Agent (Bronze Tier)
=========================================================
Reasoning + Action layers of the Perception → Reasoning → Action architecture.

This script implements the full task-processing pipeline using reusable skill
classes. In Bronze tier all reasoning is rule-based. Every point where an LLM
call would be inserted is marked with # [LLM_HOOK] for Silver+ migration.

Silver+ compatibility:
  • All skill classes have clean interfaces; swap internals, not signatures.
  • [LLM_HOOK] comments mark every upgrade point.

Ralph Wiggum loop: Not implemented. [RW_HOOK] marks future integration.

Usage:
    python claude_agent.py                    # Process all pending tasks
    python claude_agent.py --dry-run          # Simulate; no file changes
    python claude_agent.py --update-dashboard # Dashboard refresh only
    python claude_agent.py --scan             # List tasks without processing

Environment:
    DRY_RUN=true   Enable dry-run (same as --dry-run flag)
"""

import os
import sys
import json
import shutil
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Load .env so DRY_RUN (and Silver+ keys) are available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Fix Windows console encoding so Unicode symbols render correctly
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python < 3.7 fallback — symbols may show as '?'

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

VAULT_ROOT          = Path(__file__).parent / "AI_Employee_Vault"
INBOX_DIR           = VAULT_ROOT / "Inbox"
NEEDS_ACTION_DIR    = VAULT_ROOT / "Needs_Action"
DONE_DIR            = VAULT_ROOT / "Done"
PLANS_DIR           = VAULT_ROOT / "Plans"
PENDING_APPROVAL_DIR = VAULT_ROOT / "Pending_Approval"
APPROVED_DIR        = VAULT_ROOT / "Approved"
REJECTED_DIR        = VAULT_ROOT / "Rejected"
LOGS_DIR            = VAULT_ROOT / "Logs"
SKILLS_DIR          = VAULT_ROOT / "Skills"
DASHBOARD_FILE      = VAULT_ROOT / "Dashboard.md"
CATALOG_FILE        = LOGS_DIR / "task_catalog.jsonl"

AGENT_VERSION = "1.0.0"
TIER          = "bronze"

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in ("true", "1", "yes")

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────

LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOGS_DIR / "agent.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ClaudeAgent")


# ══════════════════════════════════════════════════════════════════════════════
# SKILL 1 — VAULT READER
# See: Skills/vault_reader.md
# ══════════════════════════════════════════════════════════════════════════════

class VaultReader:
    """
    Reads content and lists files from the vault.

    Bronze : Direct filesystem reads.
    Silver+: [LLM_HOOK] Can be backed by MCP filesystem server.
    """

    @staticmethod
    def read_file(path: Path) -> Optional[str]:
        """Return text content of a vault file, or None on failure."""
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error(f"VaultReader.read_file({path.name}): {exc}")
            return None

    @staticmethod
    def list_files(directory: Path, suffix: str = None) -> list[Path]:
        """Return sorted list of files in a vault directory."""
        if not directory.exists():
            return []
        try:
            files = [f for f in directory.iterdir() if f.is_file()]
            if suffix:
                files = [f for f in files if f.suffix.lower() == suffix.lower()]
            return sorted(files, key=lambda f: f.stat().st_mtime)
        except Exception as exc:
            logger.error(f"VaultReader.list_files({directory.name}): {exc}")
            return []

    @staticmethod
    def scan_needs_action() -> list[dict]:
        """
        Scan Needs_Action/ and return task descriptors.
        Each descriptor pairs a task file with its _meta.md counterpart.
        """
        all_files = VaultReader.list_files(NEEDS_ACTION_DIR)
        meta_names = {f.name for f in all_files if f.stem.endswith("_meta")}

        # Task files are non-meta, non-markdown files
        task_files = [
            f for f in all_files
            if f.name not in meta_names and f.suffix.lower() != ".md"
        ]

        tasks = []
        for tf in task_files:
            meta_name = tf.stem + "_meta.md"
            meta_path = NEEDS_ACTION_DIR / meta_name
            tasks.append({
                "task_file" : tf,
                "meta_file" : meta_path if meta_path.exists() else None,
                "meta_content": VaultReader.read_file(meta_path) if meta_path.exists() else None,
                "name"      : tf.name,
                "stem"      : tf.stem,
                "extension" : tf.suffix.lower(),
                "size"      : tf.stat().st_size,
                "modified"  : datetime.fromtimestamp(tf.stat().st_mtime),
            })
        return tasks


# ══════════════════════════════════════════════════════════════════════════════
# SKILL 2 — VAULT WRITER
# See: Skills/vault_writer.md
# ══════════════════════════════════════════════════════════════════════════════

class VaultWriter:
    """
    Writes and appends files in the vault.

    Bronze : Direct filesystem writes.
    Silver+: [LLM_HOOK] Can be backed by MCP filesystem server.
    """

    @staticmethod
    def write(path: Path, content: str, overwrite: bool = True) -> bool:
        """Write text to a vault file. Returns True on success."""
        if path.exists() and not overwrite:
            logger.warning(f"VaultWriter.write: exists, overwrite=False: {path.name}")
            return False
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would write {len(content):,} bytes → {path}")
            return True
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.debug(f"Written: {path.name} ({len(content):,} bytes)")
            return True
        except Exception as exc:
            logger.error(f"VaultWriter.write({path.name}): {exc}")
            return False

    @staticmethod
    def append(path: Path, content: str) -> bool:
        """Append text to an existing vault file."""
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would append to: {path.name}")
            return True
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(content)
            return True
        except Exception as exc:
            logger.error(f"VaultWriter.append({path.name}): {exc}")
            return False


# ══════════════════════════════════════════════════════════════════════════════
# SKILL 3 — TASK CLASSIFIER
# See: Skills/task_classifier.md
# ══════════════════════════════════════════════════════════════════════════════

class TaskClassifier:
    """
    Classifies a task dict by type, priority, required action, and approval need.

    Bronze : Rule-based (filename + extension heuristics).
    Silver+: [LLM_HOOK] Replace classify() body with LLM call:
             response = llm.complete(CLASSIFY_PROMPT.format(**task))
             return parse_json(response)
    """

    _TYPE_MAP: dict[str, list[str]] = {
        "document"   : [".pdf", ".docx", ".doc", ".rtf", ".odt"],
        "spreadsheet": [".xlsx", ".xls", ".ods"],
        "image"      : [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
        "code"       : [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml",
                        ".yml", ".sh", ".bat", ".ps1", ".rb", ".go"],
        "email"      : [".eml", ".msg"],
        "archive"    : [".zip", ".tar", ".gz", ".7z", ".rar"],
        "note"       : [".txt", ".md"],
        "data"       : [".csv", ".tsv", ".xml"],
    }

    _PRIORITY_KEYWORDS: dict[str, list[str]] = {
        "urgent": ["urgent", "asap", "critical", "emergency", "immediate"],
        "high"  : ["important", "high", "priority", "deadline", "needed"],
        "low"   : ["low", "minor", "optional", "sometime", "fyi"],
    }

    _ACTION_MAP: dict[str, str] = {
        "document"   : "read_and_classify",
        "spreadsheet": "analyze_and_report",
        "image"      : "catalog_and_archive",
        "code"       : "review_code",
        "email"      : "parse_and_respond",
        "archive"    : "extract_and_catalog",
        "note"       : "read_and_classify",
        "data"       : "analyze_and_report",
        "unknown"    : "general_processing",
    }

    # Keyword overrides take precedence over type-based defaults
    _KEYWORD_ACTIONS: dict[str, str] = {
        "review"  : "read_and_classify",
        "report"  : "generate_summary",
        "summary" : "generate_summary",
        "task"    : "process_task_list",
        "todo"    : "process_task_list",
        "meeting" : "generate_summary",
        "invoice" : "generate_summary",
    }

    @classmethod
    def classify(cls, task: dict) -> dict:
        """
        Enrich a task dict with classification fields.
        Returns updated dict with: task_type, priority, action, requires_approval.

        # [LLM_HOOK] Silver+:
        # prompt = build_classify_prompt(task, handbook_content, business_goals)
        # result = llm.complete(prompt)
        # return {**task, **parse_classification(result)}
        """
        name_lower = task["name"].lower()
        ext        = task["extension"]

        # Determine task type
        task_type = "unknown"
        for tname, exts in cls._TYPE_MAP.items():
            if ext in exts:
                task_type = tname
                break

        # Determine priority
        priority = "medium"
        for level, keywords in cls._PRIORITY_KEYWORDS.items():
            if any(kw in name_lower for kw in keywords):
                priority = level
                break

        # Determine action (keyword override → type default)
        action = cls._ACTION_MAP.get(task_type, "general_processing")
        for kw, kw_action in cls._KEYWORD_ACTIONS.items():
            if kw in name_lower:
                action = kw_action
                break

        # Safety gate: some task types always require human approval
        requires_approval = (
            priority == "urgent"
            or task_type in {"email", "code"}   # potential external impact
        )

        return {
            **task,
            "task_type"          : task_type,
            "priority"           : priority,
            "action"             : action,
            "requires_approval"  : requires_approval,
            "classifier_version" : f"{AGENT_VERSION}-bronze",
        }


# ══════════════════════════════════════════════════════════════════════════════
# SKILL 4 — PLAN GENERATOR
# See: Skills/plan_generator.md
# ══════════════════════════════════════════════════════════════════════════════

class PlanGenerator:
    """
    Generates a Plan.md checklist for a classified task.

    Bronze : Template-based plans keyed on task action.
    Silver+: [LLM_HOOK] Replace _get_steps() with LLM plan generation.
    """

    _STEPS: dict[str, list[str]] = {
        "read_and_classify": [
            "Open and read the file content in full",
            "Identify the document type and primary subject",
            "Extract key information (who, what, when, why)",
            "Summarise in 3–5 bullet points",
            "Tag with relevant labels and categories",
            "Determine if any action items are present",
            "Archive or route to the appropriate folder",
            "Update Dashboard.md with findings",
        ],
        "generate_summary": [
            "Read the full document",
            "Identify main topics and key findings",
            "Write executive summary (≤ 200 words)",
            "List concrete action items and owners",
            "Note any deadlines or hard dependencies",
            "Save summary to Plans/",
            "Update Dashboard.md with summary link",
        ],
        "process_task_list": [
            "Parse all task items from the file",
            "Sort by urgency × importance (Eisenhower matrix)",
            "Identify dependencies between tasks",
            "Assign effort estimate (S / M / L)",
            "Flag tasks that require human decision",
            "Create structured breakdown in Plans/",
            "Update Dashboard.md task queue",
        ],
        "analyze_and_report": [
            "Open file and validate its structure",
            "Identify schema, column types, and row count",
            "Check for missing values or anomalies",
            "Compute basic summary statistics",
            "Identify patterns or trends",
            "Generate insight report in Plans/",
            "Update Dashboard.md with findings",
        ],
        "parse_and_respond": [
            "Parse headers: sender, recipient, date, subject",
            "Extract body content and attachments list",
            "Identify urgency indicators",
            "Extract action items from body",
            "Draft a response outline (requires approval before sending)",
            "File email in appropriate category",
            "Log to communication audit trail",
        ],
        "review_code": [
            "Read and understand the code structure",
            "Check for syntax and obvious logic errors",
            "Review algorithms for correctness",
            "Identify potential security concerns",
            "Note test coverage gaps",
            "Generate code-review summary in Plans/",
            "Flag items requiring developer follow-up",
        ],
        "catalog_and_archive": [
            "Verify file integrity (size / hash check)",
            "Determine file type and intended purpose",
            "Generate descriptive canonical filename",
            "Add entry to asset catalog",
            "Move to appropriate archive subfolder",
            "Update asset index in Plans/",
        ],
        "extract_and_catalog": [
            "Verify archive is not corrupted",
            "List archive contents without extracting",
            "Assess safety of contents",
            "Extract to a sandboxed staging folder",
            "Catalog extracted files",
            "Route individual files to appropriate folders",
            "Update asset index",
        ],
        "general_processing": [
            "Read and understand the file",
            "Determine the most appropriate handling approach",
            "Apply standard processing rules",
            "Document key findings in a note",
            "Route to appropriate vault folder",
            "Update Dashboard.md",
        ],
    }

    @classmethod
    def generate(cls, task: dict) -> str:
        """
        Return Plan.md content for the given task.

        # [LLM_HOOK] Silver+:
        # context = load_handbook() + load_business_goals()
        # steps = llm.generate_plan(task, context)
        """
        now    = datetime.now()
        action = task.get("action", "general_processing")
        steps  = cls._get_steps(action)
        checklist = "\n".join(f"- [ ] {s}" for s in steps)

        approval_block = ""
        if task.get("requires_approval"):
            approval_block = """
## ⚠️ Human Approval Required

This task requires human review before execution because it either:
- Has **URGENT** priority, or
- Involves **email or code** (potential external impact).

**File placed in:** `Pending_Approval/`

To proceed:
- **Approve** → Move plan to `Approved/`
- **Reject**  → Move plan to `Rejected/`
- **Modify**  → Edit checklist, then move to `Approved/`
"""

        return f"""---
title: "Plan: {task['name']}"
task_file: "{task['name']}"
task_type: "{task.get('task_type', 'unknown')}"
priority: "{task.get('priority', 'medium')}"
action: "{action}"
requires_approval: {str(task.get('requires_approval', False)).lower()}
created: "{now.strftime('%Y-%m-%d %H:%M:%S')}"
status: "pending"
tier: "{TIER}"
---

# Plan: {task['name']}

| Field | Value |
|-------|-------|
| Created | {now.strftime('%Y-%m-%d %H:%M:%S')} |
| File | `{task['name']}` |
| Type | {task.get('task_type', 'unknown').replace('_', ' ').title()} |
| Priority | **{task.get('priority', 'medium').upper()}** |
| Action | {action.replace('_', ' ').title()} |
| Size | {task.get('size', 0):,} bytes |
| Detected | {task.get('modified', now).strftime('%Y-%m-%d %H:%M:%S')} |
| Requires Approval | {'**Yes ⚠️**' if task.get('requires_approval') else 'No'} |
{approval_block}
## Execution Checklist

{checklist}

## Observations

*Record notes here during execution.*

## Completion Checklist

- [ ] All execution steps completed
- [ ] Observations documented above
- [ ] Dashboard.md updated
- [ ] Task file moved to `Done/`
- [ ] Catalog entry written to `Logs/task_catalog.jsonl`

---
*Generated by PlanGenerator v{AGENT_VERSION} (Bronze Tier)*
*Classifier: {task.get('classifier_version', 'unknown')}*
"""

    @classmethod
    def _get_steps(cls, action: str) -> list[str]:
        return cls._STEPS.get(action, cls._STEPS["general_processing"])


# ══════════════════════════════════════════════════════════════════════════════
# SKILL 5 — FILE MOVER
# See: Skills/file_mover.md
# ══════════════════════════════════════════════════════════════════════════════

class FileMover:
    """
    Safely moves or copies files between vault folders.

    Uses copy-verify-delete pattern:  never delete source until destination
    is confirmed to exist at the correct size.

    Bronze : Local shutil operations.
    Silver+: [LLM_HOOK] Can be backed by MCP filesystem server.
    """

    @staticmethod
    def move(source: Path, dest_dir: Path, new_name: str = None) -> Optional[Path]:
        """
        Move source to dest_dir (with optional rename).
        Returns destination Path on success, None on failure.
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_name = new_name or source.name
        dest_path = FileMover._safe_path(dest_dir / dest_name)

        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would move: {source.name} → {dest_dir.name}/{dest_path.name}")
            return dest_path

        try:
            shutil.copy2(source, dest_path)
            # Verify before deleting source
            if not dest_path.exists():
                raise RuntimeError("Destination not found after copy")
            if dest_path.stat().st_size != source.stat().st_size:
                raise RuntimeError("Size mismatch after copy")
            source.unlink()
            logger.info(f"Moved: {source.name} → {dest_dir.name}/{dest_path.name}")
            return dest_path
        except Exception as exc:
            logger.error(f"FileMover.move({source.name}): {exc}")
            # Clean up partial copy
            if dest_path.exists() and source.exists():
                try:
                    dest_path.unlink()
                except Exception:
                    pass
            return None

    @staticmethod
    def copy_to(source: Path, dest_dir: Path, new_name: str = None) -> Optional[Path]:
        """Copy source to dest_dir without removing source."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = FileMover._safe_path(dest_dir / (new_name or source.name))

        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would copy: {source.name} → {dest_dir.name}/")
            return dest_path

        try:
            shutil.copy2(source, dest_path)
            return dest_path
        except Exception as exc:
            logger.error(f"FileMover.copy_to({source.name}): {exc}")
            return None

    @staticmethod
    def _safe_path(path: Path) -> Path:
        """Resolve filename collision by appending a counter suffix."""
        if not path.exists():
            return path
        counter = 1
        while True:
            candidate = path.parent / f"{path.stem}_{counter}{path.suffix}"
            if not candidate.exists():
                return candidate
            counter += 1


# ══════════════════════════════════════════════════════════════════════════════
# SKILL 6 — DASHBOARD UPDATER
# See: Skills/dashboard_updater.md
# ══════════════════════════════════════════════════════════════════════════════

class DashboardUpdater:
    """
    Regenerates Dashboard.md from the current vault state.

    Bronze : File-count statistics.
    Silver+: [LLM_HOOK] Add AI-generated one-line summaries per task.
    """

    @staticmethod
    def update() -> bool:
        """Rewrite Dashboard.md with live vault statistics."""
        now = datetime.now()

        inbox_files    = VaultReader.list_files(INBOX_DIR)
        na_files       = VaultReader.list_files(NEEDS_ACTION_DIR)
        done_files     = VaultReader.list_files(DONE_DIR)
        plan_files     = VaultReader.list_files(PLANS_DIR, ".md")
        pending_files  = VaultReader.list_files(PENDING_APPROVAL_DIR)
        approved_files = VaultReader.list_files(APPROVED_DIR)
        rejected_files = VaultReader.list_files(REJECTED_DIR)

        task_files = [f for f in na_files if not f.stem.endswith("_meta")
                      and f.suffix.lower() != ".md"]

        done_today = [f for f in done_files
                      if datetime.fromtimestamp(f.stat().st_mtime).date() == now.date()]

        # ── Pending tasks table ──────────────────────────────────────────────
        if task_files:
            rows = []
            for f in task_files[:15]:
                age = int((now - datetime.fromtimestamp(f.stat().st_mtime)).total_seconds() / 60)
                rows.append(f"| `{f.name}` | {age}m ago | Unclassified | Medium |")
            pending_table = "\n".join(rows)
        else:
            pending_table = "| — | — | — | — |"

        # ── Done today table ─────────────────────────────────────────────────
        if done_today:
            rows = []
            for f in done_today[:15]:
                t = datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M")
                rows.append(f"| `{f.name}` | {t} | ✅ Completed |")
            done_table = "\n".join(rows)
        else:
            done_table = "| — | — | — |"

        # ── Alerts ───────────────────────────────────────────────────────────
        alerts = []
        if len(task_files) > 10:
            alerts.append(f"- ⚠️ **High load:** {len(task_files)} items awaiting action")
        if pending_files:
            alerts.append(f"- 🔔 **Approval needed:** {len(pending_files)} item(s) in Pending_Approval/")
        if len(inbox_files) > 5:
            alerts.append(f"- 📥 **Inbox filling:** {len(inbox_files)} items unprocessed")
        alert_section = "\n".join(alerts) if alerts else "- ✅ No active alerts"

        content = f"""---
last_updated: "{now.strftime('%Y-%m-%d %H:%M:%S')}"
system: "AI Employee - Bronze Tier"
auto_generated: true
---

# 🤖 AI Employee — Dashboard

> **Last Updated:** {now.strftime('%A, %B %d, %Y at %H:%M:%S')}
> **System:** AI Employee v{AGENT_VERSION} (Bronze Tier)
> **Mode:** {'⚠️ DRY RUN' if DRY_RUN else '🟢 ACTIVE'}

---

## 📊 System Overview

| Metric | Count |
|--------|-------|
| 📥 Inbox | {len(inbox_files)} |
| ⚡ Needs Action | {len(task_files)} |
| 📋 Plans Generated | {len(plan_files)} |
| ⏳ Pending Approval | {len(pending_files)} |
| ✅ Approved | {len(approved_files)} |
| ❌ Rejected | {len(rejected_files)} |
| ✅ Completed Today | {len(done_today)} |
| 📁 Total Done | {len(done_files)} |

---

## ⚡ Pending Tasks

| File | Age | Type | Priority |
|------|-----|------|----------|
{pending_table}

---

## 🔄 In Progress

*Tasks actively being processed by the AI Employee.*

| Task | Status | Started |
|------|--------|---------|
| — | — | — |

---

## ✅ Completed Today

| File | Time | Status |
|------|------|--------|
{done_table}

---

## 🚨 Alerts

{alert_section}

---

## 🖥️ System Status

| Component | Status |
|-----------|--------|
| Vault Watcher | 🟢 Active |
| Claude Agent | 🟢 Ready |
| Task Classifier | 🟢 Online |
| Plan Generator | 🟢 Online |
| File Mover | 🟢 Online |
| Dashboard Updater | 🟢 Online |
| DRY_RUN Mode | {'🟡 ENABLED' if DRY_RUN else '⚫ Disabled'} |

---

## 📌 Quick Navigation

- [[Inbox]] — Drop new tasks here
- [[Needs_Action]] — Awaiting processing
- [[Plans]] — Generated execution plans
- [[Pending_Approval]] — Awaiting human review
- [[Approved]] — Approved for execution
- [[Rejected]] — Declined tasks
- [[Done]] — Completed tasks
- [[Logs]] — Audit logs and catalog

---

*Auto-generated by DashboardUpdater v{AGENT_VERSION} | Bronze Tier*
*Upgrade to Silver for AI-powered per-task summaries.*
"""
        return VaultWriter.write(DASHBOARD_FILE, content)


# ══════════════════════════════════════════════════════════════════════════════
# SKILL 7 — ACTION PROCESSOR
# See: Skills/action_processor.md
# ══════════════════════════════════════════════════════════════════════════════

class ActionProcessor:
    """
    Orchestrates the full task-processing pipeline for all items in Needs_Action/.

    Pipeline per task:
      classify → generate_plan → route (approval | execute) → move_to_done → update_dashboard

    Bronze  : Rule-based classify + execute (safe catalog-only actions).
    Silver+ : [LLM_HOOK] Replace execute step with LLM-driven real actions.
    [RW_HOOK]: Gold tier Ralph Wiggum continuous loop wraps this class.
    """

    @staticmethod
    def run() -> dict:
        """Process all pending tasks. Returns a results summary dict."""
        logger.info("═" * 62)
        logger.info(f"  ClaudeAgent v{AGENT_VERSION} — Bronze Tier")
        logger.info(f"  Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if DRY_RUN:
            logger.info("  *** DRY_RUN MODE — No changes will be made ***")
        logger.info("═" * 62)

        results = {
            "processed"          : 0,
            "plans_created"      : 0,
            "completed"          : 0,
            "routed_for_approval": 0,
            "errors"             : 0,
        }

        tasks = VaultReader.scan_needs_action()
        if not tasks:
            logger.info("Needs_Action/ is empty — nothing to process.")
            DashboardUpdater.update()
            return results

        logger.info(f"Found {len(tasks)} task(s) in Needs_Action/")

        for task in tasks:
            try:
                ActionProcessor._process_one(task, results)
            except Exception as exc:
                logger.error(f"Error on {task['name']}: {exc}", exc_info=True)
                results["errors"] += 1

        DashboardUpdater.update()
        logger.info("═" * 62)
        logger.info(f"  Run complete: {results}")
        logger.info("═" * 62)
        return results

    # ── private ─────────────────────────────────────────────────────────────

    @staticmethod
    def _process_one(task: dict, results: dict):
        logger.info(f"▶ Processing: {task['name']}")

        # Step 1 — Classify
        ct = TaskClassifier.classify(task)
        logger.info(
            f"  type={ct['task_type']}  priority={ct['priority']}  "
            f"action={ct['action']}  approval={ct['requires_approval']}"
        )

        # Step 2 — Generate plan
        plan_content = PlanGenerator.generate(ct)
        ts           = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_name    = f"{ts}_{task['stem']}_plan.md"
        plan_path    = PLANS_DIR / plan_name

        PLANS_DIR.mkdir(parents=True, exist_ok=True)
        if VaultWriter.write(plan_path, plan_content):
            results["plans_created"] += 1
            logger.info(f"  ✔ Plan → Plans/{plan_name}")

        # Step 3 — Route
        if ct["requires_approval"]:
            # Move task file + metadata to Pending_Approval; copy plan there too.
            # This clears the queue — human reviews in Pending_Approval/.
            FileMover.move(task["task_file"], PENDING_APPROVAL_DIR,
                           f"{ts}_{task['name']}")
            if task.get("meta_file") and task["meta_file"].exists():
                FileMover.move(task["meta_file"], PENDING_APPROVAL_DIR,
                               f"{ts}_{task['meta_file'].name}")
            FileMover.copy_to(plan_path, PENDING_APPROVAL_DIR)
            logger.info(f"  ⏳ Routed to Pending_Approval/ (approval required)")
            results["routed_for_approval"] += 1
        else:
            # Step 4 — Execute safe Bronze-tier actions
            ActionProcessor._execute(ct)

            # Step 5 — Move task file to Done/
            done_name = f"{ts}_{task['name']}"
            dest = FileMover.move(task["task_file"], DONE_DIR, done_name)
            if dest:
                results["completed"] += 1
                logger.info(f"  ✔ Done → Done/{done_name}")

            # Move metadata alongside it
            if task.get("meta_file") and task["meta_file"].exists():
                FileMover.move(
                    task["meta_file"], DONE_DIR,
                    f"{ts}_{task['meta_file'].name}"
                )

        results["processed"] += 1
        logger.info(f"  ✅ {task['name']} complete")

    @staticmethod
    def _execute(task: dict):
        """
        Execute safe, non-destructive Bronze-tier actions.

        Currently: write a structured catalog entry to Logs/task_catalog.jsonl.

        # [LLM_HOOK] Silver+: Replace with real AI-driven actions, e.g.:
        #   - Generate document summaries via LLM
        #   - Draft email responses (held in Pending_Approval)
        #   - Query internal knowledge base
        #   - Populate spreadsheet templates
        """
        logger.info(f"  ⚙ Executing: {task.get('action')} on {task.get('task_type')} file")

        entry = {
            "timestamp"  : datetime.now().isoformat(),
            "file"       : task["name"],
            "type"       : task.get("task_type"),
            "action"     : task.get("action"),
            "priority"   : task.get("priority"),
            "tier"       : TIER,
            "status"     : "completed",
            "dry_run"    : DRY_RUN,
        }

        if not DRY_RUN:
            try:
                LOGS_DIR.mkdir(parents=True, exist_ok=True)
                with open(CATALOG_FILE, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry) + "\n")
                logger.debug(f"  Catalog entry written")
            except Exception as exc:
                logger.warning(f"  Catalog write failed: {exc}")
        else:
            logger.info(f"  [DRY_RUN] Catalog entry: {entry}")


# ──────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="claude_agent",
        description="AI Employee — Claude Agent Task Processor (Bronze Tier)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python claude_agent.py                    Process all pending tasks
  python claude_agent.py --dry-run          Simulate; no changes
  python claude_agent.py --update-dashboard Refresh Dashboard.md only
  python claude_agent.py --scan             List tasks in Needs_Action/

Environment variables:
  DRY_RUN=true    Enable dry-run mode
        """,
    )
    p.add_argument("--dry-run",           action="store_true",
                   help="Simulate actions without writing or moving files")
    p.add_argument("--update-dashboard",  action="store_true",
                   help="Only refresh Dashboard.md; skip task processing")
    p.add_argument("--scan",              action="store_true",
                   help="List pending tasks without processing them")
    return p


def main():
    global DRY_RUN

    args = build_parser().parse_args()

    if args.dry_run:
        DRY_RUN = True
        os.environ["DRY_RUN"] = "true"
        logger.info("DRY_RUN enabled via --dry-run flag")

    if args.scan:
        tasks = VaultReader.scan_needs_action()
        print(f"\nPending tasks in Needs_Action/ ({len(tasks)} found):")
        for t in tasks:
            print(f"  • {t['name']}  [{t['size']:,} bytes | {t['modified'].strftime('%H:%M:%S')}]")
        print()
        return

    if args.update_dashboard:
        logger.info("Dashboard update only…")
        DashboardUpdater.update()
        logger.info("Dashboard updated.")
        return

    results = ActionProcessor.run()

    print(f"\n{'─'*50}")
    print(f"  Run Summary")
    print(f"{'─'*50}")
    print(f"  Tasks processed       : {results['processed']}")
    print(f"  Plans created         : {results['plans_created']}")
    print(f"  Completed → Done/     : {results['completed']}")
    print(f"  Pending approval      : {results['routed_for_approval']}")
    print(f"  Errors                : {results['errors']}")
    print(f"{'─'*50}\n")


if __name__ == "__main__":
    main()
