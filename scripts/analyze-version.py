#!/usr/bin/env python3
"""
Analyze commits to determine semantic version bump needed.
Used by GitHub Actions for automated version management.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    # Check for help
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print("Usage: analyze-version.py [latest_tag] [force_bump] [override_type]")
        print("  latest_tag: e.g., 'v1.0.0' (default: v0.0.0)")
        print("  force_bump: 'true' or 'false' (default: false)")
        print("  override_type: 'auto', 'patch', 'minor', 'major' (default: auto)")
        sys.exit(0)

    # Get parameters from environment or command line
    latest_tag = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("LATEST_TAG", "v0.0.0")
    force_bump = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("FORCE_BUMP", "false")
    override_type = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("OVERRIDE_TYPE", "auto")

    # Validate latest_tag format
    if not latest_tag.startswith("v") or latest_tag.count(".") != 2:
        print(f"Warning: Invalid tag format '{latest_tag}', using v0.0.0")
        latest_tag = "v0.0.0"

    # Get commits since last tag
    commit_range = "HEAD" if latest_tag == "v0.0.0" else f"{latest_tag}..HEAD"

    print(f"Analyzing commits since {latest_tag}")
    print(f"Commit range: {commit_range}")

    # Get commits
    result = subprocess.run(
        ["git", "log", "--oneline", "--pretty=format:%s", commit_range],
        capture_output=True,
        text=True,
    )
    commits = result.stdout.strip().split("\n") if result.stdout.strip() else []

    print(f"Found {len(commits)} commits")

    # Parse conventional commits
    breaking_changes = []
    features = []
    fixes = []
    other = []

    for commit in commits:
        if not commit.strip():
            continue

        print(f"  Analyzing: {commit[:60]}...")

        # Check for breaking changes
        if "BREAKING CHANGE" in commit.upper():
            breaking_changes.append(commit)
            print("    -> BREAKING CHANGE")
        elif commit.startswith("feat"):
            features.append(commit)
            print("    -> FEATURE")
        elif commit.startswith(("fix", "perf")):
            fixes.append(commit)
            print("    -> FIX/PERF")
        else:
            other.append(commit)
            print("    -> OTHER")

    # Determine version bump needed
    if breaking_changes:
        bump_type = "major"
    elif features:
        bump_type = "minor"
    elif fixes:
        bump_type = "patch"
    else:
        bump_type = "none"

    print("\nVersion analysis:")
    print(f"  Breaking changes: {len(breaking_changes)}")
    print(f"  Features: {len(features)}")
    print(f"  Fixes: {len(fixes)}")
    print(f"  Other: {len(other)}")
    print(f"  Recommended bump: {bump_type}")

    # Override if manual input provided
    if override_type != "auto":
        print(f"  Override to: {override_type}")
        bump_type = override_type

    # Force bump if requested
    if force_bump == "true" and bump_type == "none":
        print("  Force bump: patch")
        bump_type = "patch"

    # Calculate new version
    current_version = latest_tag.lstrip("v")
    if current_version == "0.0.0":
        new_version = "0.1.0"
    else:
        parts = current_version.split(".")
        try:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            print(f"Error: Cannot parse version '{current_version}', using 0.1.0")
            new_version = "0.1.0"
            bump_type = "none"
        else:
            if bump_type == "major":
                major += 1
                minor = 0
                patch = 0
            elif bump_type == "minor":
                minor += 1
                patch = 0
            elif bump_type == "patch":
                patch += 1

            new_version = f"{major}.{minor}.{patch}"

    # Generate changelog
    changelog_entries = []

    if breaking_changes:
        changelog_entries.append("### ⚠️ BREAKING CHANGES")
        for commit in breaking_changes[:3]:
            desc = commit.split(":", 1)[1].strip() if ":" in commit else commit
            changelog_entries.append(f"- {desc}")
        changelog_entries.append("")

    if features:
        changelog_entries.append("### ✨ Features")
        for commit in features[:5]:
            desc = commit.split(":", 1)[1].strip() if ":" in commit else commit
            desc = desc.replace("feat(", "").replace("feat:", "").strip()
            if desc.startswith(")"):
                desc = desc[1:].strip()
            changelog_entries.append(f"- {desc}")
        if len(features) > 5:
            changelog_entries.append(f"- ... and {len(features) - 5} more features")
        changelog_entries.append("")

    if fixes:
        changelog_entries.append("### 🐛 Bug Fixes")
        for commit in fixes[:5]:
            desc = commit.split(":", 1)[1].strip() if ":" in commit else commit
            desc = (
                desc.replace("fix(", "")
                .replace("fix:", "")
                .replace("perf(", "")
                .replace("perf:", "")
                .strip()
            )
            if desc.startswith(")"):
                desc = desc[1:].strip()
            changelog_entries.append(f"- {desc}")
        if len(fixes) > 5:
            changelog_entries.append(f"- ... and {len(fixes) - 5} more fixes")
        changelog_entries.append("")

    changelog = "\n".join(changelog_entries)
    needs_bump = bump_type != "none"

    print("\nFinal results:")
    print(f"  Current version: {current_version}")
    print(f"  New version: {new_version}")
    print(f"  Bump type: {bump_type}")
    print(f"  Needs bump: {needs_bump}")

    # Output to GitHub Actions
    if "GITHUB_OUTPUT" in os.environ:
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as f:
            f.write(f"needs-bump={str(needs_bump).lower()}\n")
            f.write(f"bump-type={bump_type}\n")
            f.write(f"new-version={new_version}\n")
            f.write(f"commits-count={len(commits)}\n")
            f.write(f"changelog<<EOF\n{changelog}\nEOF\n")
        print("✅ GitHub Actions outputs written")
    else:
        print("⚠️ No GITHUB_OUTPUT environment variable found")


if __name__ == "__main__":
    main()
