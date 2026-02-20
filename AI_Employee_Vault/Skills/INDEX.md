---
title: "Skills Index — AI Employee Bronze Tier"
version: "1.0.0"
tier: "bronze"
last_updated: "2026-02-19"
---

# 🧩 Agent Skills Index

> All AI Employee capabilities are implemented as **reusable, modular skills**.
> Each skill has a defined interface, failure-handling strategy, and
> Silver/Gold/Platinum upgrade path.

---

## Architecture Layer Map

```
┌─────────────────────────────────────────────────┐
│           PERCEPTION LAYER                       │
│  • Vault Reader  (read vault files/dirs)         │
└──────────────────────┬──────────────────────────┘
                       │ task descriptors
┌──────────────────────▼──────────────────────────┐
│           REASONING LAYER                        │
│  • Task Classifier  (type, priority, action)     │
│  • Plan Generator   (checklist creation)         │
└──────────────────────┬──────────────────────────┘
                       │ classified tasks + plans
┌──────────────────────▼──────────────────────────┐
│           ACTION LAYER                           │
│  • Action Processor  (pipeline orchestration)    │
│  • File Mover        (safe file operations)      │
│  • Vault Writer      (write vault files)         │
│  • Dashboard Updater (refresh Dashboard.md)      │
└─────────────────────────────────────────────────┘
```

---

## Skills Registry

| ID | Name | Layer | File | Status |
|----|------|-------|------|--------|
| `vault_reader` | Vault Reader | Perception | `vault_reader.md` | ✅ Active |
| `vault_writer` | Vault Writer | Action | `vault_writer.md` | ✅ Active |
| `task_classifier` | Task Classifier | Reasoning | `task_classifier.md` | ✅ Active |
| `plan_generator` | Plan Generator | Reasoning | `plan_generator.md` | ✅ Active |
| `file_mover` | File Mover | Action | `file_mover.md` | ✅ Active |
| `action_processor` | Action Processor | Orchestration | `action_processor.md` | ✅ Active |
| `dashboard_updater` | Dashboard Updater | Action | `dashboard_updater.md` | ✅ Active |

---

## Skill Development Contract

All skills must follow this contract:

### Required Fields (YAML frontmatter)
```yaml
skill_id:      unique snake_case identifier
skill_name:    Human-readable name
version:       semver (1.0.0)
tier:          bronze | silver | gold | platinum
category:      perception | reasoning | action | orchestration
layer:         perception | reasoning | action
implementation: module::ClassName
status:        active | beta | deprecated
```

### Required Sections (Markdown body)
1. **Purpose** — What does this skill do and why?
2. **Inputs** — Parameter table with types
3. **Outputs** — Return types and formats
4. **Failure Handling** — Scenario/behaviour table
5. **Implementation Notes** — Code with `[LLM_HOOK]` markers
6. **Reusability Notes** — How to use from other skills
7. **Future Tier Compatibility** — Upgrade path table
8. **Example Usage** — Runnable code snippet

### Bronze Tier Constraints
- No external network calls
- No LLM API calls (rule-based only)
- DRY_RUN mode must be respected
- All errors caught and logged (never raise to caller)
- Copy-verify-delete for any file moves

---

## How to Add a New Skill

1. Create `Skills/{skill_id}.md` using the contract above
2. Implement the class in `claude_agent.py`
3. Add an entry to this INDEX.md
4. Update `action_processor.md` if it's a pipeline step
5. Test with `DRY_RUN=true` first

---

*Skills Index v1.0.0 | Bronze Tier | 7 Active Skills*
