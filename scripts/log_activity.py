#!/usr/bin/env python3
"""Append structured entries to SYSTEM_ACTIVITY.md for every user request."""

from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent


LOG_FILE = Path("SYSTEM_ACTIVITY.md")


def build_entry(title: str, user_request: str, actions: str, notes: str | None) -> str:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
    entry_lines = [
        f"## {timestamp} — {title}",
        f"- **Request**: {user_request.strip()}",
        f"- **Actions**: {actions.strip()}",
    ]
    if notes:
        entry_lines.append(f"- **Notes**: {notes.strip()}")

    return "\n".join(entry_lines) + "\n"


def append_entry(entry: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text(
            dedent(
                """\
                # System Activity Log

                This is the central log for every user request and the associated actions.
                """
            )
        )
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write("\n" + entry)


def main() -> None:
    parser = ArgumentParser(description="Add an entry to the system activity log.")
    parser.add_argument("--title", "-t", default="Manual update", help="Short title for this entry.")
    parser.add_argument("--request", "-r", required=True, help="The user request text.")
    parser.add_argument(
        "--actions", "-a", required=True, help="Summary of the work performed."
    )
    parser.add_argument("--notes", "-n", help="Optional follow-up or verification notes.")
    args = parser.parse_args()

    append_entry(build_entry(args.title, args.request, args.actions, args.notes))


if __name__ == "__main__":
    main()
