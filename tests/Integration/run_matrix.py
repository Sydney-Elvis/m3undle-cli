#!/usr/bin/env python3
"""Run Docker integration scenarios for the M3Undle CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run M3Undle CLI integration scenarios.")
    parser.add_argument("--cli", required=True, help="Path to the CLI executable.")
    parser.add_argument("--playlist", required=True, help="Playlist source path or URL.")
    parser.add_argument("--epg", default="", help="EPG source path or URL.")
    parser.add_argument("--output-dir", required=True, help="Directory for scenario output.")
    parser.add_argument("--matrix", required=True, help="Path to the JSON matrix file.")
    return parser.parse_args()


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-") or "scenario"


def render_tokens(values: list[str], replacements: dict[str, str]) -> list[str]:
    return [value.format(**replacements) for value in values]


def load_matrix(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)

    scenarios = document.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError(f"{path} must contain a 'scenarios' array.")

    return scenarios


def write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def validate_outputs(scenario_dir: Path, names: list[str]) -> list[str]:
    failures: list[str] = []

    for name in names:
        output_path = scenario_dir / name
        if not output_path.exists():
            failures.append(f"missing expected output: {output_path}")
            continue

        if output_path.stat().st_size == 0:
            failures.append(f"expected output is empty: {output_path}")

    return failures


def run_scenario(
    scenario: dict[str, Any],
    cli_path: Path,
    output_root: Path,
    playlist_source: str,
    epg_source: str,
    timeout_seconds: int,
) -> tuple[bool, str]:
    name = str(scenario.get("name", "scenario"))
    scenario_dir = output_root / "scenarios" / slug(name)
    scenario_dir.mkdir(parents=True, exist_ok=True)

    command_name = str(scenario.get("command", "")).strip()
    if not command_name:
        return False, f"{name}: missing command"

    raw_args = scenario.get("args", [])
    if not isinstance(raw_args, list) or not all(isinstance(value, str) for value in raw_args):
        return False, f"{name}: args must be an array of strings"

    replacements = {
        "playlist_url": playlist_source,
        "epg_url": epg_source,
        "scenario_dir": str(scenario_dir),
    }
    command = [str(cli_path), command_name, *render_tokens(raw_args, replacements)]
    write_text(scenario_dir / "command.txt", " ".join(command) + "\n")

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as ex:
        write_text(scenario_dir / "stdout.txt", ex.stdout or "")
        write_text(scenario_dir / "stderr.txt", ex.stderr or "")
        return False, f"{name}: timed out after {timeout_seconds}s"

    write_text(scenario_dir / "stdout.txt", result.stdout)
    write_text(scenario_dir / "stderr.txt", result.stderr)

    expect_success = bool(scenario.get("expectSuccess", True))
    succeeded = result.returncode == 0
    if succeeded != expect_success:
        expectation = "success" if expect_success else "failure"
        return False, f"{name}: expected {expectation}, got exit code {result.returncode}"

    output_names = scenario.get("validateOutputs", [])
    if not isinstance(output_names, list) or not all(isinstance(value, str) for value in output_names):
        return False, f"{name}: validateOutputs must be an array of strings"

    if expect_success:
        output_failures = validate_outputs(scenario_dir, output_names)
        if output_failures:
            return False, f"{name}: " + "; ".join(output_failures)

    return True, f"{name}: passed"


def main() -> int:
    args = parse_args()
    cli_path = Path(args.cli)
    output_root = Path(args.output_dir)
    matrix_path = Path(args.matrix)
    timeout_seconds = int(os.environ.get("SCENARIO_TIMEOUT_SECONDS", "60"))

    output_root.mkdir(parents=True, exist_ok=True)

    try:
        scenarios = load_matrix(matrix_path)
    except Exception as ex:
        print(f"[matrix] failed to load matrix: {ex}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for scenario in scenarios:
        passed, message = run_scenario(
            scenario,
            cli_path,
            output_root,
            args.playlist,
            args.epg,
            timeout_seconds,
        )

        stream = sys.stdout if passed else sys.stderr
        print(f"[matrix] {message}", file=stream)
        if not passed:
            failures.append(message)

    if failures:
        print(f"[matrix] {len(failures)} scenario(s) failed.", file=sys.stderr)
        return 1

    print(f"[matrix] {len(scenarios)} scenario(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
