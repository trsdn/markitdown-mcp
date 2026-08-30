# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.3] - 2026-08-30

### 🐛 Bug Fixes
- restore the workflow_dispatch re-run path in the release pipeline (#54)



### Fixed
- Release workflow: `publish`, `create-github-release` and `post-release-validation` no
  longer require `github.ref` to be a tag. `workflow_dispatch` takes a required `tag`
  input and every job checks that tag out, so a dispatch is a re-run of the pipeline for
  an existing tag; on a dispatch `github.ref` is `refs/heads/main`, so the guard was
  always false and silently skipped the upload while the run still reported success.
  Duplicate uploads remain prevented by the existing "Check if tag already exists in
  releases" step in `validate-release`.
- CI: removed the `paths:` filter from the `pull_request` trigger of `ci-gates.yml` and
  `fast-tests.yml`. These workflows provide the required status checks `Unit Tests &
  Coverage`, `Integration Smoke Tests` and `Quick Security Scan`; with a path filter they
  never ran on PRs without matching files (docs- or YAML-only, e.g. the automated
  `docs/changelog-v*` release PRs), so those checks never reported and the PRs stayed
  blocked indefinitely.
- Release workflow: `post-release-validation` now sets `GH_REPO` for the step, so `gh`
  resolves the repository in a job without a checkout instead of failing the check with
  "GitHub release missing".
- Release workflow: the PyPI verification uses the PyPI JSON API with retries instead of
  the experimental `pip index versions` plus a substring `grep`.
- Release workflow: `update-docs` opens a pull request with the changelog update instead of
  pushing directly to the protected `main` branch (GH006).

### Changed
- **Renamed the PyPI distribution to `trsdn-markitdown-mcp`** (the name `markitdown-mcp`
  is taken by Microsoft's official project). The import package (`markitdown_mcp`) and the
  `markitdown-mcp` console command are unchanged.
- Release workflow now publishes via PyPI Trusted Publishing (OIDC, `environment: pypi`)
  instead of API tokens.
- `MANIFEST.in` prunes tests, docs, examples, scripts and schemas from the published
  sdist.

### Added
- `trsdn-markitdown-mcp` console-script alias and `python -m markitdown_mcp` support.
- Packaging metadata: SPDX `license`, `license-files`, maintainers, extra classifiers,
  keywords and project URLs.

## [1.2.2] - 2026-06-10

### Fixed
- Resolve MCP protocol and file validation issues (#44)

### Performance
- Remove artificial path validation delay (#43)

## [] - $(date +%Y-%m-%d)

### Added
- Comprehensive security scanning infrastructure
  - GitLeaks credential scanning
  - Bandit Python security analysis
  - Safety dependency vulnerability scanning
  - CodeQL analysis with security-focused queries
  - Dependency review for pull requests
- MCP protocol compliance testing
  - Protocol smoke tests for initialization and tool discovery
  - Wire protocol compliance via subprocess testing
  - Schema validation for tools and responses
  - Tool calling verification with real examples
- Repository structure improvements
  - Organized documentation in `docs/` directory
  - Utility scripts moved to `scripts/` directory
  - MCP configuration examples in `examples/` directory
  - Comprehensive `.gitignore` with security patterns
- Performance test enhancements
  - Fixed large file size calculation in test generators
  - Improved file generation buffers for consistent test sizes

### Changed
- Moved documentation files to organized structure
  - `CONTRIBUTING.md` → `docs/CONTRIBUTING.md`
  - `TESTING_STRATEGY.md` → `docs/TESTING_STRATEGY.md`
  - `KNOWN_ISSUES.md` → `docs/KNOWN_ISSUES.md`
- Moved utility scripts to `scripts/` directory
  - `install-all-deps.sh` → `scripts/install-all-deps.sh`
  - `run_server.py` → `scripts/run_server.py`

### Fixed
- Memory cleanup assertion in performance tests
- Large CSV file test size calculation (now properly generates 8MB+ files)
- Code formatting applied across all test files using Black

### Security
- Added GitLeaks scanning to prevent credential leaks
- Implemented comprehensive security workflow for CI/CD
- Added dependency vulnerability scanning
- Enhanced code security analysis with multiple tools

## [1.0.0] - 2024-09-XX

### Added
- Initial release of MarkItDown MCP Server
- Support for converting documents to markdown format
- Three main tools:
  - `convert_file`: Convert individual files to markdown
  - `convert_directory`: Batch convert directories
  - `list_supported_formats`: List supported file formats
- Support for multiple file formats:
  - PDF documents (with optional dependencies)
  - Microsoft Office documents (Word, Excel, PowerPoint)
  - HTML and XML files
  - CSV and JSON data files
  - Plain text and markdown files
- Base64 content processing support
- Path traversal protection and security measures
- Comprehensive test suite:
  - Unit tests for all tools
  - Integration tests for MCP protocol
  - Performance tests for large files
  - Security tests for malicious content
  - Compatibility tests across Python versions
- Memory usage optimization and leak detection
- Concurrent processing support with rate limiting
- Extensive documentation and examples

### Security
- Path traversal attack prevention
- Safe directory restrictions
- Temporary file cleanup mechanisms
- DoS protection with request rate limiting
- Malicious file detection and handling

---

## Release Notes

### Version Numbering
This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backward-compatible functionality additions
- **PATCH** version for backward-compatible bug fixes

### Security Updates
Security vulnerabilities will be documented in this changelog and addressed in patch releases when possible. Critical security issues may require immediate major or minor version bumps.

### Deprecated Features
Deprecated features will be marked in the changelog and removed in the next major version. Users will have at least one major version cycle to migrate.

### Breaking Changes
Breaking changes will be clearly marked and include migration instructions where applicable.