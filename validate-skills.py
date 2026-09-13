#!/usr/bin/env python3
"""Validate OpenCode skills without third-party YAML dependencies."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", re.IGNORECASE)
TRIGGERS = ("usar cuando", "usar para", "use when", "use only when")
INVALID = object()


def simple_scalar(raw: str, *, allow_empty: bool = False) -> str | object:
    value = raw.strip()
    if not value:
        return "" if allow_empty else INVALID

    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return INVALID
        return parsed if isinstance(parsed, str) else INVALID

    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            return INVALID
        return value[1:-1].replace("''", "'")

    if value.endswith(("'", '"')):
        return INVALID
    if value[0] in "[{>|&*!" or value.startswith(("- ", "? ")):
        return INVALID
    if value.casefold() in {"null", "~", "true", "false"} or NUMBER_RE.fullmatch(value):
        return INVALID
    return value


def parse_skill(path: Path, folder_name: str) -> tuple[list[tuple[str, str]], str | None]:
    errors: list[tuple[str, str]] = []
    display = str(path)

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [(display, f"cannot read UTF-8 file: {exc}")], None

    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return [(display, "missing YAML frontmatter")], None

    closing = next((index for index, line in enumerate(lines[1:], 1) if line == "---"), None)
    if closing is None:
        return [(display, "unterminated YAML frontmatter")], None

    fields: dict[str, str] = {}
    seen_fields: set[str] = set()
    metadata_seen = False
    metadata_entries: set[str] = set()
    in_metadata = False

    for index, line in enumerate(lines[1:closing], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            errors.append((display, f"line {index}: tabs are not allowed in frontmatter"))
            continue

        if line[0].isspace():
            if not in_metadata:
                errors.append((display, f"line {index}: unexpected indentation"))
                continue
            entry = line.strip()
            if ":" not in entry:
                errors.append((display, f"line {index}: metadata entry must be key: value"))
                continue
            raw_key, raw_value = entry.split(":", 1)
            key = simple_scalar(raw_key)
            value = simple_scalar(raw_value)
            if key is INVALID or value is INVALID:
                errors.append((display, f"line {index}: metadata must contain non-empty string-to-string entries"))
                continue
            assert isinstance(key, str)
            if key in metadata_entries:
                errors.append((display, f"line {index}: duplicate metadata key '{key}'"))
            metadata_entries.add(key)
            continue

        in_metadata = False
        if ":" not in line:
            errors.append((display, f"line {index}: malformed frontmatter field"))
            continue

        key, raw_value = (part.strip() for part in line.split(":", 1))
        if key not in ALLOWED_FIELDS:
            errors.append((display, f"line {index}: unknown top-level field '{key}'"))
            continue
        if key in seen_fields:
            errors.append((display, f"line {index}: duplicate top-level field '{key}'"))
            continue
        seen_fields.add(key)

        if key == "metadata":
            metadata_seen = True
            if raw_value:
                errors.append((display, f"line {index}: metadata must be an indented string-to-string map"))
            else:
                in_metadata = True
            continue

        value = simple_scalar(raw_value, allow_empty=key in {"name", "description"})
        if value is INVALID:
            errors.append((display, f"line {index}: '{key}' must be a simple string scalar"))
            continue
        assert isinstance(value, str)
        fields[key] = value

    if metadata_seen and not metadata_entries:
        errors.append((display, "metadata must be a non-empty string-to-string map"))

    name = fields.get("name")
    if not name:
        errors.append((display, "missing or empty name"))
    else:
        if not 1 <= len(name) <= 64:
            errors.append((display, "name length must be 1-64 characters"))
        if not NAME_RE.fullmatch(name):
            errors.append((display, "name must match ^[a-z0-9]+(-[a-z0-9]+)*$"))
        if name != folder_name:
            errors.append((display, f"name '{name}' does not match folder '{folder_name}'"))

    description = fields.get("description")
    if not description:
        errors.append((display, "missing or empty description"))
    else:
        if not 1 <= len(description) <= 1024:
            errors.append((display, "description length must be 1-1024 characters"))
        folded = description.casefold()
        if not any(trigger in folded for trigger in TRIGGERS):
            errors.append((display, "description must contain an accepted trigger phrase"))

    if not "\n".join(lines[closing + 1 :]).strip():
        errors.append((display, "Markdown body must not be empty"))

    return errors, name


def validate(root: Path) -> tuple[list[tuple[str, str]], int]:
    display = str(root)
    if not root.exists():
        return [(display, "path does not exist")], 0
    if not root.is_dir():
        return [(display, "path is not a directory")], 0

    try:
        entries = sorted(root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        return [(display, f"cannot read directory: {exc}")], 0
    if not entries:
        return [(display, "skills directory is empty")], 0

    errors: list[tuple[str, str]] = []
    skill_files: list[Path] = []
    index_files: list[Path] = []

    def walk_error(exc: OSError) -> None:
        errors.append((exc.filename or display, f"cannot read directory: {exc}"))

    for directory, dirnames, filenames in os.walk(root, onerror=walk_error, followlinks=False):
        dirnames.sort()
        filenames.sort()
        base = Path(directory)
        for filename in filenames:
            candidate = base / filename
            if filename == "SKILL.md":
                skill_files.append(candidate)
            elif filename == "SKILL_INDEX.md":
                index_files.append(candidate)

    for path in index_files:
        errors.append((str(path), "SKILL_INDEX.md is not allowed"))

    direct_dirs = [entry for entry in entries if entry.is_dir()]
    direct_skills: list[Path] = []
    for path in skill_files:
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            errors.append((str(path), "SKILL.md is outside the skills path"))
            continue
        if len(parts) != 2:
            kind = "stray" if len(parts) == 1 else "nested"
            errors.append((str(path), f"{kind} SKILL.md; expected PATH/<folder>/SKILL.md"))
            continue
        direct_skills.append(path)

    direct_set = set(direct_skills)
    for folder in direct_dirs:
        expected = folder / "SKILL.md"
        if expected not in direct_set:
            errors.append((str(expected), "missing SKILL.md"))

    if not direct_skills:
        errors.append((display, "no direct skills found"))

    names: defaultdict[str, list[Path]] = defaultdict(list)
    for path in sorted(direct_skills, key=str):
        skill_errors, name = parse_skill(path, path.parent.name)
        errors.extend(skill_errors)
        if name:
            names[name].append(path)

    for name, paths in sorted(names.items()):
        if len(paths) > 1:
            for path in paths:
                errors.append((str(path), f"duplicate name '{name}'"))

    return sorted(errors), len(direct_skills)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 validate-skills.py PATH", file=sys.stderr)
        return 1

    errors, count = validate(Path(argv[1]))
    if errors:
        for path, message in errors:
            print(f"{path}: {message}", file=sys.stderr)
        return 1

    print(f"[ok] {count} skills valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
