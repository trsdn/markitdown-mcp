# PR Feedback & Issue Reporting System

This document describes the comprehensive PR feedback system that automatically detects, reports, and helps fix issues in pull requests.

## Overview

The PR feedback system consists of three complementary workflows that provide different types of feedback:

1. **PR Feedback & Issue Reporting** - Comprehensive analysis with detailed reports
2. **CI Quality Gates** - High-level status summary with quick fixes
3. **Code Annotations** - Inline comments and security-focused review

## Feedback Types

### 1. Comprehensive Issue Analysis (`pr-feedback.yml`)

**Purpose**: Deep analysis of all code quality, security, and maintainability issues

**Features**:
- 🎨 **Code Formatting**: Detects files needing `ruff format`
- 🔧 **Linting Issues**: Detailed breakdown by file and rule
- 📝 **Type Checking**: MyPy errors with specific locations
- 🔒 **Security Analysis**: Bandit findings with severity levels
- 📊 **Test Coverage**: File-by-file coverage analysis
- 🧹 **Dead Code Detection**: Unused functions and imports

**Comment Format**:
```markdown
## 🔍 PR Analysis Results

### 🎨 Code Formatting
❌ **3 file(s) need formatting**

<details><summary>Click to see formatting issues</summary>
- markitdown_mcp/server.py
- tests/test_server.py
</details>

### 🔧 Quick Fix Commands:
```bash
ruff format .
ruff check . --fix
```

**When It Runs**: On PR open/update, provides comprehensive feedback

### 2. CI Quality Gates Summary (`ci-gates.yml`)

**Purpose**: High-level overview of all quality gates with actionable guidance

**Features**:
- ✅/❌ **Status Table**: Clear pass/fail for each check
- 🛠️ **Action Required**: Specific commands to fix issues
- 🔗 **Quick Links**: Direct links to workflow logs
- 📊 **Coverage Tracking**: Real-time coverage percentage

**Comment Format**:
```markdown
## 🔍 CI Quality Gates Summary

**Overall Status**: ❌ Issues Found

| Check | Status | Details | Action Required |
|-------|--------|---------|-----------------|
| 🎨 Format | ❌ Failed | ruff format check | Run `ruff format .` |
| 🔧 Lint | ❌ Failed | ruff linting | Run `ruff check . --fix` |
| 📊 Coverage | 85.2% | Minimum: 80% | None |

### 🛠️ Quick Fix Commands
```bash
ruff format .
ruff check . --fix
pytest tests/unit/ --cov=markitdown_mcp
```

**When It Runs**: After all CI checks complete, provides summary status

### 3. Inline Code Annotations (`code-annotations.yml`)

**Purpose**: Inline comments directly on problematic code lines

**Features**:
- 🔍 **GitHub Annotations**: Comments appear directly on code lines
- 🚨 **Security Patterns**: Detects hardcoded secrets, SQL injection risks
- ⚠️ **Code Quality**: High complexity functions, missing docstrings
- 📝 **Debug Code**: Finds leftover print statements, TODO comments
- 🏗️ **Architecture Issues**: Large files, unsafe patterns

**Annotation Types**:
- `::error::` - Critical issues (security, broken code)
- `::warning::` - Important issues (complexity, debug code)
- `::notice::` - Suggestions (missing docstrings, TODOs)

**When It Runs**: On PR open/update, provides line-by-line feedback

## Best Practices for Developers

### Understanding Feedback Levels

1. **🚨 Critical (Must Fix)**:
   - Security vulnerabilities (HIGH severity)
   - Failing tests
   - Build errors
   - Hardcoded secrets

2. **⚠️ Important (Should Fix)**:
   - Linting violations
   - Type errors
   - Coverage below 80%
   - Code complexity issues

3. **📝 Suggestions (Consider)**:
   - Missing docstrings
   - TODO comments
   - Code style improvements
   - Performance optimizations

### Responding to Feedback

#### For Format/Lint Issues:
```bash
# Auto-fix most formatting and linting issues
ruff format .
ruff check . --fix

# Commit the fixes
git add .
git commit -m "fix: apply automated formatting and linting fixes"
```

#### For Test Coverage Issues:
```bash
# Check current coverage
pytest tests/unit/ --cov=markitdown_mcp --cov-report=term-missing

# Identify uncovered lines and add tests
pytest tests/unit/ --cov=markitdown_mcp --cov-report=html
open htmlcov/index.html  # View detailed coverage report
```

#### For Security Issues:
```bash
# Review security findings
bandit -r markitdown_mcp/ -f json

# Fix hardcoded secrets by using environment variables
# Fix SQL injection by using parameterized queries
# Fix file handling by using 'with' statements
```

#### For Type Issues:
```bash
# Check type errors
mypy markitdown_mcp

# Add type annotations to resolve issues
# Example: def process_file(path: str) -> Dict[str, Any]:
```

### PR Labels

The system automatically applies labels based on issues found:

- `needs-formatting` - Files need `ruff format`
- `needs-linting` - Linting violations found
- `security-review` - Security issues require attention
- `needs-fixes` - General issues (1-10 problems)
- `needs-major-fixes` - Many issues (10+ problems)

### Automated Actions

The system takes these automatic actions:

1. **Request Changes**: For critical security issues
2. **Add Labels**: Based on issue types and severity
3. **Block Merge**: Via required status checks
4. **Update Comments**: When new commits are pushed

## Best Practices for Reviewers

### Using Automated Feedback

1. **Start with Automated Analysis**: Review the comprehensive PR analysis first
2. **Check Critical Issues**: Ensure security and build issues are addressed
3. **Verify Fixes**: Confirm that automated suggestions were properly implemented
4. **Focus on Logic**: Spend review time on business logic, not style issues

### Manual Review Focus Areas

Since automated tools handle code quality, focus on:

- **Business Logic**: Does the code solve the right problem?
- **Architecture**: Does it fit well with existing code?
- **Edge Cases**: Are error conditions handled properly?
- **Documentation**: Are complex changes well-documented?
- **Performance**: Are there obvious performance issues?
- **Maintainability**: Is the code easy to understand and modify?

### Review Checklist

- [ ] All automated checks pass
- [ ] Security issues are resolved
- [ ] Code coverage is adequate
- [ ] Business logic is correct
- [ ] Error handling is appropriate
- [ ] Documentation is updated
- [ ] Tests cover new functionality

## Workflow Integration

### Required Status Checks

These checks must pass before merge:
- Fast Tests Summary
- All CI Gates Passed
- Test Results Summary
- Security

### Comment Management

- **Sticky Comments**: Updated in-place, not duplicated
- **Unique Headers**: Each workflow has distinct comment sections
- **Progressive Enhancement**: Comments get more detailed as analysis completes

### Performance Considerations

- **Parallel Execution**: All analysis runs concurrently
- **Smart Caching**: Tools use pip/action caching
- **Fail Fast**: Critical issues stop unnecessary processing
- **Artifact Storage**: Detailed reports saved for investigation

## Troubleshooting

### Common Issues

**Comment Not Appearing**:
- Check workflow permissions (`pull-requests: write`)
- Verify PR is from a fork with appropriate permissions
- Check for workflow syntax errors

**Incorrect Issue Detection**:
- Review tool configuration in `pyproject.toml`
- Check if issues are in ignored files/paths
- Verify tool versions are current

**Performance Problems**:
- Check if large files are being analyzed unnecessarily
- Review timeout settings in workflows
- Consider splitting analysis across more jobs

### Debug Commands

```bash
# Run analysis locally to debug issues
ruff check . --output-format=json
mypy markitdown_mcp --json-report mypy_report.json
bandit -r markitdown_mcp/ -f json
pytest --cov=markitdown_mcp --cov-report=json

# Check workflow syntax
gh workflow view pr-feedback.yml
gh workflow list

# Monitor workflow runs
gh run list --workflow="PR Feedback"
gh run view <run-id> --log-failed
```

## Customization

### Adding New Checks

To add new automated checks:

1. **Add tool installation** to workflow
2. **Create analysis logic** with JSON output
3. **Parse results** into GitHub annotations or comments
4. **Update documentation** with new check description

### Modifying Thresholds

Common thresholds to adjust:

- **Coverage minimum**: Currently 80% (in multiple workflows)
- **Security severity**: Currently blocks on HIGH, warns on MEDIUM
- **Complexity limit**: Currently warns at 10+ cyclomatic complexity
- **File size warning**: Currently warns at 1MB+

### Custom Rules

Add project-specific rules by:

1. **Extending tool configs** in `pyproject.toml`
2. **Adding custom scripts** for domain-specific checks
3. **Creating specialized workflows** for unique requirements

## Integration Examples

### For New Team Members

The feedback system helps new contributors by:
- Providing immediate guidance on code standards
- Teaching project conventions through automated suggestions
- Reducing review burden on maintainers
- Ensuring consistent code quality

### For Complex Changes

For large PRs, the system:
- Breaks down issues by category and file
- Provides step-by-step fix instructions
- Tracks progress as issues are resolved
- Maintains history of improvements

### For Security-Sensitive Code

Security-focused features:
- Automatic detection of common vulnerabilities
- Immediate feedback on security anti-patterns
- Required review for security-labeled PRs
- Integration with security scanning tools

This comprehensive feedback system ensures high code quality while reducing manual review overhead and providing educational value for all contributors.