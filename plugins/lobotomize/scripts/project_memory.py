#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "lobotomize/v1"
DISCOVERY_SCHEMA = "lobotomize/v2-discovery"
CONTEXT_PACK_SCHEMA = "lobotomize/v2-context-pack"
EXPORT_PLAN_SCHEMA = "lobotomize/v2-export-plan"
MERGED_MEMORY_SCHEMA = "lobotomize/v2-merged-memory"
MEMORY_CANDIDATES = (
    ".project-memory/memory.json",
    ".codex/project-memory/memory.json",
    ".codex/memory.json",
)
MEMORY_KEYS = ("keep", "clarify", "adapt", "ignore", "sensitive", "sources")
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|private[_-]?key)\s*[:=]\s*['\"]?[^'\"\s,}]+"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"sk-[0-9A-Za-z_\-]{20,}"),
)
BOILERPLATE_PATTERNS = (
    re.compile(r"(?i)^generated from approved lobotomize memory"),
    re.compile(r"(?i)^do not add secrets"),
    re.compile(r"(?i)^none recorded\.?$"),
    re.compile(r"(?i)^this file"),
    re.compile(r"(?i)^the approved memory has sensitive entries"),
)
CATEGORY_HEADINGS = {
    "stable project facts": "keep",
    "project facts": "keep",
    "facts": "keep",
    "decisions": "keep",
    "architecture": "keep",
    "system patterns": "keep",
    "progress": "keep",
    "open clarifications": "clarify",
    "clarifications": "clarify",
    "questions": "clarify",
    "todo": "clarify",
    "todos": "clarify",
    "working preferences": "adapt",
    "preferences": "adapt",
    "conventions": "adapt",
    "rules": "adapt",
    "coding rules": "adapt",
    "tech context": "adapt",
    "things to ignore": "ignore",
    "ignore": "ignore",
    "out of scope": "ignore",
    "sensitive notes": "sensitive",
    "sensitive": "sensitive",
    "secrets": "sensitive",
}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".turbo",
    ".venv",
    "dist",
    "build",
    "node_modules",
    "vendor",
}
MEMORY_SURFACES = (
    {
        "tool": "lobotomize",
        "display_name": "Lobotomize",
        "patterns": (".project-memory/memory.json", ".codex/project-memory/memory.json", ".codex/memory.json"),
        "class": "structured_memory",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "manual",
        "write_support": "approved_file_write",
    },
    {
        "tool": "agents_md",
        "display_name": "AGENTS.md",
        "patterns": ("AGENTS.md", "**/AGENTS.md"),
        "class": "instruction_rule",
        "scope": "directory",
        "visibility": "team_shared",
        "activation": "always_or_tool_specific",
        "write_support": "approved_file_write",
    },
    {
        "tool": "claude",
        "display_name": "Claude Code",
        "patterns": ("CLAUDE.md", "**/CLAUDE.md", "CLAUDE.local.md", ".claude/rules/*.md"),
        "class": "instruction_rule",
        "scope": "repository_or_local",
        "visibility": "team_shared_or_private",
        "activation": "always_or_path_scoped",
        "write_support": "approved_file_write",
    },
    {
        "tool": "cursor",
        "display_name": "Cursor",
        "patterns": (".cursor/rules/*.mdc",),
        "class": "instruction_rule",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "metadata_driven",
        "write_support": "approved_file_write",
    },
    {
        "tool": "opencode",
        "display_name": "OpenCode",
        "patterns": ("opencode.json", "opencode.jsonc", "AGENTS.md", "**/AGENTS.md", "CLAUDE.md"),
        "class": "instruction_or_config",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "config_or_always",
        "write_support": "approved_file_write",
    },
    {
        "tool": "gemini",
        "display_name": "Gemini CLI",
        "patterns": ("GEMINI.md", "**/GEMINI.md", ".gemini/settings.json"),
        "class": "instruction_or_config",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "context_file_or_config",
        "write_support": "approved_file_write",
    },
    {
        "tool": "qwen",
        "display_name": "Qwen Code",
        "patterns": (".qwen/settings.json",),
        "class": "config",
        "scope": "repository",
        "visibility": "private_or_team_shared",
        "activation": "config",
        "write_support": "read_only_initially",
    },
    {
        "tool": "windsurf",
        "display_name": "Windsurf / Devin",
        "patterns": (".devin/rules/*.md", ".windsurf/rules/*.md", "AGENTS.md", "**/AGENTS.md"),
        "class": "instruction_rule",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "metadata_or_always",
        "write_support": "approved_file_write",
    },
    {
        "tool": "cline",
        "display_name": "Cline",
        "patterns": ("memory-bank/*.md", ".clinerules/*.md"),
        "class": "structured_memory",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "manual_instruction",
        "write_support": "approved_file_write",
    },
    {
        "tool": "continue",
        "display_name": "Continue",
        "patterns": (".continue/rules/*.md",),
        "class": "instruction_rule",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "metadata_driven",
        "write_support": "approved_file_write",
    },
    {
        "tool": "aider",
        "display_name": "Aider",
        "patterns": (".aider.conf.yml", ".aider.conf.yaml", "CONVENTIONS.md"),
        "class": "instruction_or_config",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "read_config",
        "write_support": "approved_file_write",
    },
    {
        "tool": "github_copilot",
        "display_name": "GitHub Copilot",
        "patterns": (".github/copilot-instructions.md", ".github/instructions/*.instructions.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md"),
        "class": "instruction_rule",
        "scope": "repository",
        "visibility": "team_shared",
        "activation": "automatic_when_supported",
        "write_support": "approved_file_write",
    },
)
EXPORT_TARGETS = {
    "agents": {
        "display_name": "AGENTS.md",
        "path": "AGENTS.md",
        "format": "markdown",
        "activation": "always_or_tool_specific",
    },
    "claude": {
        "display_name": "Claude Code",
        "path": "CLAUDE.md",
        "format": "markdown",
        "activation": "always",
    },
    "gemini": {
        "display_name": "Gemini CLI",
        "path": "GEMINI.md",
        "format": "markdown",
        "activation": "context_file",
    },
    "cursor": {
        "display_name": "Cursor",
        "path": ".cursor/rules/lobotomize-memory.mdc",
        "format": "mdc",
        "activation": "alwaysApply",
    },
    "continue": {
        "display_name": "Continue",
        "path": ".continue/rules/lobotomize-memory.md",
        "format": "continue_rule",
        "activation": "alwaysApply",
    },
    "github_copilot": {
        "display_name": "GitHub Copilot",
        "path": ".github/copilot-instructions.md",
        "format": "markdown",
        "activation": "automatic_when_supported",
    },
    "cline": {
        "display_name": "Cline",
        "path": "memory-bank/lobotomize.md",
        "format": "markdown",
        "activation": "memory_bank",
    },
    "aider": {
        "display_name": "Aider",
        "path": "CONVENTIONS.md",
        "format": "markdown",
        "activation": "read_config",
    },
}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def state_db() -> Path:
    return codex_home() / "state_5.sqlite"


def memory_path(project: Path) -> Path:
    return project / ".project-memory" / "memory.json"


def find_memory_path(project: Path) -> Path | None:
    for candidate in MEMORY_CANDIDATES:
        path = project / candidate
        if path.exists():
            return path
    return None


def connect_state() -> sqlite3.Connection:
    db_path = state_db()
    if not db_path.exists():
        raise SystemExit(f"Codex state database was not found at {db_path}")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def project_name(project: Path) -> str:
    return project.resolve().name or str(project.resolve())


def is_skipped_path(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in SKIP_DIRS for part in rel.parts)


def unique_matching_paths(project: Path, patterns: tuple[str, ...]) -> list[Path]:
    root = project.expanduser().resolve()
    seen = set()
    matches = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file() or is_skipped_path(path, root):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            matches.append(path)
    return sorted(matches, key=lambda value: value.relative_to(root).as_posix())


def line_count(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return sum(1 for _ in fh)
    except UnicodeDecodeError:
        return None


def file_metadata(path: Path, root: Path) -> dict:
    stat = path.stat()
    return {
        "path": str(path.relative_to(root)),
        "absolute_path": str(path),
        "bytes": stat.st_size,
        "lines": line_count(path),
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def read_text_sample(path: Path, limit: int = 12000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def read_preview(path: Path, limit: int = 4000) -> str:
    text = read_text_sample(path, limit * 3)
    return clamp_text(text, limit)


def has_secret_signal(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def strip_markdown_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) == 3:
        return parts[2].lstrip()
    return text


def is_boilerplate(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    return any(pattern.search(stripped) for pattern in BOILERPLATE_PATTERNS)


def normalize_entry_key(text: str) -> str:
    value = redact_text(text).lower()
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"[^a-z0-9áéíóúñü]+", " ", value, flags=re.IGNORECASE)
    return " ".join(value.split())


def normalize_heading(text: str) -> str:
    text = text.strip().strip("#").strip()
    text = re.sub(r"^\d+[\.)]\s*", "", text)
    return " ".join(text.lower().split())


def infer_category(text: str, fallback: str = "keep") -> str:
    lower = text.lower()
    if has_secret_signal(text):
        return "sensitive"
    if any(word in lower for word in ("verify", "confirm", "unclear", "unknown", "needs clarification", "todo", "pending")):
        return "clarify"
    if any(word in lower for word in ("ignore", "out of scope", "do not use", "do not carry", "not relevant")):
        return "ignore"
    if any(word in lower for word in ("prefer", "use ", "run ", "always", "never", "should", "must", "convention", "style", "workflow")):
        return "adapt"
    return fallback


def source_ref(tool: dict, path: str, section: str | None = None) -> dict:
    ref = {
        "tool": tool["tool"],
        "display_name": tool["display_name"],
        "path": path,
    }
    if section:
        ref["section"] = section
    return ref


def memory_item_to_text(item) -> str:
    return clamp_text(item_text(item), 1200)


def extract_lobotomize_entries(payload: dict, tool: dict, path: str) -> list[dict]:
    entries = []
    for category in MEMORY_KEYS:
        if category == "sources":
            continue
        value = payload.get(category, [])
        if not isinstance(value, list):
            continue
        for item in value:
            text = memory_item_to_text(item)
            if is_boilerplate(text):
                continue
            entries.append(
                {
                    "text": text,
                    "category": category,
                    "sources": [source_ref(tool, path, category)],
                    "confidence": "high",
                }
            )
    return entries


def extract_markdown_entries(text: str, tool: dict, path: str) -> list[dict]:
    entries = []
    current_section = None
    current_category = "adapt" if tool["class"] in ("instruction_rule", "instruction_or_config") else "keep"
    current_heading_category = None
    for raw_line in strip_markdown_frontmatter(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            current_section = line.lstrip("#").strip()
            current_heading_category = CATEGORY_HEADINGS.get(normalize_heading(current_section))
            if current_heading_category:
                current_category = current_heading_category
            continue
        bullet_match = re.match(r"^([-*+]|\d+[\.)])\s+(.*)$", line)
        if bullet_match:
            line = bullet_match.group(2).strip()
        elif len(line) > 180:
            line = clamp_text(line, 600)
        elif has_secret_signal(line):
            pass
        elif not current_section and tool["class"] in ("config", "instruction_or_config"):
            continue
        if is_boilerplate(line):
            continue
        category = "sensitive" if has_secret_signal(line) else (current_heading_category or infer_category(line, current_category))
        entries.append(
            {
                "text": clamp_text(line, 1200),
                "category": category,
                "sources": [source_ref(tool, path, current_section)],
                "confidence": "medium",
            }
        )
    return entries


def extract_config_entries(text: str, tool: dict, path: str) -> list[dict]:
    if not text.strip() or is_boilerplate(text):
        return []
    if has_secret_signal(text):
        return [
            {
                "text": f"{path} contains secret-like values and should be reviewed before sharing.",
                "category": "sensitive",
                "sources": [source_ref(tool, path)],
                "confidence": "high",
            }
        ]
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return extract_markdown_entries(text, tool, path)
    interesting_keys = []
    for key in ("instructions", "references", "includeDirectories", "contextFileName", "read", "model", "modelProviders"):
        if key in payload:
            interesting_keys.append(key)
    if not interesting_keys:
        return []
    return [
        {
            "text": f"{path} configures {', '.join(interesting_keys)} for {tool['display_name']}.",
            "category": "adapt",
            "sources": [source_ref(tool, path)],
            "confidence": "medium",
        }
    ]


def extract_artifact_entries(root: Path, tool: dict, file_info: dict) -> list[dict]:
    path = root / file_info["path"]
    text = read_text_sample(path, 24000)
    if not text:
        return []
    if tool["tool"] == "lobotomize" and path.suffix == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return []
        return extract_lobotomize_entries(payload, tool, file_info["path"])
    if path.suffix.lower() in (".json", ".jsonc", ".yml", ".yaml"):
        return extract_config_entries(text, tool, file_info["path"])
    return extract_markdown_entries(text, tool, file_info["path"])


def merge_entries(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    merged_by_key: dict[str, dict] = {}
    review_items = []
    review_keys = set()
    for entry in entries:
        key = normalize_entry_key(entry["text"])
        if not key:
            continue
        existing = merged_by_key.get(key)
        if existing:
            if entry["category"] != existing["category"]:
                existing.setdefault("alternate_categories", [])
                if entry["category"] not in existing["alternate_categories"]:
                    existing["alternate_categories"].append(entry["category"])
                review_key = ("category_conflict", key)
                if review_key not in review_keys:
                    review_keys.add(review_key)
                    review_items.append(
                        {
                            "type": "category_conflict",
                            "text": existing["text"],
                            "categories": sorted(set([existing["category"], entry["category"]] + existing.get("alternate_categories", []))),
                        }
                    )
            existing["sources"].extend(entry["sources"])
            if entry["confidence"] == "high":
                existing["confidence"] = "high"
            continue
        merged_by_key[key] = {
            "id": f"merged_{len(merged_by_key) + 1:04d}",
            "text": entry["text"],
            "category": entry["category"],
            "sources": entry["sources"],
            "confidence": entry["confidence"],
        }
        if entry["category"] == "sensitive":
            review_key = ("sensitive_entry", key)
            if review_key not in review_keys:
                review_keys.add(review_key)
                review_items.append({"type": "sensitive_entry", "text": entry["text"]})
    return list(merged_by_key.values()), review_items


def build_merged_memory(project: Path, include_raw_entries: bool = False) -> dict:
    root = project.expanduser().resolve()
    discovery = discover_memory_surfaces(root)
    extracted = []
    source_files = []
    for tool in discovery["tools"]:
        for file_info in tool["files"]:
            source_files.append(
                {
                    "tool": tool["tool"],
                    "display_name": tool["display_name"],
                    "path": file_info["path"],
                    "class": tool["class"],
                    "visibility": tool["visibility"],
                    "activation": tool["activation"],
                }
            )
            extracted.extend(extract_artifact_entries(root, tool, file_info))
    merged, review_items = merge_entries(extracted)
    by_category = {key: [] for key in ("keep", "clarify", "adapt", "ignore", "sensitive")}
    for entry in merged:
        by_category.setdefault(entry["category"], []).append(entry)
    proposal = default_memory(root)
    proposal["sources"] = [
        {
            "type": "merged_memory",
            "generated_at": now_iso(),
            "source_files": source_files,
        }
    ]
    for category in ("keep", "clarify", "adapt", "ignore", "sensitive"):
        proposal[category] = [
            {
                "text": entry["text"],
                "sources": entry["sources"],
                "confidence": entry["confidence"],
            }
            for entry in by_category.get(category, [])
        ]
    return {
        "schema": MERGED_MEMORY_SCHEMA,
        "generated_at": now_iso(),
        "project": discovery["project"],
        "summary": {
            "source_files": len(source_files),
            "raw_entries": len(extracted),
            "merged_entries": len(merged),
            "needs_review": len(review_items),
            "categories": {category: len(items) for category, items in by_category.items()},
        },
        "source_files": source_files,
        "categories": by_category,
        "review": review_items,
        "proposal": proposal,
        "raw_entries": extracted if include_raw_entries else None,
        "instruction": "Review this merged memory before applying it. It is derived from detected project memory/rule files and may contain duplicates, stale rules, or uncertain inferences.",
    }


def discover_memory_surfaces(project: Path) -> dict:
    root = project.expanduser().resolve()
    tools = []
    path_index: dict[str, list[str]] = {}
    for surface in MEMORY_SURFACES:
        files = [file_metadata(path, root) for path in unique_matching_paths(root, surface["patterns"])]
        for file_info in files:
            path_index.setdefault(file_info["path"], []).append(surface["tool"])
        tools.append(
            {
                "tool": surface["tool"],
                "display_name": surface["display_name"],
                "class": surface["class"],
                "scope": surface["scope"],
                "visibility": surface["visibility"],
                "activation": surface["activation"],
                "write_support": surface["write_support"],
                "files": files,
            }
        )
    detected_tools = [tool for tool in tools if tool["files"]]
    shared_paths = [
        {"path": path, "tools": sorted(set(tool_ids))}
        for path, tool_ids in sorted(path_index.items())
        if len(set(tool_ids)) > 1
    ]
    health = "none"
    if detected_tools:
        health = "partial"
    if len(detected_tools) >= 3:
        health = "multi_tool"
    if shared_paths:
        health = "overlapping"
    return {
        "schema": DISCOVERY_SCHEMA,
        "generated_at": now_iso(),
        "project": {
            "name": project_name(root),
            "path": str(root),
        },
        "health": health,
        "detected_tool_count": len(detected_tools),
        "detected_file_count": sum(len(tool["files"]) for tool in detected_tools),
        "tools": tools,
        "overlaps": shared_paths,
        "research_gaps": [
            "Kimi: no official user-editable project memory surface confirmed yet.",
            "Google Antigravity: no official memory/rules file format confirmed yet.",
        ],
    }


def build_context_pack(project: Path, include_preview: bool) -> dict:
    root = project.expanduser().resolve()
    discovery = discover_memory_surfaces(root)
    artifacts = []
    for tool in discovery["tools"]:
        for file_info in tool["files"]:
            path = root / file_info["path"]
            raw_sample = read_text_sample(path)
            preview = read_preview(path)
            artifact = {
                "tool": tool["tool"],
                "display_name": tool["display_name"],
                "class": tool["class"],
                "scope": tool["scope"],
                "visibility": tool["visibility"],
                "activation": tool["activation"],
                "write_support": tool["write_support"],
                "path": file_info["path"],
                "bytes": file_info["bytes"],
                "lines": file_info["lines"],
                "modified_at": file_info["modified_at"],
                "sensitivity": "secret_signal" if has_secret_signal(raw_sample) else "normal",
                "preview": preview if include_preview else None,
            }
            artifacts.append(artifact)
    return {
        "schema": CONTEXT_PACK_SCHEMA,
        "generated_at": now_iso(),
        "project": discovery["project"],
        "health": discovery["health"],
        "artifacts": artifacts,
        "overlaps": discovery["overlaps"],
        "research_gaps": discovery["research_gaps"],
        "instruction": "Use this pack as read-only evidence. Do not treat detected files as approved canonical memory until the user approves a proposal.",
    }


def render_list_section(title: str, items: list) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("- None recorded.")
        lines.append("")
        return lines
    for item in items:
        lines.append(f"- {item_text(item)}")
    lines.append("")
    return lines


def render_memory_markdown(payload: dict, target_name: str, fallback_project_name: str) -> str:
    project = payload.get("project", {})
    name = project.get("name") or fallback_project_name
    lines = [
        f"# {name} Project Memory",
        "",
        f"Generated from approved Lobotomize memory for {target_name}.",
        "Do not add secrets, tokens, private keys, raw transcripts, or personal data to this file.",
        "",
    ]
    lines.extend(render_list_section("Stable Project Facts", payload.get("keep", [])))
    lines.extend(render_list_section("Open Clarifications", payload.get("clarify", [])))
    lines.extend(render_list_section("Working Preferences", payload.get("adapt", [])))
    lines.extend(render_list_section("Things To Ignore", payload.get("ignore", [])))
    sensitive = payload.get("sensitive", [])
    if sensitive:
        lines.extend(
            [
                "## Sensitive Notes",
                "",
                "The approved memory has sensitive entries. Keep them out of shared assistant rules unless the user explicitly approves each one.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_target_content(payload: dict, target_id: str, target: dict) -> str:
    body = render_memory_markdown(payload, target["display_name"], payload.get("_fallback_project_name", "Project"))
    if target["format"] == "mdc":
        return "---\nalwaysApply: true\n---\n\n" + body
    if target["format"] == "continue_rule":
        return "---\nname: Lobotomize Project Memory\nalwaysApply: true\n---\n\n" + body
    return body


def selected_export_targets(value: str) -> list[str]:
    if value == "all":
        return list(EXPORT_TARGETS)
    selected = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [item for item in selected if item not in EXPORT_TARGETS]
    if unknown:
        raise SystemExit(f"Unknown export target(s): {', '.join(unknown)}")
    return selected


def build_export_plan(project: Path, targets: list[str], include_content: bool = False) -> dict:
    root = project.expanduser().resolve()
    payload = read_memory(root)
    payload["_fallback_project_name"] = project_name(root)
    operations = []
    for target_id in targets:
        target = EXPORT_TARGETS[target_id]
        path = root / target["path"]
        content = render_target_content(payload, target_id, target)
        operations.append(
            {
                "target": target_id,
                "display_name": target["display_name"],
                "path": target["path"],
                "absolute_path": str(path),
                "action": "update" if path.exists() else "create",
                "format": target["format"],
                "activation": target["activation"],
                "requires_approval": True,
                "bytes": len(content.encode("utf-8")),
                "preview": clamp_text(content, 1800),
                "content": content if include_content else None,
            }
        )
    return {
        "schema": EXPORT_PLAN_SCHEMA,
        "generated_at": now_iso(),
        "project": {
            "name": project_name(root),
            "path": str(root),
        },
        "memory_file": str(find_memory_path(root) or memory_path(root)),
        "targets": targets,
        "operations": operations,
        "instruction": "This is a dry-run plan. Do not write these files until the user explicitly approves the plan.",
    }


def validate_export_plan(plan: dict) -> dict:
    if not isinstance(plan, dict):
        raise SystemExit("Export plan must be a JSON object.")
    if plan.get("schema") != EXPORT_PLAN_SCHEMA:
        raise SystemExit(f"Export plan schema must be {EXPORT_PLAN_SCHEMA}.")
    project = plan.get("project") or {}
    project_path = Path(project.get("path", "")).expanduser()
    if not project_path:
        raise SystemExit("Export plan is missing project.path.")
    operations = plan.get("operations")
    if not isinstance(operations, list) or not operations:
        raise SystemExit("Export plan has no operations.")
    root = project_path.resolve()
    for operation in operations:
        rel_path = operation.get("path")
        content = operation.get("content")
        if not rel_path or not isinstance(rel_path, str):
            raise SystemExit("Every export operation must include a relative path.")
        if content is None:
            raise SystemExit("Export operation is missing full content. Recreate the plan with --include-content.")
        destination = (root / rel_path).resolve()
        try:
            destination.relative_to(root)
        except ValueError:
            raise SystemExit(f"Export operation escapes the project root: {rel_path}")
    return plan


def apply_export_plan(plan: dict) -> dict:
    validated = validate_export_plan(plan)
    root = Path(validated["project"]["path"]).expanduser().resolve()
    applied = []
    for operation in validated["operations"]:
        destination = root / operation["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        action = "update" if destination.exists() else "create"
        destination.write_text(operation["content"], encoding="utf-8")
        applied.append(
            {
                "target": operation.get("target"),
                "display_name": operation.get("display_name"),
                "path": operation["path"],
                "absolute_path": str(destination),
                "action": action,
                "bytes": len(operation["content"].encode("utf-8")),
            }
        )
    return {
        "schema": "lobotomize/v2-export-apply-result",
        "applied_at": now_iso(),
        "project": validated["project"],
        "operations": applied,
    }


def markdown_discovery_card(payload: dict) -> str:
    project = payload["project"]
    lines = [
        f"### Lobotomize v2: {project['name']}",
        "",
        f"**Proyecto:** `{project['path']}`",
        f"**Estado:** {payload['health']}",
        f"**Herramientas detectadas:** {payload['detected_tool_count']}",
        f"**Archivos detectados:** {payload['detected_file_count']}",
        "",
        "| Herramienta | Archivos | Alcance | Visibilidad | Escritura |",
        "|---|---:|---|---|---|",
    ]
    for tool in payload["tools"]:
        if not tool["files"]:
            continue
        lines.append(
            f"| {tool['display_name']} | {len(tool['files'])} | {tool['scope']} | {tool['visibility']} | {tool['write_support']} |"
        )
    if payload["overlaps"]:
        lines.extend(["", "#### Archivos compartidos por varias herramientas", ""])
        for overlap in payload["overlaps"]:
            lines.append(f"- `{overlap['path']}`: {', '.join(overlap['tools'])}")
    if not payload["detected_file_count"]:
        lines.extend(["", "No encontré archivos de memoria o reglas conocidos en este proyecto."])
    lines.extend(["", "#### Brechas de investigación", ""])
    lines.extend(f"- {item}" for item in payload["research_gaps"])
    return "\n".join(lines)


def markdown_context_pack(payload: dict) -> str:
    lines = [
        f"### Lobotomize v2 Context Pack: {payload['project']['name']}",
        "",
        f"**Proyecto:** `{payload['project']['path']}`",
        f"**Estado:** {payload['health']}",
        f"**Artefactos:** {len(payload['artifacts'])}",
        "",
        "| Herramienta | Archivo | Clase | Sensibilidad |",
        "|---|---|---|---|",
    ]
    for artifact in payload["artifacts"]:
        lines.append(
            f"| {artifact['display_name']} | `{artifact['path']}` | {artifact['class']} | {artifact['sensitivity']} |"
        )
    if not payload["artifacts"]:
        lines.append("| Ninguna | - | - | - |")
    if payload["overlaps"]:
        lines.extend(["", "#### Solapamientos", ""])
        for overlap in payload["overlaps"]:
            lines.append(f"- `{overlap['path']}`: {', '.join(overlap['tools'])}")
    return "\n".join(lines)


def markdown_export_plan(payload: dict) -> str:
    lines = [
        f"### Lobotomize v2 Export Plan: {payload['project']['name']}",
        "",
        f"**Proyecto:** `{payload['project']['path']}`",
        f"**Memoria fuente:** `{payload['memory_file']}`",
        f"**Operaciones:** {len(payload['operations'])}",
        "",
        "| Destino | Acción | Archivo | Formato |",
        "|---|---|---|---|",
    ]
    for operation in payload["operations"]:
        lines.append(
            f"| {operation['display_name']} | {operation['action']} | `{operation['path']}` | {operation['format']} |"
        )
    lines.extend(["", "No se escribió ningún archivo. Este plan requiere aprobación explícita."])
    return "\n".join(lines)


def markdown_merged_memory(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        f"### Lobotomize v2 Merged Memory: {payload['project']['name']}",
        "",
        f"**Proyecto:** `{payload['project']['path']}`",
        f"**Archivos fuente:** {summary['source_files']}",
        f"**Entradas extraídas:** {summary['raw_entries']}",
        f"**Entradas fusionadas:** {summary['merged_entries']}",
        f"**Requiere revisión:** {summary['needs_review']}",
        "",
        "| Categoría | Entradas |",
        "|---|---:|",
    ]
    labels = {
        "keep": "Conservar",
        "clarify": "Aclarar",
        "adapt": "Adaptar",
        "ignore": "Ignorar",
        "sensitive": "Sensible",
    }
    for category in ("keep", "clarify", "adapt", "ignore", "sensitive"):
        lines.append(f"| {labels[category]} | {summary['categories'].get(category, 0)} |")
    lines.extend(["", "#### Vista rápida", ""])
    for category in ("keep", "clarify", "adapt", "ignore", "sensitive"):
        entries = payload["categories"].get(category, [])
        if not entries:
            continue
        lines.append(f"**{labels[category]}**")
        for entry in entries[:5]:
            sources = ", ".join(sorted({source["path"] for source in entry["sources"]}))
            lines.append(f"- {entry['text']} _(fuentes: {sources})_")
        if len(entries) > 5:
            lines.append(f"- ...{len(entries) - 5} más")
        lines.append("")
    if payload["review"]:
        lines.extend(["#### Revisión sugerida", ""])
        for item in payload["review"][:8]:
            lines.append(f"- {item['type']}: {item.get('text', '')}")
        if len(payload["review"]) > 8:
            lines.append(f"- ...{len(payload['review']) - 8} más")
    if payload.get("proposal_file"):
        lines.extend(["", f"Propuesta fusionada guardada en `{payload['proposal_file']}`. Revísala antes de aplicarla."])
    else:
        lines.extend(["", "No se escribió ningún archivo. Usa el JSON de `proposal` como base si quieres aplicar una memoria curada después de revisarla."])
    return "\n".join(lines)


def default_memory(project: Path) -> dict:
    return {
        "schema": SCHEMA,
        "updated_at": now_iso(),
        "project": {
            "name": project_name(project),
            "path_hint": str(project.resolve()),
        },
        "policy": {
            "share_with_team": True,
            "default_retention": "curated_only",
            "never_store": [
                "API keys, tokens, passwords, and private keys",
                "Personal data that is not required for project work",
                "Raw conversation transcripts unless explicitly approved",
            ],
        },
        "keep": [],
        "clarify": [],
        "adapt": [],
        "ignore": [],
        "sensitive": [],
        "sources": [],
    }


def read_memory(project: Path) -> dict:
    path = find_memory_path(project)
    if path is None:
        path = memory_path(project)
        raise SystemExit(f"No curated memory file exists yet at {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def read_memory_with_path(project: Path) -> tuple[dict | None, Path]:
    path = find_memory_path(project)
    if path is None:
        return None, memory_path(project)
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh), path


def write_memory(project: Path, payload: dict) -> Path:
    path = memory_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = now_iso()
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def redact_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def clamp_text(text: str, limit: int) -> str:
    clean = " ".join(redact_text(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def should_skip_note(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    lower = stripped.lower()
    return lower.startswith(
        (
            "<environment_context>",
            "<permissions instructions>",
            "<app-context>",
            "<collaboration_mode>",
            "<apps_instructions>",
            "<skills_instructions>",
            "<plugins_instructions>",
        )
    )


def append_unique(items: list[str], text: str, limit: int) -> None:
    if should_skip_note(text):
        return
    clamped = clamp_text(text, limit)
    if clamped and clamped not in items:
        items.append(clamped)


def user_thread_rows(project: Path, limit: int) -> list[sqlite3.Row]:
    project_resolved = str(project.expanduser().resolve())
    with connect_state() as con:
        return con.execute(
            """
            select id, title, rollout_path, git_branch, git_sha, updated_at
            from threads
            where cwd = ?
              and coalesce(thread_source, 'user') = 'user'
            order by updated_at desc
            limit ?
            """,
            (project_resolved, limit),
        ).fetchall()


def message_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for item in content:
            if isinstance(item, dict):
                value = item.get("text") or item.get("input_text") or item.get("output_text")
                if value:
                    chunks.append(str(value))
        return "\n".join(chunks)
    return ""


def extract_thread_notes(path: str, per_thread_limit: int = 8) -> dict:
    notes = []
    final_answers = []
    rollout = Path(path)
    if not rollout.exists():
        return {"notes": notes, "final_answers": final_answers}
    with rollout.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = event.get("payload", {})
            if event.get("type") == "response_item":
                if payload.get("type") == "message" and payload.get("role") == "user":
                    text = message_text(payload.get("content"))
                    if text:
                        append_unique(notes, text, 900)
                if payload.get("type") == "message" and payload.get("role") == "assistant" and payload.get("phase") == "final_answer":
                    text = message_text(payload.get("content"))
                    if text:
                        append_unique(final_answers, text, 700)
            if event.get("type") == "event_msg":
                if payload.get("type") == "user_message" and payload.get("message"):
                    append_unique(notes, payload.get("message"), 900)
                if payload.get("type") == "agent_message" and payload.get("phase") == "final_answer":
                    append_unique(final_answers, payload.get("message", ""), 700)
            if len(notes) >= per_thread_limit and len(final_answers) >= 3:
                break
    return {
        "notes": notes[:per_thread_limit],
        "final_answers": final_answers[:3],
    }


def validate_memory_payload(payload: dict, project: Path) -> dict:
    if not isinstance(payload, dict):
        raise SystemExit("The approved proposal must be a JSON object.")
    normalized = default_memory(project)
    normalized.update(
        {
            "schema": payload.get("schema", SCHEMA),
            "project": payload.get("project") or normalized["project"],
            "policy": payload.get("policy") or normalized["policy"],
        }
    )
    for key in MEMORY_KEYS:
        value = payload.get(key, [])
        if not isinstance(value, list):
            raise SystemExit(f"`{key}` must be a list.")
        normalized[key] = value
    return normalized


def cmd_init(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    path = memory_path(project)
    if path.exists() and not args.force:
        print(str(path))
        return
    print(str(write_memory(project, default_memory(project))))


def cmd_show(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    print(json.dumps(read_memory(project), indent=2, ensure_ascii=False))


def thread_summary(project: Path) -> dict:
    project_resolved = str(project.expanduser().resolve())
    with connect_state() as con:
        rows = con.execute(
            """
            select title, updated_at, rollout_path
            from threads
            where cwd = ?
              and coalesce(thread_source, 'user') = 'user'
            order by updated_at desc
            limit 5
            """,
            (project_resolved,),
        ).fetchall()
        count = con.execute(
            "select count(*) from threads where cwd = ? and coalesce(thread_source, 'user') = 'user'",
            (project_resolved,),
        ).fetchone()[0]
    latest = []
    for row in rows:
        latest.append(
            {
                "title": clean_preview(row["title"], 120),
                "updated_at": datetime.fromtimestamp(row["updated_at"], timezone.utc).isoformat(),
            }
        )
    return {"count": count, "latest": latest}


def clean_preview(value: str | None, limit: int) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def count_items(payload: dict | None, key: str) -> int:
    value = (payload or {}).get(key, [])
    return len(value) if isinstance(value, list) else 0


def item_text(item) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("text", "title", "summary", "value", "note"):
            if item.get(key):
                return str(item[key])
        return json.dumps(item, ensure_ascii=False)
    return str(item)


def first_items(payload: dict | None, key: str, limit: int = 3) -> list[str]:
    value = (payload or {}).get(key, [])
    if not isinstance(value, list):
        return []
    return [item_text(item) for item in value[:limit]]


def markdown_card(project: Path, payload: dict | None, path: Path, threads: dict) -> str:
    project_block = (payload or {}).get("project", {})
    name = project_block.get("name") or project.name
    status = "Memoria curada encontrada" if payload else "Sin memoria curada"
    lines = [
        f"### Lobotomize: {name}",
        "",
        f"**Estado:** {status}",
        f"**Archivo:** `{path}`",
        f"**Hilos Codex del proyecto:** {threads['count']}",
        "",
        "| Sección | Items | Vista rápida |",
        "|---|---:|---|",
    ]
    labels = [
        ("keep", "Conservar"),
        ("clarify", "Aclarar"),
        ("adapt", "Adaptar"),
        ("ignore", "Ignorar"),
        ("sensitive", "Sensible"),
    ]
    for key, label in labels:
        preview = "; ".join(first_items(payload, key, 2)) or "Sin items"
        lines.append(f"| {label} | {count_items(payload, key)} | {preview} |")
    if not payload:
        lines.extend(
            [
                "",
                "No se creó ningún archivo nuevo. Para inicializar una memoria curada, pide explícitamente: `inicializa lobotomize`.",
            ]
        )
    return "\n".join(lines)


def cmd_card(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    payload, path = read_memory_with_path(project)
    threads = thread_summary(project)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "project": str(project.resolve()),
                    "memory_file": str(path),
                    "has_curated_memory": payload is not None,
                    "counts": {
                        "keep": count_items(payload, "keep"),
                        "clarify": count_items(payload, "clarify"),
                        "adapt": count_items(payload, "adapt"),
                        "ignore": count_items(payload, "ignore"),
                        "sensitive": count_items(payload, "sensitive"),
                    },
                    "threads": threads,
                    "memory": payload,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    print(markdown_card(project, payload, path, threads))


def cmd_scan_context(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    payload = discover_memory_surfaces(project)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(markdown_discovery_card(payload))


def cmd_context_pack(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    payload = build_context_pack(project, args.include_preview)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(markdown_context_pack(payload))


def cmd_plan_exports(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    payload = build_export_plan(project, selected_export_targets(args.targets), args.include_content)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(markdown_export_plan(payload))


def cmd_merge_memories(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    payload = build_merged_memory(project, args.include_raw_entries)
    if args.proposal_out:
        out = Path(args.proposal_out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            json.dump(payload["proposal"], fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        payload["proposal_file"] = str(out)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(markdown_merged_memory(payload))


def cmd_apply_export_plan(args: argparse.Namespace) -> None:
    if not args.approved:
        raise SystemExit("Refusing to write export files without --approved.")
    plan_path = Path(args.plan).expanduser()
    if not plan_path.exists():
        raise SystemExit(f"Export plan not found: {plan_path}")
    with plan_path.open("r", encoding="utf-8") as fh:
        plan = json.load(fh)
    result = apply_export_plan(plan)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    lines = [
        f"### Lobotomize v2 Export Apply: {result['project'].get('name')}",
        "",
        f"**Proyecto:** `{result['project'].get('path')}`",
        f"**Operaciones aplicadas:** {len(result['operations'])}",
        "",
        "| Acción | Archivo | Bytes |",
        "|---|---|---:|",
    ]
    for operation in result["operations"]:
        lines.append(f"| {operation['action']} | `{operation['path']}` | {operation['bytes']} |")
    print("\n".join(lines))


def cmd_source_pack(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    memory, path = read_memory_with_path(project)
    rows = user_thread_rows(project, args.limit)
    threads = []
    for row in rows:
        extracted = extract_thread_notes(row["rollout_path"], args.per_thread_items)
        threads.append(
            {
                "id": row["id"],
                "title": clean_preview(row["title"], 160),
                "updated_at": datetime.fromtimestamp(row["updated_at"], timezone.utc).isoformat(),
                "git_branch": row["git_branch"],
                "git_sha": row["git_sha"],
                "notes": extracted["notes"],
                "final_answers": extracted["final_answers"],
            }
        )
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "generated_at": now_iso(),
                "project": {
                    "name": project_name(project),
                    "path": str(project.resolve()),
                },
                "memory_file": str(path),
                "has_curated_memory": memory is not None,
                "proposal_language": args.language,
                "interaction_language": "Use the user's current conversation language for questions, explanations, and the proposed memory unless the user requested another language.",
                "current_memory": memory,
                "threads": threads,
                "instruction": f"Draft a proposed memory.json in {args.language} using stable project facts, decisions, conventions, preferences, pitfalls, and open clarifications. Do not include secrets or raw transcripts.",
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def cmd_apply(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    proposal_path = Path(args.proposal).expanduser()
    if not proposal_path.exists():
        raise SystemExit(f"Approved proposal not found: {proposal_path}")
    with proposal_path.open("r", encoding="utf-8") as fh:
        proposal = json.load(fh)
    payload = validate_memory_payload(proposal, project)
    path = write_memory(project, payload)
    print(str(path))


def cmd_list_projects(_: argparse.Namespace) -> None:
    with connect_state() as con:
        rows = con.execute(
            """
            select cwd, count(*) as threads, max(updated_at) as updated_at
            from threads
            group by cwd
            order by updated_at desc
            """
        ).fetchall()
    for row in rows:
        updated = datetime.fromtimestamp(row["updated_at"], timezone.utc).isoformat()
        print(json.dumps({"project": row["cwd"], "threads": row["threads"], "updated_at": updated}, ensure_ascii=False))


def cmd_list_threads(args: argparse.Namespace) -> None:
    project = str(Path(args.project).expanduser().resolve())
    with connect_state() as con:
        rows = con.execute(
            """
            select id, title, rollout_path, memory_mode, git_branch, git_sha, updated_at
            from threads
            where cwd = ?
            order by updated_at desc
            limit ?
            """,
            (project, args.limit),
        ).fetchall()
    for row in rows:
        updated = datetime.fromtimestamp(row["updated_at"], timezone.utc).isoformat()
        print(
            json.dumps(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "memory_mode": row["memory_mode"],
                    "git_branch": row["git_branch"],
                    "git_sha": row["git_sha"],
                    "updated_at": updated,
                    "rollout_path": row["rollout_path"],
                },
                ensure_ascii=False,
            )
        )


def cmd_export(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    payload = read_memory(project)
    export_payload = {
        "schema": payload.get("schema", SCHEMA),
        "exported_at": now_iso(),
        "project": payload.get("project", {}),
        "policy": payload.get("policy", {}),
        "keep": payload.get("keep", []),
        "clarify": payload.get("clarify", []),
        "adapt": payload.get("adapt", []),
        "ignore": payload.get("ignore", []),
        "sources": payload.get("sources", []),
    }
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(export_payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(str(out))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Curate Codex project memory.")
    sub = p.add_subparsers(required=True)

    init = sub.add_parser("init", help="Create a curated project memory file.")
    init.add_argument("--project", required=True)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    show = sub.add_parser("show", help="Print the curated project memory file.")
    show.add_argument("--project", required=True)
    show.set_defaults(func=cmd_show)

    card = sub.add_parser("card", help="Render a compact project memory card.")
    card.add_argument("--project", required=True)
    card.add_argument("--format", choices=("markdown", "json"), default="markdown")
    card.set_defaults(func=cmd_card)

    scan_context = sub.add_parser("scan-context", help="Detect v2 memory and instruction surfaces across AI coding tools.")
    scan_context.add_argument("--project", required=True)
    scan_context.add_argument("--format", choices=("markdown", "json"), default="markdown")
    scan_context.set_defaults(func=cmd_scan_context)

    context_pack = sub.add_parser("context-pack", help="Normalize detected memory and instruction files into a v2 context pack.")
    context_pack.add_argument("--project", required=True)
    context_pack.add_argument("--format", choices=("markdown", "json"), default="markdown")
    context_pack.add_argument("--include-preview", action="store_true")
    context_pack.set_defaults(func=cmd_context_pack)

    plan_exports = sub.add_parser("plan-exports", help="Create a dry-run export plan from approved Lobotomize memory to other AI tools.")
    plan_exports.add_argument("--project", required=True)
    plan_exports.add_argument("--targets", default="all", help=f"Comma-separated targets or 'all'. Options: {', '.join(EXPORT_TARGETS)}")
    plan_exports.add_argument("--format", choices=("markdown", "json"), default="markdown")
    plan_exports.add_argument("--include-content", action="store_true", help="Include full generated file contents so an approved plan can be applied later.")
    plan_exports.set_defaults(func=cmd_plan_exports)

    merge_memories = sub.add_parser("merge-memories", help="Fuse detected project memories/rules into one structured analysis and proposal.")
    merge_memories.add_argument("--project", required=True)
    merge_memories.add_argument("--format", choices=("markdown", "json"), default="markdown")
    merge_memories.add_argument("--include-raw-entries", action="store_true")
    merge_memories.add_argument("--proposal-out", help="Write the merged curated-memory proposal JSON to this path for later approval.")
    merge_memories.set_defaults(func=cmd_merge_memories)

    apply_export_plan_parser = sub.add_parser("apply-export-plan", help="Apply a previously approved v2 export plan.")
    apply_export_plan_parser.add_argument("--plan", required=True)
    apply_export_plan_parser.add_argument("--approved", action="store_true")
    apply_export_plan_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    apply_export_plan_parser.set_defaults(func=cmd_apply_export_plan)

    source_pack = sub.add_parser("source-pack", help="Collect prior conversation context for a memory proposal.")
    source_pack.add_argument("--project", required=True)
    source_pack.add_argument("--limit", type=int, default=20)
    source_pack.add_argument("--per-thread-items", type=int, default=8)
    source_pack.add_argument("--language", default="the user's current conversation language")
    source_pack.set_defaults(func=cmd_source_pack)

    apply = sub.add_parser("apply", help="Apply an approved memory proposal.")
    apply.add_argument("--project", required=True)
    apply.add_argument("--proposal", required=True)
    apply.set_defaults(func=cmd_apply)

    projects = sub.add_parser("list-projects", help="List projects known to Codex.")
    projects.set_defaults(func=cmd_list_projects)

    threads = sub.add_parser("list-threads", help="List Codex threads for a project.")
    threads.add_argument("--project", required=True)
    threads.add_argument("--limit", type=int, default=25)
    threads.set_defaults(func=cmd_list_threads)

    export = sub.add_parser("export", help="Export team-safe memory without sensitive entries.")
    export.add_argument("--project", required=True)
    export.add_argument("--out", required=True)
    export.set_defaults(func=cmd_export)
    return p


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
