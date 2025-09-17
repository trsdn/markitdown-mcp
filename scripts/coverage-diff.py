#!/usr/bin/env python3
"""
Coverage comparison script for CI.

Compares current coverage with base branch to detect coverage regressions.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


def load_coverage(coverage_file: Path) -> Optional[Dict]:
    """Load coverage data from JSON file."""
    try:
        with open(coverage_file) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_coverage_summary(coverage_data: Dict) -> Tuple[float, Dict[str, float]]:
    """Extract coverage summary from coverage data."""
    total_coverage = coverage_data["totals"]["percent_covered"]

    file_coverage = {}
    for filename, file_data in coverage_data.get("files", {}).items():
        if "summary" in file_data:
            file_coverage[filename] = file_data["summary"]["percent_covered"]

    return total_coverage, file_coverage


def compare_coverage(
    current_file: Path,
    base_file: Optional[Path] = None
) -> Dict[str, any]:
    """Compare current coverage with base coverage."""
    current_data = load_coverage(current_file)
    if not current_data:
        return {"error": f"Could not load current coverage from {current_file}"}

    current_total, current_files = get_coverage_summary(current_data)

    result = {
        "current_coverage": current_total,
        "base_coverage": None,
        "diff": 0,
        "status": "new",
        "file_changes": [],
        "summary": f"Coverage: {current_total:.1f}%"
    }

    if base_file and base_file.exists():
        base_data = load_coverage(base_file)
        if base_data:
            base_total, base_files = get_coverage_summary(base_data)

            result["base_coverage"] = base_total
            result["diff"] = current_total - base_total
            result["status"] = "improved" if result["diff"] > 0 else "decreased" if result["diff"] < 0 else "same"

            # Check file-level changes
            for filename in set(current_files.keys()) | set(base_files.keys()):
                current_cov = current_files.get(filename, 0)
                base_cov = base_files.get(filename, 0)
                diff = current_cov - base_cov

                if abs(diff) > 1:  # Only report significant changes
                    result["file_changes"].append({
                        "file": filename,
                        "current": current_cov,
                        "base": base_cov,
                        "diff": diff
                    })

            # Update summary
            if result["diff"] > 0:
                result["summary"] = f"Coverage: {current_total:.1f}% (+{result['diff']:.1f}%) ⬆️"
            elif result["diff"] < 0:
                result["summary"] = f"Coverage: {current_total:.1f}% ({result['diff']:.1f}%) ⬇️"
            else:
                result["summary"] = f"Coverage: {current_total:.1f}% (no change)"

    return result


def generate_coverage_comment(comparison: Dict) -> str:
    """Generate markdown comment for coverage comparison."""
    lines = []

    # Header
    lines.append("## 📊 Coverage Report")
    lines.append("")

    # Summary
    status_emoji = {
        "improved": "✅",
        "decreased": "⚠️",
        "same": "➡️",
        "new": "🆕"
    }

    emoji = status_emoji.get(comparison["status"], "ℹ️")
    lines.append(f"{emoji} **{comparison['summary']}**")
    lines.append("")

    if comparison["base_coverage"] is not None:
        # Detailed comparison
        lines.append("| Metric | Current | Base | Change |")
        lines.append("|--------|---------|------|--------|")
        lines.append(f"| Total Coverage | {comparison['current_coverage']:.1f}% | {comparison['base_coverage']:.1f}% | {comparison['diff']:+.1f}% |")
        lines.append("")

        # File-level changes
        if comparison["file_changes"]:
            lines.append("### File-level Changes")
            lines.append("")
            lines.append("| File | Current | Base | Change |")
            lines.append("|------|---------|------|--------|")

            for change in comparison["file_changes"][:10]:  # Limit to 10 files
                lines.append(f"| {change['file']} | {change['current']:.1f}% | {change['base']:.1f}% | {change['diff']:+.1f}% |")

            if len(comparison["file_changes"]) > 10:
                lines.append(f"*... and {len(comparison['file_changes']) - 10} more files*")
            lines.append("")

    # Threshold check
    if comparison["current_coverage"] < 80:
        lines.append("⚠️ **Coverage is below 80% threshold**")
        lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: coverage-diff.py <current_coverage.json> [base_coverage.json]")
        sys.exit(1)

    current_file = Path(sys.argv[1])
    base_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    comparison = compare_coverage(current_file, base_file)

    if "error" in comparison:
        print(f"Error: {comparison['error']}")
        sys.exit(1)

    # Print summary for CI logs
    print(comparison["summary"])

    if comparison["diff"] < -5:  # Significant decrease
        print(f"⚠️ Coverage decreased by {abs(comparison['diff']):.1f}%")
        sys.exit(1)

    # Output markdown for PR comments
    comment = generate_coverage_comment(comparison)
    with open("coverage-comment.md", "w") as f:
        f.write(comment)

    print("📝 Coverage comment written to coverage-comment.md")


if __name__ == "__main__":
    main()