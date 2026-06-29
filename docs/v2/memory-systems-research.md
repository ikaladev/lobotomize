# Lobotomize v2 Memory Systems Research

This document captures the current evidence for how major AI coding tools expose project memory, rules, instructions, context, and related persistence mechanisms.

Evidence standard: prefer official product documentation. When no official, accessible documentation was found for a memory feature, the system is marked as a research gap instead of treated as supported.

## Summary

Most tools do not expose one universal "memory" API. They combine several surfaces:

- User or account memory, usually private and cloud-managed.
- Project instruction files, usually committed to the repository.
- Local private memories, usually stored under the user's home directory.
- Rule systems with activation modes such as always-on, file globs, manual triggers, or model-decision triggers.
- Session compression, checkpointing, and history, which preserve work but are not durable project memory.
- References, docs, and retrieval sources that add context without becoming memory.

For Lobotomize v2, the safest model is adapter-based: discover what each tool can actually read/write, normalize it into one canonical memory model, show provenance and risk, then write changes only after explicit approval.

## Tool Matrix

| Tool | Official memory/context surfaces | Storage and scope | User controls | Lobotomize v2 implication |
| --- | --- | --- | --- | --- |
| OpenAI / ChatGPT / Codex family | Saved memories, reference chat history, custom instructions, files, connected app context, memory sources | Account and workspace dependent; some project memory may be local or app-managed | View, edit, delete, disable memory; memory sources can be inspected in supported surfaces | Treat native memory as user-controlled and provenance-sensitive. Do not assume raw history is equivalent to approved memory. |
| Claude Code | `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`, managed policy memory, auto memory | User, project, local-private, managed policy scopes; loaded at session start | `/init` creates or improves reviewable memory files; imports via `@path`; path-scoped rules | Strong adapter target. Support CLAUDE files, local/private split, imports, and path-specific rules. |
| Cursor | `.cursor/rules/*.mdc`, user rules, team rules, `AGENTS.md` | Project, user, team scopes; `.mdc` files carry metadata such as globs and apply mode | Create rules in chat or settings; team/user/project precedence | Strong adapter target. Preserve activation metadata and support `AGENTS.md` as a portable bridge. |
| OpenCode | `AGENTS.md`, `CLAUDE.md` fallback, global `~/.config/opencode/AGENTS.md`, `opencode.json` instructions and references | Project and global scopes; references may point to local directories or Git repos | `/init` creates or updates AGENTS.md; config can include instruction files and references | Strong adapter target. Support AGENTS.md, config instructions, and described references separately. |
| Gemini CLI | `GEMINI.md`, configurable `contextFileName`, optional `AGENTS.md`, `.gemini/settings.json`, include directories, checkpointing | User/project/system settings; context files in project and included dirs | Settings control context file names, included directories, checkpointing, and memory loading from includes | Strong adapter target. Support GEMINI.md and AGENTS.md generation, plus settings discovery. |
| Qwen Code | `.qwen/settings.json`, user/project config, model providers, commands such as `/compress`; file references with `@` | User and project config; sessions and context compression | Config scopes and CLI/session commands | Adapter should start with config/context discovery. No official first-class editable project memory surface was found in the researched docs. |
| Windsurf / Devin Desktop Cascade | Auto-generated Memories, global/workspace/system Rules, `.devin/rules/*.md`, `.windsurf/rules/*.md`, `AGENTS.md` | Local memories under `~/.codeium/windsurf/memories/`; workspace rules in repo; global/system scopes | Memories can be edited in settings; durable/shareable knowledge should be Rules or AGENTS.md | Strong adapter target. Separate private local memories from shareable rules. |
| Cline | Memory Bank markdown folder plus Cline Rules such as `.clinerules/memory-bank.md` | Project folder, usually `memory-bank/*.md` | User initializes and updates memory bank through chat instructions | Strong adapter target for structured project memory. Useful canonical export format. |
| Continue | `.continue/rules/*.md`, YAML frontmatter, globs, regex, alwaysApply | Project rules; toolbar order affects joined rules | Rules can be created by agent and configured with metadata | Strong adapter target. Preserve rule metadata and load order. |
| Aider | Convention files read into chat with `/read` or `.aider.conf.yml` `read:` entries | Project files loaded as read-only context | User controls files read into chat/config | Treat as instructions/context, not native memory. Export conventions safely. |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `AGENTS.md`, root `CLAUDE.md`/`GEMINI.md`, personal/org/repo instructions | Repository, path-specific, personal, organization scopes | Instructions automatically attach; references show when used in supported clients | Strong adapter target for repository-shareable instructions. |
| Google Antigravity | Official public docs for a concrete memory/rules file format were not accessible in this research pass; the official docs URL did not expose parseable memory/rules documentation | Unknown | Unknown | Research gap. Add adapter only after official docs or verified local behavior. |
| Kimi | Official public docs for a concrete user-editable project memory format were not found in this research pass; current evidence points more to long-context/model/provider use than to a documented project-memory file | Unknown; Kimi models may be used through other agent runtimes | Unknown | Research gap. Treat Kimi as a model/provider until a memory surface is verified. |

## Sources

- OpenAI Help Center, [Memory FAQ](https://help.openai.com/en/articles/8590148-memory-faq)
- Anthropic, [Claude Code memory](https://code.claude.com/docs/en/memory)
- Cursor, [Rules](https://cursor.com/docs/rules.md)
- OpenCode, [Rules](https://opencode.ai/docs/rules/)
- OpenCode, [References](https://opencode.ai/docs/references/)
- QwenLM, [Qwen Code repository](https://github.com/QwenLM/qwen-code)
- Google Gemini CLI, [Configuration](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/configuration.md)
- Devin / Windsurf, [Cascade memories and rules](https://docs.devin.ai/desktop/cascade/memories)
- Cline, [Memory Bank](https://docs.cline.bot/best-practices/memory-bank)
- Continue, [Rules](https://docs.continue.dev/customize/deep-dives/rules)
- Aider, [Coding conventions](https://aider.chat/docs/usage/conventions.html)
- GitHub Docs, [Repository custom instructions for Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
- GitHub Docs, [Personal custom instructions for Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-personal-instructions)
- Google, [Antigravity official site](https://antigravity.google/)
