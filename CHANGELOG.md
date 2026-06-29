# Changelog

## 0.2.0

Lobotomize v2 expands the project from a Codex-only memory curator into a cross-tool memory manager for AI coding workflows.

### Added

- Research notes for how major AI coding tools handle memory, rules, instructions, context, and persistence.
- A shared memory taxonomy for native memory, project instructions, private rules, structured memory, runtime context, references, and session state.
- A v2 product spec with adapter boundaries, safety rules, export targets, and research-gap adapters.
- `scan-context` command to detect memory/rule surfaces across AI coding tools.
- `context-pack` command to normalize detected files into a read-only evidence pack.
- `merge-memories` command to fuse all detected project memories/rules into one structured analysis and proposal.
- Secret-like pattern detection for context packs, with redacted previews.
- `plan-exports` command to create dry-run export plans from approved Lobotomize memory.
- `apply-export-plan` command to apply an explicitly approved export plan.
- Export targets for `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor rules, Continue rules, GitHub Copilot instructions, Cline memory bank notes, and Aider conventions.

### Changed

- Plugin metadata now describes Lobotomize as a multi-tool project memory manager.
- The `lobotomize` skill now includes the v2 discovery, context pack, export plan, and approved apply flow.

### Safety

- Export plans do not write files by default.
- Applying exports requires `--approved`.
- Export application validates the v2 plan schema.
- Export application rejects paths that escape the project root.
- Kimi and Google Antigravity remain research-gap adapters until an official, user-editable project memory/rules surface is verified.
