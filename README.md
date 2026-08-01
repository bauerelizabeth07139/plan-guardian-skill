<p align="center">
  <img src="./assets/logo.svg" width="120" alt="Plan Guardian"/>
</p>

<h1 align="center">Plan Guardian</h1>

<p align="center">
  <strong>Strict planning  -  Memoryless verification  -  Subagent-first execution</strong><br/>
  A Codex skill that enforces verifiable planning, then validates completion with independent memoryless subagents.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.9.0-blue" alt="Version"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
  <img src="https://img.shields.io/badge/Codex-Skill-purple" alt="Codex Skill"/>
  <img src="https://img.shields.io/badge/Platform-Codex-black" alt="Platform"/>
</p>

---

## What It Does

Plan Guardian is a **Codex skill** that wraps every user request in a strict 7-step planning and verification workflow. Instead of letting Codex respond directly, it forces a closed-loop process: plan -> execute -> verify -> report.

### Core Functionality

| Function | Description |
|----------|-------------|
| **Strict Planning** | Every request produces exactly 7 numbered steps with deliverables, dependencies, and risks |
| **Acceptance Criteria** | Each step gets binary pass/fail criteria defined before execution begins |
| **Worker Delegation** | Implementation is delegated to spawned worker subagents, keeping the main loop lightweight |
| **3-Phase Verification** | Each verification step uses 3 separate subagents (READ & STRUCTURE -> SYNTAX & CONNECTIONS -> FUNCTIONAL TEST & VISUAL CHECK) |
| **Context-Aware Splitting** | Large file sets are split across multiple subagents to stay within the 258k token limit |
| **Multimodal Detection** | Step 0 auto-discovers credentials from Codex config (~/.codex/auth.json + config.toml), probes for multimodal support, and selects the best match; falls back to the parent when credentials are not available |
| **FAIL -> Fix -> Re-Verify** | When verification fails, a fix plan is created, executed by a new worker, and re-verified (up to 5 cycles) |

### Why Use It?

- Eliminates silent failures on complex tasks
- Prevents self-verification bias (main loop never checks its own work)
- Forces observable, binary acceptance criteria before execution starts
- Scales to multi-file, multi-step tasks with parallel worker subagents
- Context-aware: splits large tasks across multiple subagents to avoid context overflow

---

## Why Plan Guardian?

Complex tasks fail silently when plans are loose and verification is shallow. Plan Guardian eliminates that by forcing a **closed-loop workflow**:

- **Strict Planning**  -  Every request starts with a numbered plan, dependencies, and acceptance criteria
- **Subagent-First**  -  Main loop stays lightweight; workers and verifiers handle the heavy lifting
- **3-Phase Verification**  -  Independent subagents verify each phase with zero prior context
- **Multimodal-Aware**  -  Visual tasks use multimodal models when detected; Step 0 auto-reads Codex config for credential discovery
- **FAIL -> Fix -> Re-Verify**  -  When verification fails, a fix plan is created and re-verified (up to 5 cycles)
- **Context-Aware**  -  Large tasks are split across multiple subagents to stay within the 258k token limit

---

## Architecture

```mermaid
flowchart TD
    A[User Request] --> B[Clarify Intent]
    B --> C[Draft Plan + Acceptance Criteria]
    C --> D{Execute}
    D --> E[Worker Subagent<br/>Implementation]
    E --> F[Phase 1: READ & STRUCTURE]
    F --> G[Phase 2: SYNTAX & CONNECTIONS]
    G --> H[Phase 3: FUNCTIONAL TEST & VISUAL CHECK]
    H -->|PASS| I{All Steps OK?}
    H -->|FAIL| J[FAIL -> Plan Fix -> New Worker] --> E
    I -->|Yes| K[[x] Final Report]
    I -->|No| D
```

---

## Quick Start

There are **two installation levels**. Choose based on how you want the skill to behave.

### System Level  -  Auto-activates on every request (Recommended)

**Two files must be installed:**

```bash
# Step 1: Install the skill
# Linux/macOS
cp -r plan-guardian-skill ~/.codex/skills/.system/plan-guardian

# Windows (PowerShell)
robocopy plan-guardian-skill "$env:USERPROFILE\.codex\skills\.system\plan-guardian" /E
```

```bash
# Step 2: Install the global AGENTS.md (REQUIRED for subagent spawning)
# Linux/macOS
cp AGENTS.global.md ~/.codex/AGENTS.md

# Windows (PowerShell)
Copy-Item AGENTS.global.md "$env:USERPROFILE\.codex\AGENTS.md" -Force
```

**Why two files?**
- `SKILL.md` tells Codex WHAT to do (7-step workflow)
- `AGENTS.global.md` tells Codex HOW to do it (spawn subagents, detect multimodal, 3-phase verification, context management)
- Without AGENTS.md, the model will plan but NOT spawn workers or verifiers

- Codex loads this on **every request** automatically  -  no exceptions
- The 7-step workflow (Step 0 -> Step 7) applies to all tasks, including simple questions
- Skill appears as `plan-guardian` in Codex's system skills list
- **This is the forced mode  -  no way to skip it once installed**

### User Level  -  Manual invocation only

```bash
# Linux/macOS
cp -r plan-guardian-skill ~/.codex/skills/plan-guardian

# Windows (PowerShell)
robocopy plan-guardian-skill "$env:USERPROFILE\.codex\skills\plan-guardian" /E
```

- **Not** automatically activated  -  you choose when to use it
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

##  How It Works

| Step | What Happens | Who Does It |
|------|-------------|-------------|
| **0. Detect Model Capabilities** | Probe whether current model supports multimodal (image) input | Diagnostic Subagent |
| **1. Clarify Intent** | Restate user request in one paragraph | Main Loop |
| **2. Draft Plan** | Exactly 7 numbered steps with dependencies, risks, and deliverables | Main Loop |
| **3. Acceptance Criteria** | Binary pass/fail criteria for every step | Main Loop |
| **4. Execute** | Delegate all steps to Worker subagents | **Worker Subagent** |
| **5. Verify (3 Phases)** | Phase 1: READ & STRUCTURE -> Phase 2: SYNTAX & CONNECTIONS -> Phase 3: FUNCTIONAL TEST & VISUAL CHECK (split by scope) | **3+ Verifier Subagents** |
| **6. FAIL -> Fix -> Re-Verify** | If verifier FAILs: create fix plan, spawn new worker, spawn new verifiers (up to 5 cycles) | **New Workers + Verifiers** |
| **7. Report** | Present plan, status, evidence, and remediation actions | Main Loop |

---

## Subagent Roles

### Planner (Main Loop)
- Clarifies intent, drafts plan, coordinates execution
- **Never** pastes large files or logs  -  delegates to workers
- **Never** self-verifies  -  all verification uses spawn_agent
- Estimates context before spawning subagents (258k token limit)

### Worker Subagents
- Implement, build, fix, edit, inspect files, run tests
- **Text/code tasks**: spawn WITHOUT model override (inherits parent)
- **Visual tasks** (images, UI, frontend, screenshots, diagrams, PDFs): spawn WITH model override when Step 0 = NOT_MULTIMODAL

### Verifier Subagents (3 Phases)
- **Phase 1 (READ & STRUCTURE)**: Read files, check required fields, verify values
- **Phase 2 (SYNTAX & CONNECTIONS)**: Check syntax, bindings, event handlers, APIs, imports, routes
- **Phase 3 (FUNCTIONAL TEST & VISUAL CHECK)**: Split by scope (functional areas or interaction groups). Run artifact, interact with elements, screenshot each interface, compare to pre-written expectations. Keep each subagent small and time-bounded.
- Each phase is a separate subagent with only: acceptance criteria + previous phase summary
- **ALWAYS use multimodal model when available**
- **Write expected results BEFORE testing  -  do not change after seeing actual**

---

## Codex++ integration (Plan Guardian)

- Designed for use inside the Codex (Codex++) environment.
- Step 0 detection is integrated with the local Codex++ proxy. When no base URL is configured, it defaults to `http://127.0.0.1:8788/v1` (provider-agnostic).
- The detection flow validates the environment endpoint first, then validates the model-specific endpoint when known (provider-agnostic; depends on configured backend).
- Use the quick-check examples below to confirm your Codex++ setup before running longer workflows.

## Model Selection

Step 0 uses available-model discovery by default: list candidates from the configured endpoint, probe for multimodal support, and prefer the best match. The script automatically reads credentials from ~/.codex/auth.json (API key) and ~/.codex/config.toml (base URL, model name) when running inside the Codex desktop app with a custom provider (e.g., Codex++ proxy). The Codex++ proxy port is dynamic and read from config.toml at runtime.

Credential resolution order:
1. Command-line arguments
2. Environment variables (OPENAI_BASE_URL, OPENAI_API_KEY, MIMO_BASE_URL, MIMO_API_KEY)
3. ~/.mimo2codex/.env (Codex++ key file)
4. ~/.codex/config.toml + ~/.codex/auth.json (Codex desktop app config)

Quick check:
`ash
python scripts/detect_multimodal.py
`

`
Step 0 result:
 MULTIMODAL     -> Visual/verification subagents use detected multimodal model
 NOT_MULTIMODAL -> All subagents inherit parent model
 UNKNOWN        -> All subagents inherit parent model
`

### Subagent Model Selection

| Subagent Type | Model |
|---------------|-------|
| Step 0 detection | Parent model (no override) |
| Text/code workers | Inherit parent |
| Visual tasks (UI, frontend, beautification) | Multimodal model (when available) |
| Screenshot/visual verification | Multimodal model (when available) |
| Other verification | Inherit parent |

## Context Management (258k Token Limit)

Each subagent has a 258k token context limit. Do NOT get close to this limit.

| Task Size | Files | Subagents |
|-----------|-------|-----------|
| Small | 1-2 files | 1 subagent |
| Medium | 3-5 files | 2-3 subagents |
| Large | 6+ files | 4+ subagents |

Each subagent returns a **summary**, not full file content. Pass summaries to the next subagent.

---

##  Timeout Rules

| Verifier Type | timeout_ms | Retry |
|---------------|-----------|-------|
| Per-step (Phase 1-3) | 120,000 (2 min) | +60s each retry |
| Final gate | 180,000 (3 min) | +60s each retry |
| Maximum | 360,000 (6 min) |  -  |

---

## Emoji and encoding policy

- Emoji is allowed.
- Explicitly prevent garbled output: ensure UTF-8 encoding on files, terminals, and logs.
- If the rendering environment is unknown, prefer ASCII-safe wording, or normalize non-ASCII characters to ASCII equivalents.
- For Chinese/CJK content, verify CJK encoding (UTF-8) to avoid mojibake; when uncertain, use sanitized ASCII-safe fallbacks.

## Structure

```
plan-guardian-skill/
 SKILL.md                              # Core skill instructions (7-step workflow)
 AGENTS.md                             # Repo-level agent guidelines
    AGENTS.global.md                  # Global template (install to ~/.codex/AGENTS.md)
 agents/
    openai.yaml                       # UI metadata (display name, icon, default prompt)
 assets/
    plan-guardian-small.svg           # Small icon
    logo.png                          # Large icon
    logo.svg                          # Vector logo
 references/
    memoryless_review.md              # Strict verifier protocol & independence rules
    plan_protocol.md                  # Acceptance criteria patterns & verifier prompt template
 scripts/
    detect_multimodal.py              # Runtime multimodal model detection via API probe
    plan_guardian.py                  # Sample plan generator (demo/testing)
    validate_skill.py                 # Local validator (checks SKILL.md frontmatter & required files)
 LICENSE                               # MIT license
 README.md                             # This file
```

---

## Hard Rules

1. Never respond to the user without completing the Final Gate (Step 7)
2. Never self-verify  -  all verification uses subagents with fork_context=false
3. Never reuse a verifier that returned FAIL  -  follow the Fix Cycle
4. Never pass conversation history to verifiers  -  they get criteria + previous phase summaries only
5. Never assume a step passed without verifier evidence
6. Plan must have **exactly 7 steps**  -  no shortcuts
7. When verification fails -> Fix Cycle (up to 5 cycles)
8. After 5 fix cycles -> escalate honestly, never silently give up
9. If a verifier times out -> treat as FAIL, increase timeout by 60s, retry with new verifier
10. Estimate context before spawning subagents  -  do not exceed 258k token limit

---

## License

MIT  -  Use it, fork it, improve it.

---

<p align="center">
  <sub>Built for <a href="https://github.com/openai/codex">Codex</a>  -  Enforcing rigor since 2026</sub>
</p>
