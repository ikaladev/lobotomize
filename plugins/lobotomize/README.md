# Lobotomize

Lobotomize is a local Codex plugin for curating and exporting project memory across AI coding tools.

It separates historical Codex logs from an intentional, editable memory file:

```text
.project-memory/memory.json
```

Use it to decide what Codex and other AI coding tools should keep, clarify, adapt, ignore, or treat as sensitive for a project. For teams, commit the curated memory file after reviewing sensitive entries.

In Codex, activate it with:

```text
lobotomize
```

## First Commands

```bash
python3 scripts/project_memory.py list-projects
python3 scripts/project_memory.py card --project /path/to/project
python3 scripts/project_memory.py scan-context --project /path/to/project
python3 scripts/project_memory.py context-pack --project /path/to/project
python3 scripts/project_memory.py merge-memories --project /path/to/project
python3 scripts/project_memory.py merge-memories --project /path/to/project --proposal-out /path/to/merged-proposal.json
python3 scripts/project_memory.py plan-exports --project /path/to/project
python3 scripts/project_memory.py plan-exports --project /path/to/project --format json --include-content
python3 scripts/project_memory.py apply-export-plan --plan /path/to/approved-export-plan.json --approved
python3 scripts/project_memory.py source-pack --project /path/to/project --limit 20
python3 scripts/project_memory.py list-threads --project /path/to/project
python3 scripts/project_memory.py show --project /path/to/project
python3 scripts/project_memory.py init --project /path/to/project
python3 scripts/project_memory.py apply --project /path/to/project --proposal /path/to/approved-proposal.json
```

## Team Memory

The curated file is designed to be shared through the repository. It should contain decisions, conventions, domain vocabulary, recurring instructions, and things Codex should adapt to.

It should not contain credentials, secrets, raw transcripts, or private data.

## Safety / Privacy

Lobotomize separates source material from approved memory. Conversation history, detected rule files, and exported target files are treated as review inputs until the user approves a proposal or export plan.

The tool refuses export writes unless an export plan is explicitly approved. Secret-like values are flagged in context packs and previews are redacted. Sensitive entries should stay out of shared assistant rules unless the user explicitly approves each one.

## V2 Prototype Commands

`scan-context` detects known memory and instruction surfaces for AI coding tools.

`context-pack` normalizes detected files into a read-only evidence pack for review.

`merge-memories` fuses all detected project memory/rule files into one structured analysis grouped as keep, clarify, adapt, ignore, and sensitive. It can also save a merged proposal for later approval.

`plan-exports` creates a dry-run plan that maps approved Lobotomize memory into tool-specific files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor rules, Continue rules, Copilot instructions, Cline memory bank notes, and Aider conventions. It does not write those files.

To apply exports, first generate a JSON plan with `--include-content`, review it, save it as the approved plan, and then run `apply-export-plan --approved`. Without `--approved`, Lobotomize refuses to write.

## Author

Built by Ikala / Ikaladev.

X: [@ikaladev](https://x.com/ikaladev)
