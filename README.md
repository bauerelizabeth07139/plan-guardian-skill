<p align="center">
  <img src="./assets/logo.svg" width="120" alt="Plan Guardian"/>
</p>

<h1 align="center">ğŸ›¡ï¸?Plan Guardian</h1>

<p align="center">
  <strong>Strict planning Â· Memoryless verification Â· Subagent-first execution</strong><br/>
  A Codex skill that enforces verifiable planning, then validates completion with independent memoryless subagents.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.3.0-blue" alt="Version"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
  <img src="https://img.shields.io/badge/Codex-Skill-purple" alt="Codex Skill"/>
  <img src="https://img.shields.io/badge/Platform-Codex-black" alt="Platform"/>
</p>

---

## ğŸ“– What It Does

Plan Guardian is a **Codex skill** that wraps every user request in a strict 7-step planning and verification workflow. Instead of letting Codex respond directly, it forces a closed-loop process: plan â†?execute â†?verify â†?report.

### Core Functionality

| Function | Description |
|----------|-------------|
| **Strict Planning** | Every request produces exactly 7 numbered steps with deliverables, dependencies, and risks |
| **Acceptance Criteria** | Each step gets binary pass/fail criteria defined before execution begins |
| **Worker Delegation** | Implementation is delegated to spawned worker subagents, keeping the main loop lightweight |
| **Memoryless Verification** | Independent verifier subagents (with `fork_context=false`) check each step with zero prior context |
| **Final Gate** | At least 2 independent verifiers check ALL criteria before the response is delivered |
| **Re-Planning Protocol** | On failure, a new plan is drafted (not blind retry) and re-verified until all pass or 3 cycles exhausted |
| **Multimodal Detection** | Step 0 probes the model API to determine image support, then applies the result to all worker/verifier model selections |

### Why Use It?

- Eliminates silent failures on complex tasks
- Prevents self-verification bias (main loop never checks its own work)
- Forces observable, binary acceptance criteria before execution starts
- Scales to multi-file, multi-step tasks with parallel worker subagents

---

## âœ?Why Plan Guardian?

Complex tasks fail silently when plans are loose and verification is shallow. Plan Guardian eliminates that by forcing a **closed-loop workflow**:

- ğŸ¯ **Strict Planning** â€?Every request starts with a numbered plan, dependencies, and acceptance criteria
- ğŸ¤– **Subagent-First** â€?Main loop stays lightweight; workers and verifiers handle the heavy lifting
- ğŸ” **Memoryless Verification** â€?Independent subagents verify completion with zero prior context
- ğŸ§  **Multimodal-First** â€?Workers prefer multimodal models; verifiers always use them
- ğŸ”„ **Re-Planning Protocol** â€?When verification fails, a new plan is drafted (not blind retry) and re-verified until all pass

---

## ğŸ—ï¸?Architecture

```mermaid
flowchart TD
    A[User Request] --> B[Clarify Intent]
    B --> C[Draft Plan + Acceptance Criteria]
    C --> D{Execute}
    D --> E[Worker Subagent<br/>Implementation]
    E --> F[Memoryless Verifier<br/>Per-Step Check]
    F -->|PASS| G{All Steps OK?}
    F -->|FAIL| H["Re-Plan (new 7-step plan)"] --> D
    G -->|Yes| I[Final Gate<br/>2+ Independent Verifiers]
    G -->|No| D
    I -->|ALL PASS| J[âœ?Final Report]
    I -->|FAIL| H
```

---

## ğŸš€ Quick Start

There are **two installation levels**. Choose based on how you want the skill to behave.

### System Level â€?Auto-activates on every request (Recommended)

```bash
# Linux/macOS
cp -r plan-guardian-skill ~/.codex/skills/.system/plan-guardian

# Windows (PowerShell)
robocopy plan-guardian-skill "$env:USERPROFILE\.codex\skills\.system\plan-guardian" /E
```

- Codex loads this on **every request** automatically â€?no exceptions
- The 7-step workflow (Step 0 â†?Step 7) applies to all tasks, including simple questions
- Skill appears as `plan-guardian` in Codex's system skills list
- **This is the forced mode â€?no way to skip it once installed**

### User Level â€?Manual invocation only

```bash
# Linux/macOS
cp -r plan-guardian-skill ~/.codex/skills/plan-guardian

# Windows (PowerShell)
robocopy plan-guardian-skill "$env:USERPROFILE\.codex\skills\plan-guardian" /E
```

- **Not** automatically activated â€?you choose when to use it
- Invoke explicitly with `$plan-guardian <your task>`
- Use when you want strict planning only for complex tasks

### Usage (User Level)

```
$plan-guardian implement a multi-file refactoring with tests
```

### Validate Installation

```bash
python scripts/validate_skill.py .
```

---

## ğŸ“‹ How It Works

| Step | What Happens | Who Does It |
|------|-------------|-------------|
| **0. Detect Model Capabilities** | Probe whether current model supports multimodal (image) input | Diagnostic Subagent |
| **1. Clarify Intent** | Restate user request in one paragraph | Main Loop |
| **2. Draft Plan** | Exactly 7 numbered steps with dependencies, risks, and deliverables | Main Loop |
| **3. Acceptance Criteria** | Binary pass/fail criteria for every step | Main Loop |
| **4. Execute** | Delegate all steps to Worker subagents | **Worker Subagent** |
| **5. Per-Step Verification** | Independent memoryless verifier checks each step | **Verifier Subagent** |
| **6. Final Gate** | â‰? memoryless verifiers check ALL criteria | **Verifier Subagents** |
| **7. Report** | Present plan, status, evidence, and remediation actions | Main Loop |

---

## ğŸ§© Subagent Roles

### Planner (Main Loop)
- Clarifies intent, drafts plan, coordinates execution
- **Never** pastes large files or logs â€?delegates to workers
- **Never** self-verifies â€?all verification uses spawn_agent

### Worker Subagents
- Implement, build, fix, edit, inspect files, run tests
- **Prefer multimodal model by default** â€?fall back to parent for pure text/code only
- **Visual rule**: MUST use multimodal model for image/UI/PDF tasks

### Verifier Subagents
- Independent, memoryless (`fork_context=false`)
- Receive only: deliverables + acceptance criteria
- Output: `PASS` or `FAIL` with exact reason
- **Always use multimodal model** â€?code, files, and artifacts all benefit from visual understanding

---

## ğŸ”§ Model Selection

```
Step 0 detection result:
â”œâ”€â”€ MULTIMODAL   â†?All workers/verifiers inherit parent model
â”œâ”€â”€ NOT_MULTIMODAL â†?Visual tasks override to multimodal model; text tasks inherit
â””â”€â”€ UNKNOWN      â†?Assume multimodal, inherit parent model
```

---

## â±ï¸ Timeout Rules

| Verifier Type | timeout_ms | Retry |
|---------------|-----------|-------|
| Per-step (Step 5) | 120,000 (2 min) | +60s each retry |
| Final gate (Step 6) | 180,000 (3 min) | +60s each retry |
| Maximum | 360,000 (6 min) | â€?|

---

## ğŸ“ Structure

```
plan-guardian-skill/
â”œâ”€â”€ SKILL.md                              # Core skill instructions (7-step workflow)
â”œâ”€â”€ AGENTS.md                             # Repo-level agent guidelines
â”œâ”€â”€ agents/
â”?  â””â”€â”€ openai.yaml                       # UI metadata (display name, icon, default prompt)
â”œâ”€â”€ assets/
â”?  â”œâ”€â”€ plan-guardian-small.svg           # Small icon
â”?  â”œâ”€â”€ logo.png                          # Large icon
â”?  â””â”€â”€ logo.svg                          # Vector logo
â”œâ”€â”€ references/
â”?  â”œâ”€â”€ memoryless_review.md              # Strict verifier protocol & independence rules
â”?  â””â”€â”€ plan_protocol.md                  # Acceptance criteria patterns & verifier prompt template
â”œâ”€â”€ scripts/
â”?  â”œâ”€â”€ detect_multimodal.py              # Runtime multimodal model detection via API probe
â”?  â”œâ”€â”€ plan_guardian.py                  # Sample plan generator (demo/testing)
â”?  â””â”€â”€ validate_skill.py                 # Local validator (checks SKILL.md frontmatter & required files)
â”œâ”€â”€ LICENSE                               # MIT license
â””â”€â”€ README.md                             # This file
```

---

## ğŸ›¡ï¸?Hard Rules

1. â?Never respond to the user without completing the Final Gate (Step 6)
2. â?Never self-verify â€?all verification uses `spawn_agent` with `fork_context=false`
3. â?Never reuse a verifier that returned FAIL â€?follow the Re-Planning Protocol
4. â?Never pass conversation history to verifiers â€?they get deliverables + criteria only
5. â?Never assume a step passed without verifier evidence
6. âœ?Plan must have **exactly 7 steps** â€?no shortcuts
7. âœ?If two final verifiers disagree â†?spawn a third
8. âœ?When verification fails â†?Re-Planning Protocol, never blind retry
9. âœ?After 3 re-plan cycles â†?escalate honestly, never silently give up
10. âœ?If a verifier times out â†?treat as FAIL, increase timeout by 60s, retry with new verifier

---

## ğŸ“œ License

MIT â€?Use it, fork it, improve it.

---

<p align="center">
  <sub>Built for <a href="https://github.com/openai/codex">Codex</a> Â· Enforcing rigor since 2026</sub>
</p>
