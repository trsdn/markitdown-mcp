#!/usr/bin/env python3
"""
Analyze commits to determine semantic version bump needed.
Used by GitHub Actions for automated version management.
"""

import os
import subprocess
import sys
from datetime import datetime


def main():
    # Get parameters from environment or command line
    latest_tag = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('LATEST_TAG', 'v0.0.0')
    force_bump = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('FORCE_BUMP', 'false')
    override_type = sys.argv[3] if len(sys.argv) > 3 else os.environ.get('OVERRIDE_TYPE', 'auto')

    # Get commits since last tag
    if latest_tag == 'v0.0.0':
        commit_range = 'HEAD'
    else:
        commit_range = f'{latest_tag}..HEAD'

    print(f'Analyzing commits since {latest_tag}')
    print(f'Commit range: {commit_range}')

    # Get commits
    result = subprocess.run(
        ['git', 'log', '--oneline', '--pretty=format:%s', commit_range],
        capture_output=True, text=True
    )
    commits = result.stdout.strip().split('\n') if result.stdout.strip() else []

    print(f'Found {len(commits)} commits')

    # Parse conventional commits
    breaking_changes = []
    features = []
    fixes = []
    other = []

    for commit in commits:
        if not commit.strip():
            continue

        print(f'  Analyzing: {commit[:60]}...')

        # Check for breaking changes
        if 'BREAKING CHANGE' in commit.upper():
            breaking_changes.append(commit)
            print(f'    -> BREAKING CHANGE')
        elif commit.startswith('feat'):
            features.append(commit)
            print(f'    -> FEATURE')
        elif commit.startswith(('fix', 'perf')):
            fixes.append(commit)
            print(f'    -> FIX/PERF')
        else:
            other.append(commit)
            print(f'    -> OTHER')

    # Determine version bump needed
    if breaking_changes:
        bump_type = 'major'
    elif features:
        bump_type = 'minor'
    elif fixes:
        bump_type = 'patch'
    else:
        bump_type = 'none'

    print(f'\nVersion analysis:')
    print(f'  Breaking changes: {len(breaking_changes)}')
    print(f'  Features: {len(features)}')
    print(f'  Fixes: {len(fixes)}')
    print(f'  Other: {len(other)}')
    print(f'  Recommended bump: {bump_type}')

    # Override if manual input provided
    if override_type != 'auto':
        print(f'  Override to: {override_type}')
        bump_type = override_type

    # Force bump if requested
    if force_bump == 'true' and bump_type == 'none':
        print(f'  Force bump: patch')
        bump_type = 'patch'

    # Calculate new version
    current_version = latest_tag.lstrip('v')
    if current_version == '0.0.0':
        new_version = '0.1.0'
    else:
        parts = current_version.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        elif bump_type == 'patch':
            patch += 1

        new_version = f'{major}.{minor}.{patch}'

    # Generate changelog
    changelog_entries = []

    if breaking_changes:
        changelog_entries.append('### ⚠️ BREAKING CHANGES')
        for commit in breaking_changes[:3]:
            desc = commit.split(':', 1)[1].strip() if ':' in commit else commit
            changelog_entries.append(f'- {desc}')
        changelog_entries.append('')

    if features:
        changelog_entries.append('### ✨ Features')
        for commit in features[:5]:
            desc = commit.split(':', 1)[1].strip() if ':' in commit else commit
            desc = desc.replace('feat(', '').replace('feat:', '').strip()
            if desc.startswith(')'): desc = desc[1:].strip()
            changelog_entries.append(f'- {desc}')
        if len(features) > 5:
            changelog_entries.append(f'- ... and {len(features) - 5} more features')
        changelog_entries.append('')

    if fixes:
        changelog_entries.append('### 🐛 Bug Fixes')
        for commit in fixes[:5]:
            desc = commit.split(':', 1)[1].strip() if ':' in commit else commit
            desc = desc.replace('fix(', '').replace('fix:', '').replace('perf(', '').replace('perf:', '').strip()
            if desc.startswith(')'): desc = desc[1:].strip()
            changelog_entries.append(f'- {desc}')
        if len(fixes) > 5:
            changelog_entries.append(f'- ... and {len(fixes) - 5} more fixes')
        changelog_entries.append('')

    changelog = '\n'.join(changelog_entries)
    needs_bump = bump_type != 'none'

    print(f'\nFinal results:')
    print(f'  Current version: {current_version}')
    print(f'  New version: {new_version}')
    print(f'  Bump type: {bump_type}')
    print(f'  Needs bump: {needs_bump}')

    # Output to GitHub Actions
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'needs-bump={str(needs_bump).lower()}\n')
            f.write(f'bump-type={bump_type}\n')
            f.write(f'new-version={new_version}\n')
            f.write(f'commits-count={len(commits)}\n')
            f.write(f'changelog<<EOF\n{changelog}\nEOF\n')
        print(f'✅ GitHub Actions outputs written')
    else:
        print(f'⚠️ No GITHUB_OUTPUT environment variable found')


if __name__ == '__main__':
    main()