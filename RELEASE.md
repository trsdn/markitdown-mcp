# Release Process Guide

This document outlines the complete release process for MarkItDown MCP Server, including automated workflows, version management, and procedures for both humans and AI agents.

## 🎯 Release Overview

MarkItDown MCP Server follows **Semantic Versioning** with **fully automated releases** triggered by conventional commits and managed through CI/CD pipelines.

### Release Types

- **Major Release** (`x.0.0`): Breaking changes or major new features
- **Minor Release** (`x.y.0`): New features, backward compatible
- **Patch Release** (`x.y.z`): Bug fixes, backward compatible
- **Pre-Release** (`x.y.z-rc.n`): Release candidates for testing
- **Hotfix Release** (`x.y.z-hotfix.n`): Emergency fixes for critical issues

## 🤖 Automated Release System

### Conventional Commits

All commits **MUST** follow conventional commit format for automated version detection:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

#### Commit Types

| Type | Description | Version Impact |
|------|-------------|----------------|
| `feat` | New feature | Minor (0.1.0) |
| `fix` | Bug fix | Patch (0.0.1) |
| `docs` | Documentation only | None |
| `style` | Code formatting, no logic change | None |
| `refactor` | Code restructuring, no feature change | None |
| `perf` | Performance improvement | Patch (0.0.1) |
| `test` | Testing changes | None |
| `chore` | Build process, dependencies | None |
| `ci` | CI/CD changes | None |
| `BREAKING CHANGE` | Breaking API change | Major (1.0.0) |

#### Examples

```bash
# Minor version bump (new feature)
feat(mcp): add support for PowerBI files

# Patch version bump (bug fix)
fix(security): resolve path traversal vulnerability

# Major version bump (breaking change)
feat(api): redesign tool interface

BREAKING CHANGE: tool parameters now require explicit types
```

### Version Calculation

The automated system calculates the next version based on commits since the last release:

1. **Scan commits** since last tag
2. **Identify highest impact** change type
3. **Calculate new version** using semantic versioning
4. **Generate changelog** from commit messages
5. **Create release** with automated notes

## 🚀 Release Workflows

### 1. Automated Release (`release.yml`)

**Trigger**: Push of version tag (`v*.*.*`)

**Process**:
1. **Quality Gates**: All CI checks must pass
2. **Build & Test**: Package built and tested in clean environment
3. **Security Scan**: Final security validation
4. **Changelog**: Generated from conventional commits
5. **PyPI Publish**: Package published to Python Package Index
6. **GitHub Release**: Created with automated release notes
7. **Documentation**: Updated with new version

**Example Trigger**:
```bash
git tag v1.2.3
git push origin v1.2.3
```

### 2. Version Bump (`version-bump.yml`)

**Trigger**:
- Merge to main branch
- Manual workflow dispatch
- Scheduled (weekly)

**Process**:
1. **Analyze Commits**: Parse conventional commits since last release
2. **Calculate Version**: Determine semantic version bump
3. **Update Files**: Update `pyproject.toml` and `CHANGELOG.md`
4. **Create PR**: Submit version bump pull request
5. **Auto-tag**: Create git tag when PR is merged

### 3. Pre-Release (`pre-release.yml`)

**Trigger**: Manual workflow dispatch

**Process**:
1. **Create RC Tag**: `v1.2.3-rc.1`
2. **Build Package**: Test package creation
3. **Run Full Tests**: Complete test suite
4. **Test PyPI**: Publish to test.pypi.org
5. **Generate Notes**: Release candidate documentation

### 4. Hotfix Release (`hotfix-release.yml`)

**Trigger**: Push to `hotfix/*` branch

**Process**:
1. **Emergency Validation**: Critical security and functionality checks
2. **Fast Track**: Bypass normal review process for critical fixes
3. **Immediate Release**: Create patch release within 1 hour
4. **Backport**: Apply fix to all supported versions
5. **Post-Fix Review**: Comprehensive review after release

## 📋 Release Checklist

### Pre-Release Validation

- [ ] All CI quality gates pass (format, lint, type, security)
- [ ] Test coverage maintains minimum threshold (80%)
- [ ] All tests pass on supported Python versions (3.10, 3.11, 3.12)
- [ ] MCP protocol compliance verified
- [ ] Documentation updated and builds successfully
- [ ] Breaking changes documented with migration guide
- [ ] Security scan clean (no high/critical vulnerabilities)

### Release Artifacts

- [ ] Git tag created (`v*.*.*` format)
- [ ] GitHub release with generated notes
- [ ] PyPI package published
- [ ] Documentation deployed
- [ ] CHANGELOG.md updated
- [ ] Version in pyproject.toml updated

### Post-Release Validation

- [ ] Package installable via pip
- [ ] MCP server starts correctly
- [ ] All tools function as expected
- [ ] Documentation accessible
- [ ] No broken links or references

## 🔧 Manual Release Process

### For Emergency Situations

If automated systems fail, manual release process:

1. **Validate Environment**:
   ```bash
   # Ensure clean state
   git status
   git pull origin main

   # Run quality checks
   ruff format --check
   ruff check
   mypy markitdown_mcp/ --strict
   ```

2. **Update Version**:
   ```bash
   # Edit pyproject.toml version
   vim pyproject.toml

   # Update CHANGELOG.md
   vim CHANGELOG.md
   ```

3. **Create Release**:
   ```bash
   # Commit version changes
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to v1.2.3"

   # Create and push tag
   git tag v1.2.3
   git push origin main
   git push origin v1.2.3
   ```

4. **Build and Publish**:
   ```bash
   # Build package
   python -m build

   # Publish to PyPI
   python -m twine upload dist/*
   ```

## 🛡️ Security Considerations

### Release Security

- **GPG Signing**: All release tags must be GPG signed
- **Credential Management**: PyPI tokens stored as GitHub secrets
- **Artifact Verification**: SHA checksums for all release artifacts
- **Vulnerability Scanning**: Automated security scans before release
- **Supply Chain**: Dependencies pinned and verified

### Emergency Response

- **Security Hotfixes**: Can be released within 2 hours
- **Vulnerability Disclosure**: Follow responsible disclosure timeline
- **CVE Assignment**: Request CVE for security vulnerabilities
- **User Notification**: Security advisories via GitHub Security

## 📊 Release Metrics

### Automated Tracking

- **Release Frequency**: Target monthly minor releases
- **Time to Release**: Measure automation performance
- **Quality Metrics**: Track test coverage and bug counts
- **User Adoption**: Monitor PyPI download statistics
- **Breaking Changes**: Minimize in minor/patch releases

### Success Criteria

- **Automation Rate**: >95% of releases fully automated
- **Quality Gates**: 100% pass rate before release
- **Time to Fix**: <24 hours for critical bugs
- **User Impact**: <1% breaking change complaints
- **Documentation**: 100% coverage of new features

## 🤝 AI Agent Integration

### For AI Development Tools

AI agents (like Claude Code, GitHub Copilot, etc.) should follow these guidelines:

#### Commit Message Generation
```python
def generate_commit_message(changes):
    # Analyze changes to determine type
    if has_breaking_changes(changes):
        return "feat: add new feature\n\nBREAKING CHANGE: API signature changed"
    elif has_new_features(changes):
        return "feat: add support for new file format"
    elif has_bug_fixes(changes):
        return "fix: resolve memory leak in file processing"
    else:
        return "chore: update dependencies"
```

#### Version Bump Detection
```python
def should_create_release(commit_history):
    # Check if significant changes warrant release
    significant_changes = count_feat_and_fix_commits(commit_history)
    return significant_changes >= 3 or has_security_fixes(commit_history)
```

#### Release Validation
```python
def validate_release_readiness():
    checks = [
        run_quality_gates(),
        verify_test_coverage(),
        check_documentation(),
        scan_security_vulnerabilities()
    ]
    return all(checks)
```

## 🔄 Rollback Procedures

### Automated Rollback

If release validation fails:

1. **Immediate Stop**: Halt release pipeline
2. **Revert Tag**: Remove problematic git tag
3. **PyPI Yank**: Mark PyPI package as yanked
4. **Notification**: Alert maintainers and users
5. **Investigation**: Root cause analysis

### Manual Rollback

```bash
# Remove problematic tag
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3

# Yank from PyPI (if already published)
twine yank markitdown-mcp==1.2.3

# Create hotfix if needed
git checkout -b hotfix/critical-fix
# ... make fixes ...
git commit -m "fix: resolve critical issue from v1.2.3"
```

## 📚 Version History

### Current Version Strategy

- **Stable**: v1.x.x series
- **LTS Support**: Last 2 major versions
- **Security Updates**: All supported versions
- **Breaking Changes**: Only in major versions

### Deprecation Policy

- **Feature Deprecation**: 2 minor versions notice
- **API Changes**: 1 major version migration period
- **Documentation**: Migration guides for all breaking changes
- **Timeline**: Minimum 6 months for major deprecations

## 📞 Support & Troubleshooting

### Release Issues

- **Failed Builds**: Check GitHub Actions logs
- **PyPI Errors**: Verify package metadata and credentials
- **Version Conflicts**: Ensure semantic versioning compliance
- **Documentation**: Update all version references

### Contact Information

- **Maintainers**: Create GitHub issue with `release` label
- **Security**: Use GitHub Security Advisories
- **Questions**: Discussion in GitHub Discussions
- **Emergency**: Create issue with `urgent` label

---

*This release process is designed to be fully automated while maintaining high quality standards. All changes to this process should be tested and validated before implementation.*