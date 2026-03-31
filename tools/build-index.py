#!/usr/bin/env python3
"""Build index.json from all filter list files in lists/ directory."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LISTS_DIR = REPO_ROOT / "lists"
INDEX_PATH = REPO_ROOT / "index.json"


def build_index():
    if not LISTS_DIR.exists():
        print("WARNING: lists/ directory not found.")
        return {"generated_at": datetime.now(timezone.utc).isoformat(), "lists": []}

    json_files = sorted(LISTS_DIR.rglob("*.json"))
    lists = []

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"WARNING: Skipping {file_path}: {e}")
            continue

        rel_path = file_path.relative_to(REPO_ROOT)
        mtime = os.path.getmtime(file_path)
        updated_at = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        lists.append(
            {
                "path": str(rel_path),
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "type": data.get("type", ""),
                "expires": data.get("expires", ""),
                "entry_count": len(data.get("entries", [])),
                "updated_at": updated_at,
            }
        )

    index = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_lists": len(lists),
        "lists": lists,
    }

    return index


def main():
    index = build_index()

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"index.json generated: {index['total_lists']} list(s) indexed.")


if __name__ == "__main__":
    main()
