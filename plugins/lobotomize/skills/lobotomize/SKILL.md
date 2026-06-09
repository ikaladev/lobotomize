---
name: lobotomize
description: Activa cuando el usuario diga "lobotomize" o pida ver la memoria del proyecto. Responde desde el primer mensaje en el idioma actual del usuario, lee la memoria existente, muestra una tarjeta compacta, pregunta antes de crear o mejorar memoria, prepara propuestas desde conversaciones sólo con consentimiento y aplica cambios sólo con aprobación explícita.
---

# Lobotomize

When the user says `lobotomize`, inspect the current project memory. The very first visible response must be in the user's current conversation language.

Run from the plugin root:

```bash
python3 scripts/project_memory.py card --project <current-project-path>
```

## Required Flow

1. Show the compact memory card.
2. Ask all user-facing questions in the user's current conversation language. If no curated memory exists, ask the equivalent of: "This project does not have curated memory. Do you want me to prepare a memory proposal for approval?"
3. If the user says no, stop.
4. If the user says yes, run:

```bash
python3 scripts/project_memory.py source-pack --project <current-project-path> --limit 20
```

5. Use the source pack to draft an ideal memory proposal in the user's current conversation language by default. Show the proposal to the user and ask whether they approve it, reject it, or want adjustments.
6. If the user asks for adjustments, revise the proposal and ask again. Repeat until the user approves or cancels.
7. Apply the proposal only after explicit approval:

```bash
python3 scripts/project_memory.py apply --project <current-project-path> --proposal <approved-proposal.json>
```

8. If curated memory already exists, ask in the user's current conversation language the equivalent of: "This project already has curated memory. Do you want me to prepare an improvement using the current memory and prior conversations?"
9. If the user says no, stop. If yes, use the same proposal, adjustment, approval, and apply flow.

Do not initialize, create, overwrite, or improve memory just because the user ran `lobotomize`.

Use these categories:

- `keep`: project facts and decisions to preserve.
- `clarify`: claims that need confirmation.
- `adapt`: working style and project preferences.
- `ignore`: details that should not be carried forward.
- `sensitive`: local-only notes that must not be shared.

Never expose secrets, credentials, private keys, tokens, or raw private conversation transcripts in a shared memory card.

## Apply Boundary

The apply command writes the curated project memory file at `.project-memory/memory.json`.
Do not hand-edit generated Codex memory internals under `~/.codex/memories/`; those are generated state.

## Language

- User-facing questions and explanations must follow the user's current conversation language from the first response.
- The source pack instruction and proposed memory use the user's current conversation language by default unless the user asks for another proposal language.
- If the user switches languages, follow the latest user language for questions.
