---
name: lobotomize
description: Activa cuando el usuario diga "lobotomize" o pida ver, curar o exportar memoria de proyecto. Responde desde el primer mensaje en el idioma actual del usuario, lee la memoria existente, detecta superficies de memoria/reglas de otras herramientas de IA, muestra tarjetas compactas, pregunta antes de crear/mejorar/exportar memoria, prepara propuestas sólo con consentimiento y aplica cambios sólo con aprobación explícita.
---

# Lobotomize

When the user says `lobotomize`, inspect the current project memory. The very first visible response must be in the user's current conversation language.

Run from the plugin root:

```bash
python3 scripts/project_memory.py card --project <current-project-path>
```

For v2 multi-tool context discovery, also run when the user asks about other AI tools, memory surfaces, rules, exports, or project context portability:

```bash
python3 scripts/project_memory.py scan-context --project <current-project-path>
```

## Required Flow

1. Show the compact memory card.
2. If useful for the request, show the v2 context scan card. This detects known memory/rule surfaces for Codex/Lobotomize, AGENTS.md, Claude Code, Cursor, OpenCode, Gemini CLI, Qwen Code, Windsurf/Devin, Cline, Continue, Aider, and GitHub Copilot.
3. Ask all user-facing questions in the user's current conversation language. If no curated memory exists, ask the equivalent of: "This project does not have curated memory. Do you want me to prepare a memory proposal for approval?"
4. If the user says no, stop.
5. If the user says yes, run:

```bash
python3 scripts/project_memory.py source-pack --project <current-project-path> --limit 20
```

6. Use the source pack to draft an ideal memory proposal in the user's current conversation language by default. Show the proposal to the user and ask whether they approve it, reject it, or want adjustments.
7. If the user asks for adjustments, revise the proposal and ask again. Repeat until the user approves or cancels.
8. Apply the proposal only after explicit approval:

```bash
python3 scripts/project_memory.py apply --project <current-project-path> --proposal <approved-proposal.json>
```

9. If curated memory already exists, ask in the user's current conversation language the equivalent of: "This project already has curated memory. Do you want me to prepare an improvement using the current memory and prior conversations?"
10. If the user says no, stop. If yes, use the same proposal, adjustment, approval, and apply flow.

Do not initialize, create, overwrite, or improve memory just because the user ran `lobotomize`.

Use these categories:

- `keep`: project facts and decisions to preserve.
- `clarify`: claims that need confirmation.
- `adapt`: working style and project preferences.
- `ignore`: details that should not be carried forward.
- `sensitive`: local-only notes that must not be shared.

Never expose secrets, credentials, private keys, tokens, or raw private conversation transcripts in a shared memory card.

## V2 Multi-Tool Flow

Use this flow when the user asks to inspect, compare, organize, or export memory for other AI coding tools.

1. Detect known memory/context surfaces:

```bash
python3 scripts/project_memory.py scan-context --project <current-project-path>
```

2. If the user wants a normalized evidence pack, run:

```bash
python3 scripts/project_memory.py context-pack --project <current-project-path>
```

Use `--include-preview` only when previews are useful. Previews are redacted and files with secret-like patterns are marked as sensitive.

3. If the user wants to analyze or create memory using all existing project memories, run:

```bash
python3 scripts/project_memory.py merge-memories --project <current-project-path>
```

This fuses detected memories/rules into `keep`, `clarify`, `adapt`, `ignore`, and `sensitive`, preserving sources for each entry. Show the structured fusion to the user before proposing changes.

To save a proposal for later approval:

```bash
python3 scripts/project_memory.py merge-memories --project <current-project-path> --proposal-out <merged-proposal.json>
```

Do not apply the saved proposal until the user explicitly approves it. After approval, use the normal apply command:

```bash
python3 scripts/project_memory.py apply --project <current-project-path> --proposal <merged-proposal.json>
```

4. If the user wants to export approved Lobotomize memory into other tools, create a dry-run plan first:

```bash
python3 scripts/project_memory.py plan-exports --project <current-project-path>
```

For a reviewable/applicable JSON plan:

```bash
python3 scripts/project_memory.py plan-exports --project <current-project-path> --format json --include-content
```

5. Show the export plan to the user. Ask for explicit approval before applying.
6. Apply only a user-approved plan:

```bash
python3 scripts/project_memory.py apply-export-plan --plan <approved-export-plan.json> --approved
```

Do not run `apply-export-plan` unless the user explicitly approves that exact plan.

Supported v2 surfaces include:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.cursor/rules/*.mdc`
- `.continue/rules/*.md`
- `.devin/rules/*.md`
- `.windsurf/rules/*.md`
- `memory-bank/*.md`
- `.clinerules/*.md`
- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`
- `.aider.conf.yml`
- `.qwen/settings.json`
- `opencode.json` / `opencode.jsonc`

Kimi and Google Antigravity remain research-gap adapters until an official, user-editable project memory/rules surface is verified.

## Apply Boundary

The apply command writes the curated project memory file at `.project-memory/memory.json`.
Do not hand-edit generated Codex memory internals under `~/.codex/memories/`; those are generated state.

## Language

- User-facing questions and explanations must follow the user's current conversation language from the first response.
- The source pack instruction and proposed memory use the user's current conversation language by default unless the user asks for another proposal language.
- If the user switches languages, follow the latest user language for questions.
