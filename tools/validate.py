#!/usr/bin/env python3
"""Validate NPG filter list JSON files against schema and content rules."""

import json
import ipaddress
import re
import sys
import os
from pathlib import Path

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("ERROR: jsonschema package required. Install with: pip install jsonschema")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema.json"
LISTS_DIR = REPO_ROOT / "lists"

MAX_ENTRIES_PER_FILE = 5000

# Private/reserved IP networks to reject
PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

# Expected directory for each type
TYPE_DIRECTORIES = {
    "ip": "lists/ips",
    "cidr": "lists/cidrs",
    "user_agent": "lists/user-agents",
}


def is_private_ip(addr):
    """Check if an IP address falls within private/reserved ranges."""
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    return any(ip in net for net in PRIVATE_NETWORKS)


def is_private_cidr(cidr_str):
    """Check if a CIDR range overlaps with private/reserved ranges."""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
    except ValueError:
        return False
    return any(network.overlaps(net) for net in PRIVATE_NETWORKS)


def validate_ip(value):
    """Validate an IP address string."""
    try:
        ipaddress.ip_address(value)
        return None
    except ValueError:
        return f"Invalid IP address: {value}"


def validate_cidr(value):
    """Validate a CIDR notation string."""
    try:
        ipaddress.ip_network(value, strict=False)
        return None
    except ValueError:
        return f"Invalid CIDR notation: {value}"


def validate_user_agent(value):
    """Validate that a user_agent value compiles as a regex."""
    try:
        re.compile(value)
        return None
    except re.error as e:
        return f"Invalid regex pattern '{value}': {e}"


def check_directory(file_path, list_type):
    """Check that the file is in the correct directory based on its type."""
    rel_path = file_path.relative_to(REPO_ROOT)
    expected_dir = TYPE_DIRECTORIES.get(list_type, "")
    if not str(rel_path).startswith(expected_dir):
        return f"File type '{list_type}' should be in '{expected_dir}/', but found at '{rel_path}'"
    return None


def validate_file(file_path, schema, seen_values):
    """Validate a single filter list file. Returns list of error strings."""
    errors = []
    rel_path = file_path.relative_to(REPO_ROOT)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"{rel_path}: Invalid JSON: {e}")
        return errors

    # Schema validation
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        errors.append(f"{rel_path}: Schema validation failed: {e.message}")
        return errors

    list_type = data.get("type", "")
    entries = data.get("entries", [])

    # Directory check
    dir_err = check_directory(file_path, list_type)
    if dir_err:
        errors.append(f"{rel_path}: {dir_err}")

    # Entry count check
    if len(entries) > MAX_ENTRIES_PER_FILE:
        errors.append(
            f"{rel_path}: Too many entries ({len(entries)} > {MAX_ENTRIES_PER_FILE})"
        )

    # Per-entry validation
    file_values = set()
    for i, entry in enumerate(entries):
        value = entry.get("value", "")

        # Reason check
        if not entry.get("reason", "").strip():
            errors.append(f"{rel_path}: Entry {i} missing 'reason'")

        # Type-specific validation
        if list_type == "ip":
            err = validate_ip(value)
            if err:
                errors.append(f"{rel_path}: Entry {i}: {err}")
            elif is_private_ip(value):
                errors.append(
                    f"{rel_path}: Entry {i}: Private/reserved IP not allowed: {value}"
                )
        elif list_type == "cidr":
            err = validate_cidr(value)
            if err:
                errors.append(f"{rel_path}: Entry {i}: {err}")
            elif is_private_cidr(value):
                errors.append(
                    f"{rel_path}: Entry {i}: Private/reserved CIDR not allowed: {value}"
                )
        elif list_type == "user_agent":
            err = validate_user_agent(value)
            if err:
                errors.append(f"{rel_path}: Entry {i}: {err}")

        # In-file duplicate check
        if value in file_values:
            errors.append(f"{rel_path}: Entry {i}: Duplicate value within file: {value}")
        file_values.add(value)

        # Cross-file duplicate check
        cross_key = (list_type, value)
        if cross_key in seen_values:
            errors.append(
                f"{rel_path}: Entry {i}: Duplicate value across files "
                f"(also in {seen_values[cross_key]}): {value}"
            )
        else:
            seen_values[cross_key] = str(rel_path)

    return errors


def main():
    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema file not found: {SCHEMA_PATH}")
        sys.exit(1)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    if not LISTS_DIR.exists():
        print("WARNING: lists/ directory not found, nothing to validate.")
        sys.exit(0)

    json_files = sorted(LISTS_DIR.rglob("*.json"))
    if not json_files:
        print("No filter list files found in lists/. Nothing to validate.")
        sys.exit(0)

    all_errors = []
    seen_values = {}  # (type, value) -> file_path for cross-file duplicate detection

    for file_path in json_files:
        errors = validate_file(file_path, schema, seen_values)
        all_errors.extend(errors)

    if all_errors:
        print(f"Validation FAILED with {len(all_errors)} error(s):\n")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"Validation PASSED: {len(json_files)} file(s) checked, no errors found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
