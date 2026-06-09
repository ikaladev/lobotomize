# Lobotomize OpenAI Curated Plugin Submission Pack

## Plugin

Lobotomize

## Developer

Ikala / ikaladev

## Category

Productivity

## One-line description

Lobotomize helps Codex users inspect, curate, improve, and approve project memory safely.

## Problem

Codex users often lose valuable project context across machines, projects, and teams. They also need control over what the assistant remembers, what should be clarified, and what should never be stored.

## Solution

Lobotomize gives users an explicit workflow for project memory:

- Shows the current project memory summary.
- If no memory exists, asks before preparing one.
- If memory exists, asks before improving it.
- Uses previous Codex conversations only to prepare a proposal.
- Requires explicit user approval before applying changes.
- Avoids raw transcript storage unless explicitly approved.
- Redacts obvious secrets and excludes credentials, keys, passwords, and unrelated personal data.

## Why it should be curated

Project memory is a core productivity workflow for Codex. Lobotomize gives users and teams a safer, more transparent way to turn context into reusable project knowledge without silently writing memory.

## Safety and privacy model

- No automatic write on activation.
- User approval is required before memory is created or changed.
- Default policy excludes API keys, tokens, passwords, private keys, and unrelated personal data.
- Raw conversation transcripts are not stored by default.
- Memory is designed as curated project facts, not a hidden conversation archive.

## Current implementation

The plugin packages one skill and a local helper script:

- Skill: `skills/lobotomize/SKILL.md`
- Helper: `scripts/project_memory.py`
- Memory output: `.project-memory/memory.json`

## Review notes for OpenAI

OpenAI's public Codex documentation currently says official public plugin publishing and self-serve management are coming soon. Until that path is available, this package is prepared as a marketplace-compatible Codex plugin and can be shared through a Git marketplace URL.

## Assets

- Icon: `plugins/lobotomize/assets/icon.png`
- Logo: `plugins/lobotomize/assets/logo.png`
- Screenshots:
  - `plugins/lobotomize/assets/screenshot-flow.png`
  - `plugins/lobotomize/assets/screenshot-card.png`

## Requested outcome

Review Lobotomize for inclusion in the OpenAI-curated Codex Plugin Directory.
