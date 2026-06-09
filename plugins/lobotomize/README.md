# Lobotomize

Lobotomize is a local Codex plugin for curating project memory.

It separates historical Codex logs from an intentional, editable memory file:

```text
.project-memory/memory.json
```

Use it to decide what Codex should keep, clarify, adapt, ignore, or treat as sensitive for a project. For teams, commit the curated memory file after reviewing sensitive entries.

In Codex, activate it with:

```text
lobotomize
```

## First Commands

```bash
python3 scripts/project_memory.py list-projects
python3 scripts/project_memory.py card --project /path/to/project
python3 scripts/project_memory.py source-pack --project /path/to/project --limit 20
python3 scripts/project_memory.py list-threads --project /path/to/project
python3 scripts/project_memory.py show --project /path/to/project
python3 scripts/project_memory.py init --project /path/to/project
python3 scripts/project_memory.py apply --project /path/to/project --proposal /path/to/approved-proposal.json
```

## Team Memory

The curated file is designed to be shared through the repository. It should contain decisions, conventions, domain vocabulary, recurring instructions, and things Codex should adapt to.

It should not contain credentials, secrets, raw transcripts, or private data.

## Author

Built by Ikala / Ikaladev.

X: [@ikaladev](https://x.com/ikaladev)
