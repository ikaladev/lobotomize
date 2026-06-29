# Lobotomize

Lobotomize is a Codex plugin by Ikala for reviewing, strengthening, approving, and exporting curated project memory.

## Version 2

Lobotomize v2 is a cross-tool memory manager for AI coding assistants. It can inspect, curate, compare, and synchronize project memory across tools such as Codex, Claude Code, Cursor, OpenCode, Gemini CLI, Qwen Code, Windsurf/Devin, Cline, Continue, Aider, and GitHub Copilot.

The v2 rule stays the same: memory is created, changed, or exported only after explicit user approval.

Research, product planning, and release notes:

- [Memory systems research](docs/v2/memory-systems-research.md)
- [Memory taxonomy](docs/v2/memory-taxonomy.md)
- [Lobotomize v2 product spec](docs/v2/lobotomize-v2-spec.md)
- [Changelog](CHANGELOG.md)

## Install

This repository is a Codex plugin marketplace. The marketplace catalog lives at:

```text
.agents/plugins/marketplace.json
```

The catalog exposes the plugin from:

```text
plugins/lobotomize
```

### Install From GitHub

Add this marketplace source to Codex:

Marketplace URL:

```text
https://github.com/ikaladev/lobotomize.git
```

Codex app:

1. Open Plugins.
2. Open the marketplace/source menu.
3. Choose Add More.
4. Paste the marketplace URL.
5. Select the Ikala marketplace.
6. Install Lobotomize.

Codex CLI:

```text
codex plugin marketplace add https://github.com/ikaladev/lobotomize.git --sparse .agents/plugins --sparse plugins
codex plugin add lobotomize@ikala
```

### Local Development Install

Use this only when testing a local checkout before publishing changes:

```text
codex plugin marketplace add /absolute/path/to/lobotomize
codex plugin add lobotomize@ikala
codex plugin list
```

## What It Does

Lobotomize reviews the existing project memory, shows a summary, asks before creating or improving memory, prepares proposals from previous conversations, detects known memory/rule files for other AI coding tools, and exports approved memory only after explicit user approval.

## Safety / Privacy

Lobotomize is designed around explicit approval. It does not create, change, or export project memory unless the user approves the exact action.

Curated memory should contain durable project facts, decisions, conventions, workflows, and open clarifications. It should not contain credentials, API keys, tokens, private keys, raw transcripts, unrelated personal data, or private local preferences unless the user explicitly chooses to keep them local.

The repository ignores `.project-memory/` by default so local memory for this project is not accidentally published.

## Distribution

To make a public install link, publish this folder as a public Git repository. To make a private/team install link, publish it as a private Git repository and give access to the people who should install it.

The official OpenAI-curated directory is separate from this marketplace flow.

## License

MIT
