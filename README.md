# Lobotomize

Lobotomize is a Codex plugin by Ikala for reviewing, strengthening, and approving curated project memory.

## Install in Codex

This repository is a Codex plugin marketplace. Once it is published to a reachable Git URL, people can add it to Codex from the plugin marketplace picker.

Expected install URL format:

```text
https://github.com/<owner>/<repo>.git
```

Codex app:

1. Open Plugins.
2. Open the marketplace/source menu.
3. Choose Add More.
4. Paste the repository URL.
5. Select the Ikala marketplace.
6. Install Lobotomize.

Codex CLI:

```text
codex plugin marketplace add https://github.com/<owner>/<repo>.git --sparse .agents/plugins --sparse plugins
codex plugin install lobotomize --source ikala
```

## What it does

Lobotomize reviews the existing project memory, shows a summary, asks before creating or improving memory, prepares proposals from previous conversations, and applies changes only after explicit user approval.

## Distribution

To make a public install link, publish this folder as a public Git repository. To make a private/team install link, publish it as a private Git repository and give access to the people who should install it.

The official OpenAI-curated directory is separate from this marketplace flow.
