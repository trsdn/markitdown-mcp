# Contributing to MarkItDown MCP Server

Thank you for your interest in contributing to the MarkItDown MCP Server! 🎉

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## 📜 Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful and constructive in all interactions.

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- Git
- Basic understanding of the Model Context Protocol (MCP)

### Fork the Repository
1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/markitdown-mcp.git
   cd markitdown-mcp
   ```

## 💻 Development Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation:**
   ```bash
   markitdown-mcp --help
   ```

## 🔧 Making Changes

### Branch Naming Convention
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test improvements
- `refactor/` - Code refactoring

Example: `feat/add-new-file-format` or `fix/mcp-protocol-error`

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes:**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
   ```bash
   # Test MCP server functionality
   python -c "
   import json
   import subprocess
   test_request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}
   proc = subprocess.run(['markitdown-mcp'], input=json.dumps(test_request), 
                        capture_output=True, text=True)
   print('✅ Server working' if proc.stdout else '❌ Server error')
   "
   ```

4. **Format code (if you have dev dependencies):**
   ```bash
   black markitdown_mcp/
   isort markitdown_mcp/
   ```

### Code Style Guidelines
- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### Adding New File Format Support
If you want to add support for a new file format:

1. Check if MarkItDown library already supports it
2. Update the `supported_extensions` set in `markitdown_mcp/server.py`
3. Add the format to the README documentation
4. Test with sample files
5. Update the format count in documentation if needed

## 📤 Submitting Pull Requests

### Before Submitting
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Tests pass locally
- [ ] Documentation updated if needed
- [ ] No merge conflicts with main branch

### PR Template
When creating a PR, please include:

1. **Description**: Clear description of what the PR does
2. **Type**: Feature, bug fix, documentation, etc.
3. **Testing**: How you tested the changes
4. **Screenshots**: If applicable (especially for documentation changes)
5. **Breaking Changes**: Any breaking changes and migration steps

### PR Review Process
1. Automated checks will run
2. Maintainer will review the code
3. Address any feedback
4. Once approved, PR will be merged

## 🚀 Release Process

### Conventional Commits

**All commits MUST follow conventional commit format** for automated version management:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

#### Commit Types

| Type | Description | Version Impact |
|------|-------------|----------------|
| `feat` | New feature | Minor (0.1.0) |
| `fix` | Bug fix | Patch (0.0.1) |
| `docs` | Documentation only | None |
| `style` | Code formatting | None |
| `refactor` | Code restructuring | None |
| `perf` | Performance improvement | Patch (0.0.1) |
| `test` | Testing changes | None |
| `chore` | Build/dependencies | None |
| `ci` | CI/CD changes | None |
| `BREAKING CHANGE` | Breaking API change | Major (1.0.0) |

#### Examples

```bash
# New feature (minor version bump)
feat(mcp): add support for PowerBI files

# Bug fix (patch version bump)
fix(security): resolve path traversal vulnerability

# Breaking change (major version bump)
feat(api): redesign tool interface

BREAKING CHANGE: tool parameters now require explicit types
```

### Automated Releases

Releases are **fully automated** based on conventional commits:

1. **Version Detection**: Commits since last release determine version bump
2. **Quality Gates**: All CI checks must pass before release
3. **Changelog**: Automatically generated from commit messages
4. **Publishing**: Package published to PyPI automatically
5. **GitHub Release**: Created with auto-generated release notes

### Contributing to Releases

#### For Feature Development

```bash
# 1. Create feature branch
git checkout -b feat/new-file-format

# 2. Make changes with proper commits
git commit -m "feat(converter): add support for Pages files"
git commit -m "test(converter): add Pages file test cases"
git commit -m "docs(readme): update supported formats list"

# 3. Create PR with conventional title
# PR Title: "feat(converter): add support for Pages files"
```

#### For Bug Fixes

```bash
# 1. Create fix branch
git checkout -b fix/memory-leak

# 2. Make fix with proper commit
git commit -m "fix(memory): resolve memory leak in large file processing"

# 3. Create PR
# PR Title: "fix(memory): resolve memory leak in large file processing"
```

#### For Breaking Changes

**Breaking changes require special attention:**

```bash
# Commit message must include BREAKING CHANGE footer
git commit -m "feat(api): redesign tool response format

BREAKING CHANGE: tool responses now return structured data with metadata instead of plain text"
```

### Release Timeline

- **Patch Releases**: Automated when bug fixes are merged
- **Minor Releases**: Automated when new features are merged
- **Major Releases**: Automated when breaking changes are merged
- **Security Releases**: Emergency releases within 24 hours

### Release Quality Requirements

Before any release, automated systems verify:

- [ ] All tests pass on supported Python versions (3.10, 3.11, 3.12)
- [ ] Code formatting and linting pass (ruff)
- [ ] Type checking passes (mypy)
- [ ] Test coverage maintains minimum threshold (80%)
- [ ] Security scans pass (no high/critical vulnerabilities)
- [ ] MCP protocol compliance verified
- [ ] Documentation builds successfully

### Manual Release Override

For emergency situations, maintainers can create manual releases:

```bash
# 1. Ensure quality gates pass
ruff format --check && ruff check && mypy markitdown_mcp/

# 2. Update version in pyproject.toml
# 3. Update CHANGELOG.md
# 4. Create and push tag
git tag v1.2.3
git push origin v1.2.3
```

### Release Communication

Contributors will be notified of releases through:
- **GitHub Releases**: Automated release notes
- **PyPI**: Package updates
- **Changelog**: Updated CHANGELOG.md file
- **Issues**: Automatic closure of fixed issues

For detailed release procedures, see the RELEASE.md file in the repository root.

## 🐛 Reporting Issues

### Bug Reports
When reporting bugs, please include:
- **Environment**: OS, Python version, package version
- **Steps to reproduce**: Detailed steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Full error output
- **Sample files**: If related to specific file types (redact sensitive data)

### Use this template:
```markdown
**Environment:**
- OS: [e.g., macOS 13.0, Windows 11, Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Package version: [e.g., 1.0.0]
- MCP Client: [e.g., Claude Desktop 0.4.1]

**Bug Description:**
A clear description of the bug.

**Steps to Reproduce:**
1. Install package...
2. Run command...
3. Error occurs...

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Error Output:**
```
Paste error messages here
```

**Sample Files:**
If applicable, attach sample files that cause the issue.
```

## 💡 Feature Requests

We welcome feature requests! Please:
1. Check existing issues to avoid duplicates
2. Clearly describe the use case
3. Explain why this feature would benefit MCP users
4. Consider implementation complexity

### Feature Request Template:
```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Use Case**
How would this feature benefit MCP users?

**Additional context**
Any other context about the feature request.
```

## 🏷️ Labels

We use these labels to organize issues and PRs:
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `mcp-protocol` - Related to MCP protocol
- `file-format` - New file format support
- `performance` - Performance improvements

## 🎖️ Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Special thanks in documentation

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: We're happy to help review code before you submit

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to MarkItDown MCP Server! 🚀