# Lobotomize v2 Memory Taxonomy

Lobotomize v2 should treat "memory" as a family of related persistence surfaces, not one file format.

## Memory Classes

### 1. Native Account Memory

Cloud or account-level memory maintained by the provider.

Examples:

- ChatGPT saved memories and reference chat history.
- Claude auto memory where available.
- Windsurf/Cascade auto-generated Memories.

Properties:

- Usually private to the user or workspace.
- May not expose a stable file path or write API.
- Needs explicit user control for reading, summarizing, editing, deleting, or disabling.

Lobotomize stance:

- Inspect only when the platform exposes it safely.
- Never claim a local file is the whole source of truth.
- Prefer summary, provenance, and user approval over automatic rewriting.

### 2. Project Instruction Memory

Repository files that tell an AI assistant how to work inside a project.

Examples:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.cursor/rules/*.mdc`
- `.continue/rules/*.md`
- `.devin/rules/*.md`
- `.windsurf/rules/*.md`
- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`

Properties:

- Often shareable with the team.
- Can have activation rules: always-on, manual, globs, path-specific, or model-decision.
- Conflicts are common when multiple assistants have overlapping files.

Lobotomize stance:

- This is the primary v2 synchronization layer.
- Preserve tool-specific metadata.
- Offer one canonical review view before writing to any target file.

### 3. Local Private Rules

User-level files that shape all projects or one local checkout.

Examples:

- `~/.claude/CLAUDE.md`
- `CLAUDE.local.md`
- `~/.config/opencode/AGENTS.md`
- `~/.codeium/windsurf/memories/global_rules.md`
- Cursor User Rules

Properties:

- Useful for personal preferences.
- Dangerous to commit.
- May override or combine with project rules.

Lobotomize stance:

- Mark as private by default.
- Never move into team memory without explicit approval.
- Show override risk when private rules conflict with repo rules.

### 4. Structured Project Memory

Purpose-built documentation that stores project knowledge.

Examples:

- Lobotomize `.project-memory/memory.json`
- Cline `memory-bank/*.md`
- `CONVENTIONS.md`
- architecture, setup, and runbook docs

Properties:

- More expressive than short rules.
- Easier for teams to review.
- Often the best source for durable architecture and product decisions.

Lobotomize stance:

- Use as the canonical authoring layer.
- Export concise subsets into assistant-specific rule files.
- Track provenance and sensitivity per memory entry.

### 5. Runtime Context and References

Context attached to a session but not necessarily stored as memory.

Examples:

- `@file` references.
- OpenCode references.
- Continue context providers.
- Included directories in Gemini CLI.
- MCP servers and connected docs.

Properties:

- Can be powerful but temporary.
- May expose large private surfaces.
- Usually needs permission boundaries.

Lobotomize stance:

- Inventory references as sources, not memory.
- Recommend stable docs when repeated context becomes important.

### 6. Session Compression and Checkpoints

Mechanisms that preserve or resume current work.

Examples:

- `/compress`
- `/clear`
- `/restore`
- shell history
- checkpointing
- conversation summaries

Properties:

- Useful for continuity.
- Not reliable as team memory.
- Can contain accidental or sensitive data.

Lobotomize stance:

- Use only as source material after consent.
- Convert into curated memory entries before sharing.

## Canonical Dimensions

Every memory artifact should be normalized across these dimensions:

- `tool`: source application, such as codex, claude, cursor, opencode, gemini, windsurf.
- `class`: native_memory, instruction_rule, local_private_rule, structured_memory, reference, session_state.
- `scope`: account, global_user, organization, team, repository, directory, file, session.
- `visibility`: private, team_shared, public, unknown.
- `storage`: file path, settings location, cloud surface, or unknown.
- `activation`: always, manual, glob, path, model_decision, referenced, unknown.
- `writer`: user, assistant, team_admin, provider, mixed.
- `provenance`: where the information came from.
- `confidence`: high, medium, low.
- `sensitivity`: normal, private, secret, regulated.
- `lifecycle`: keep, clarify, adapt, ignore, expire.
- `targets`: where this entry should be exported.

## Canonical Entry Shape

```json
{
  "id": "mem_20260616_001",
  "title": "Use Firebase project remast-salud10 only for Remast deployments",
  "body": "Deployment work for Remast has historically referenced Firebase project remast-salud10. Verify the active project before deploying.",
  "class": "structured_memory",
  "scope": "repository",
  "visibility": "team_shared",
  "activation": "always",
  "targets": ["codex", "agents_md", "claude", "cursor"],
  "provenance": [
    {
      "type": "conversation_summary",
      "source": "approved_user_review",
      "date": "2026-06-16"
    }
  ],
  "confidence": "medium",
  "sensitivity": "normal",
  "lifecycle": "clarify"
}
```

## Conflict Rules

- Do not silently overwrite tool-specific files.
- If a private memory contradicts a team memory, show both and ask which should win.
- If a rule mentions credentials, tokens, personal data, or private client details, block team export unless the user explicitly downgrades the risk after review.
- If a memory came from a session transcript, treat it as unapproved until the user accepts the curated wording.
- If the official tool docs do not expose a write path, mark the adapter as read-only or unsupported.
