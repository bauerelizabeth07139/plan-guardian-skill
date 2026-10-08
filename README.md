# plan-guardian-skill

[![dsh.so risk](https://www.dsh.so/badge/plan-guardian-skill.svg)](https://www.dsh.so/artifact/plan-guardian-skill/)

**A mandatory 7-step plan, then verification by independent subagents** — as a
DeepSeek Harness plugin. The skill ships inside the bundle: install the plugin
and it is there, with the reference documents it cites.

*A Codex skill that enforces verifiable planning, then validates completion with
independent memoryless subagents.*

## Install

**DeepSeek Harness Desktop** — open **Plugins** in the sidebar, choose **Add
plugin**, and enter:

```
https://github.com/bauerelizabeth07139/plan-guardian-skill
```

Then switch the new **dsh-plan-guardian** bundle on. The Desktop app boots the
reserved `desktop` profile, so that is where it has to be enabled.

**dsh CLI** — install it into the profile you actually boot:

```sh
dsh plugin --profile web add bauerelizabeth07139/plan-guardian-skill
```

**No git on the machine?** pnpm resolves a git shorthand with `git ls-remote`,
which fails with `'git' is not recognized` when git is missing. Use the tarball
instead — that path is plain HTTPS:

```sh
dsh plugin --profile web add https://codeload.github.com/bauerelizabeth07139/plan-guardian-skill/tar.gz/master
```

The same address works in the Desktop **Add plugin** dialog. Replace `master`
with a commit SHA to pin an exact revision (`/tar.gz/<sha>`).

Uninstall with `dsh plugin --profile web remove dsh-plan-guardian`.

## The workflow

| Step | What happens |
|---|---|
| 0 | Establish verification capability — once per conversation |
| 1 | Restate the intent; name the core deliverable and the implicit requirements |
| 2 | Draft **exactly 7** concrete steps, implementation and verification kept apart |
| 3 | Give every step at least one **binary** acceptance criterion |
| 4 | Execute through **worker** subagents — they never see the criteria |
| 5 | Verify every deliverable through a **memoryless verifier** subagent |
| 6 | On FAIL, revise the plan, re-execute, re-verify |
| 7 | Report every step as PASS or FAIL, with evidence |

Hard rules the skill will not bend: never skip a step, never self-verify, never
produce fewer than 7 steps, never report a step as passed without verifier
evidence.

Full instructions: [`skills/plan-guardian/SKILL.md`](skills/plan-guardian/SKILL.md).
Supporting protocols: [`plan_protocol.md`](skills/plan-guardian/references/plan_protocol.md)
and [`memoryless_review.md`](skills/plan-guardian/references/memoryless_review.md).

## What changed for DeepSeek Harness

The 7 steps, the hard rules and the acceptance-criteria discipline are
unchanged. Two things are genuinely different:

1. **Step 0 is no longer a model probe.** In Codex the skill had to discover
   whether the session model could see images, by reading `~/.codex` and
   `~/.mimo2codex` and probing a model API. On DSH, every agent has `read_image`,
   so visual verification is always available and there is nothing to detect.
   The original probe is still in [`scripts/detect_multimodal.py`](scripts/detect_multimodal.py)
   for Codex users; the DSH skill does not call it.
2. **Subagent calls are the harness's.** `subagent` (memoryless) replaces
   `multi_agent_v1__spawn_agent(..., fork_context=false)`, and a forked
   subagent is explicitly forbidden for verifiers because it would inherit the
   conversation's assumptions. Workers report back on their own instead of a
   separate `wait_agent` call.

## Repository layout

| Path | Purpose |
|---|---|
| `index.js` | the DSH plugin: registers the bundled skill |
| `cordis.patch.yml` | the loader row that activates the plugin |
| `skills/plan-guardian/` | the skill in Harness tool names, with its references |
| `locale/{en,zh}.json` | card title and description for the plugin lists |
| `assets/icon.svg` | card artwork |
| `test/plugin.test.mjs` | static composition checks |
| `SKILL.md`, `references/`, `scripts/`, `agents/`, `AGENTS*.md` | the original Codex skill, unchanged |

## Development

No build step and no runtime dependencies — `@deepseek-ai/cordis` and
`@deepseek-ai/dsh-skill` are peers supplied by the Harness.

```sh
npm test    # node >= 22: manifest, card metadata, loader patch, skill, syntax
```

## Codex usage (unchanged)

The original files are still here, byte for byte:

```sh
git clone https://github.com/bauerelizabeth07139/plan-guardian-skill.git
cd plan-guardian-skill
cp -r . ~/.codex/skills/plan-guardian
cp AGENTS.global.md ~/.codex/AGENTS.md      # optional: the global instructions
python scripts/detect_multimodal.py         # Codex-only capability probe
python scripts/validate_skill.py .          # Codex-only skill validator
```

DSH also reads `AGENTS.md` — including a user-global `$DSH_HOME/AGENTS.md` — so
`AGENTS.md` / `AGENTS.global.md` remain useful if you want the rules applied
outside a skill invocation, with the subagent tool names swapped for the ones in
the mapping table above.

## License

[MIT](LICENSE)
