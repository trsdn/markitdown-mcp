# CI/CD Quick Reference

## 🚀 Workflow Quick Start

### For Developers

```bash
# Check your changes locally before pushing
ruff format .                    # Format code
ruff check .                     # Lint code
mypy markitdown_mcp             # Type check
pytest tests/unit/ -x           # Quick unit tests
pytest --cov=markitdown_mcp     # Full tests with coverage
```

### For Maintainers

```bash
# Trigger specific workflows manually
gh workflow run "Test Suite"
gh workflow run "Pre-Release Testing"
gh workflow run "Automated Version Bump"

# Check workflow status
gh run list --limit 10
gh run view <run-id>
gh run view <run-id> --log-failed

# Release management
git tag v1.2.3                  # Triggers release pipeline
gh release create v1.2.3        # Manual release creation
```

## 📊 Workflow Status

| Workflow | Purpose | Runtime | Frequency |
|----------|---------|---------|-----------|
| **Fast Tests** | Quick validation | ~2-3 min | Every PR/Push |
| **CI Quality Gates** | Code quality | ~3-5 min | Every PR/Push |
| **Test Suite** | Full validation | ~5-8 min | Every PR/Push |
| **Security** | Security scan | ~2-4 min | Every PR/Push |
| **Documentation** | Docs validation | ~2-3 min | Doc changes |
| **Version Bump** | Release prep | ~1-2 min | Push to main |
| **Release** | Package publish | ~5-10 min | Tag creation |

## 🔍 Quality Requirements

### Branch Protection (ENFORCED)
- ✅ **PR Review**: 1 approving review required
- ✅ **Status Checks**: All 4 required checks must pass
- ✅ **Code Owners**: Critical files need owner approval
- ✅ **No Force Push**: History protection enabled
- ✅ **Admin Rules**: Apply to all users including admins

### Code Quality
- ✅ **Format**: `ruff format` compliant
- ✅ **Lint**: `ruff check` passing
- ✅ **Types**: `mypy` validation
- ✅ **Coverage**: ≥80% test coverage
- ✅ **Security**: No high-severity issues

### Testing
- ✅ **Unit Tests**: All passing
- ✅ **Integration**: MCP protocol tests
- ✅ **Platform**: Ubuntu/Windows/macOS
- ✅ **Python**: 3.10, 3.11, 3.12, 3.13

### Documentation
- ✅ **Docstrings**: ≥80% coverage
- ✅ **Build**: Sphinx builds successfully
- ✅ **Links**: No broken links
- ✅ **Spelling**: Clean spell check

## 🚨 Troubleshooting

### Common Failures

| Issue | Quick Fix |
|-------|-----------|
| Format check fails | `ruff format .` |
| Lint errors | `ruff check . --fix` |
| Type errors | Add type annotations |
| Coverage too low | Add more tests |
| Import errors | Check dependencies |
| Timeout errors | Optimize slow tests |

### Workflow Commands

```bash
# Local validation (matches CI)
ruff format --check .
ruff check .
mypy markitdown_mcp
pytest tests/unit/ --cov=markitdown_mcp --cov-fail-under=80

# Security checks
bandit -r markitdown_mcp/
safety check

# Documentation
pydocstyle markitdown_mcp
sphinx-build -W docs/ _build/

# Performance testing
pytest tests/ --durations=10
```

## 🏷️ Release Process

### Conventional Commits
```bash
feat: add new conversion tool        # Minor release (1.X.0)
fix: resolve PDF parsing bug         # Patch release (1.0.X)
feat!: change MCP tool interface     # Major release (X.0.0)
docs: update installation guide      # No release
```

### Release Workflow
1. **Commits** → Version analysis
2. **PR Created** → Review & merge
3. **Tag Created** → Release pipeline
4. **GitHub Release** → PyPI publish

### Emergency Hotfix
```bash
git checkout -b hotfix/critical-bug
# Fix the issue
git commit -m "fix: critical security vulnerability"
# Create PR to main
# Normal release process applies
```

## 🔧 Configuration

### Environment Variables
```bash
# Local development
export MAX_FILE_SIZE_MB=100
export CONVERSION_TIMEOUT=60
export PYTHONPATH=$PWD

# CI/CD (set in GitHub secrets)
GITHUB_TOKEN=<token>
PYPI_API_TOKEN=<token>
CODECOV_TOKEN=<token>
```

### Key Files
- `pyproject.toml` - Project config & dependencies
- `pytest.ini` - Test configuration
- `.github/workflows/` - CI/CD definitions
- `scripts/analyze-version.py` - Version logic

## 📈 Metrics

### Success Targets
- **Build Success**: >95%
- **Test Coverage**: >80%
- **Build Time**: <10 minutes
- **Security Issues**: 0 high-severity

### Monitoring
- **GitHub Actions**: Workflow status
- **Codecov**: Coverage reports
- **Dependabot**: Dependency health
- **Security Advisories**: Vulnerability alerts

## 🛠️ Advanced Usage

### Matrix Testing
```yaml
# Custom test matrix
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
    os: [ubuntu-latest, windows-latest, macos-latest]
```

### Performance Testing
```bash
# Memory profiling
pytest tests/ --memprof

# Benchmark testing
pytest tests/performance/ --benchmark-only

# Load testing
pytest tests/load/ -n auto
```

### Security Scanning
```bash
# Full security audit
bandit -r markitdown_mcp/ -f json
safety check --json
semgrep --config=auto markitdown_mcp/
```

## 🔗 Useful Links

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Python Testing Best Practices](https://docs.pytest.org/)