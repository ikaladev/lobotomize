# Lobotomize v2 Product Spec

## Positioning

Lobotomize v2 is a memory command center for AI coding tools.

It helps users and teams inspect, curate, compare, and synchronize project memory across Codex, Claude Code, Cursor, OpenCode, Gemini CLI, Qwen Code, Windsurf/Devin, Cline, Continue, Aider, GitHub Copilot, and future tools with documented memory surfaces.

The core promise stays the same: nothing becomes project memory until the user approves it.

## Goals

- Show the current memory/context state for a project across supported tools.
- Separate raw conversation history from approved project memory.
- Propose ideal memory from existing files and approved conversation/source packs.
- Let the user approve, reject, or request adjustments before writing.
- Export the same curated intent into each tool's native format.
- Help teams share durable project knowledge while keeping private/local memory private.
- Detect secrets, personal data, stale assumptions, and conflicts.

## Non-Goals

- Do not bypass provider privacy controls.
- Do not scrape or rewrite cloud memories without official access.
- Do not pretend every AI app has the same memory model.
- Do not auto-commit or publish memory files.
- Do not store raw transcripts as team memory.

## Core Workflow

1. Scan the project.
2. Detect known memory surfaces.
3. Show a memory dashboard grouped by tool and scope.
4. Ask whether the user wants to create or improve memory.
5. Build a curated proposal from approved sources only.
6. Show the proposal with target exports and risk flags.
7. Apply only after explicit approval.
8. Validate generated files and report what changed.

## Adapter Interface

Each tool adapter should implement as many of these operations as the platform supports:

```ts
interface MemoryAdapter {
  id: string;
  displayName: string;
  detect(projectPath: string): Promise<DetectionResult>;
  read(projectPath: string): Promise<MemoryArtifact[]>;
  normalize(artifacts: MemoryArtifact[]): Promise<CanonicalMemoryEntry[]>;
  planWrite(entries: CanonicalMemoryEntry[]): Promise<WritePlan>;
  apply(plan: ApprovedWritePlan): Promise<ApplyResult>;
  validate(projectPath: string): Promise<ValidationResult>;
}
```

Adapters must declare:

- Supported read/write surfaces.
- Whether a surface is private, team-shared, or unknown.
- Whether writing is file-based, UI-based, API-based, or unsupported.
- Whether a memory format supports activation metadata.
- Whether external official docs confirm the behavior.

## Initial Adapter Set

### Phase 1: Read-Only Discovery

- Codex: `.project-memory/memory.json`, current Lobotomize project memory.
- AGENTS.md: root and nested files as portable project instructions.
- Claude Code: `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/*.md`.
- Cursor: `.cursor/rules/*.mdc`.
- OpenCode: `AGENTS.md`, `opencode.json`, `opencode.jsonc`, global references as metadata only.
- Gemini CLI: `GEMINI.md`, `.gemini/settings.json`, configured context file names.
- Windsurf/Devin: `.devin/rules/*.md`, `.windsurf/rules/*.md`, `AGENTS.md`; local memories read only when explicitly allowed.
- Cline: `memory-bank/*.md`, `.clinerules/*.md`.
- Continue: `.continue/rules/*.md`.
- Aider: `.aider.conf.yml` read entries and convention files.
- GitHub Copilot: `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`.

Prototype command:

```bash
python3 plugins/lobotomize/scripts/project_memory.py scan-context --project /path/to/project
python3 plugins/lobotomize/scripts/project_memory.py scan-context --project /path/to/project --format json
python3 plugins/lobotomize/scripts/project_memory.py context-pack --project /path/to/project --include-preview
python3 plugins/lobotomize/scripts/project_memory.py merge-memories --project /path/to/project
python3 plugins/lobotomize/scripts/project_memory.py merge-memories --project /path/to/project --proposal-out /path/to/merged-proposal.json
```

`context-pack` scans file content for secret-like patterns, reports sensitivity flags, and redacts preview text.

`merge-memories` fuses all detected project memory/rule files for the same project into a structured analysis. It groups entries as `keep`, `clarify`, `adapt`, `ignore`, and `sensitive`, preserves source provenance, reports review items, and can emit a `.project-memory/memory.json` proposal for later approval.

### Phase 2: Approved Writes

- Generate or update `.project-memory/memory.json`.
- Generate or update `AGENTS.md` as a portable baseline.
- Generate tool-specific exports only for adapters with documented file formats.
- Preserve manual sections when possible.
- Add comments or frontmatter identifying generated blocks and source memory IDs.

Prototype dry-run command:

```bash
python3 plugins/lobotomize/scripts/project_memory.py plan-exports --project /path/to/project
python3 plugins/lobotomize/scripts/project_memory.py plan-exports --project /path/to/project --targets agents,claude,cursor --format json
python3 plugins/lobotomize/scripts/project_memory.py plan-exports --project /path/to/project --targets agents,claude,cursor --format json --include-content
```

The command only plans writes. Actual file updates require a separate approval step.

Prototype approved apply command:

```bash
python3 plugins/lobotomize/scripts/project_memory.py apply-export-plan --plan /path/to/approved-export-plan.json --approved
```

The apply command refuses to write without `--approved`, validates that the plan uses the v2 export-plan schema, requires full generated content in the plan, and rejects paths that escape the project root.

### Phase 3: Team Memory Pack

- Create a portable `.project-memory/pack.json`.
- Include canonical entries, source provenance, target export preferences, redaction state, and adapter compatibility.
- Let teams review the pack before committing it.

### Phase 4: Research-Gap Adapters

- Kimi: add only after an official project memory, rule, or context format is verified.
- Google Antigravity: add only after official docs or verified local behavior confirm the storage and controls.
- Other tools: add by adapter contract, not by one-off scripts.

## User Experience

### Project Card

The card should show:

- Project name and path.
- Memory health: none, partial, healthy, conflicting, sensitive-risk.
- Detected tools.
- Shareable memory files.
- Private memory files.
- Missing recommended surfaces.
- Last approved update.

### Tool Cards

Each tool card should show:

- Tool name.
- Detected memory files or settings.
- Scope and visibility.
- Whether Lobotomize can read it.
- Whether Lobotomize can write it.
- Main risks or conflicts.

### Proposal Review

The proposal should group entries by action:

- Keep.
- Clarify.
- Adapt.
- Ignore.
- Sensitive/private.
- Export to selected tools.

Every proposed write should be visible before applying.

## Safety Rules

- Ask before reading conversation history.
- Ask before creating memory if none exists.
- Ask before improving memory if memory exists.
- Never write without explicit approval.
- Never export secrets, tokens, private keys, or raw transcripts.
- Never convert private local preferences into team-shared memory without explicit approval.
- Mark uncertain inferences as uncertain.
- Keep generated memory concise and operational.

## Canonical File Layout

```text
.project-memory/
  memory.json
  pack.json
  exports/
    AGENTS.md
    CLAUDE.md
    GEMINI.md
    cursor/
      project.mdc
    continue/
      project.md
```

This layout is a staging area. Actual writes to native tool locations should still require user approval.

## Recommended v2 Milestones

1. Add read-only scanner for known memory surfaces.
2. Add canonical normalization, memory fusion, and conflict reporting.
3. Add `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor, Continue, Cline, and Copilot export plans.
4. Add approved write flow with diff preview.
5. Add team memory pack export/import.
6. Add optional UI cards once the Codex plugin surface supports richer custom display.
7. Revisit Kimi and Antigravity after official docs or local storage behavior are confirmed.
