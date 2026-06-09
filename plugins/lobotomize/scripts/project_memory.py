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
