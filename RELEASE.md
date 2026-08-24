# Release Process

This document outlines the release process for `trsdn-markitdown-mcp`.

> **Naming**: the PyPI distribution is `trsdn-markitdown-mcp`. The Python import package
> stays `markitdown_mcp` and the CLI command stays `markitdown-mcp` (with a
> `trsdn-markitdown-mcp` alias). This project is **not** Microsoft's official
> `markitdown-mcp` package.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality additions
- PATCH version for backwards-compatible bug fixes

## Release Steps

1. **Update Version**
   - Update version in `pyproject.toml`
   - Update version in `markitdown_mcp/__init__.py`

2. **Update Changelog**
   - Add release notes to CHANGELOG.md
   - Include all changes, fixes, and new features

3. **Create Release**
   - Tag the release: `git tag -a v1.2.3 -m "Release v1.2.3"`
   - Push tags: `git push origin v1.2.3`

4. **Automated Publish**
   - `.github/workflows/release.yml` runs the full release chain:
     `validate-release` → `quality-gates` (ruff/mypy/pytest on Python 3.10/3.11/3.12
     plus MCP protocol validation) + `security-scan` (Bandit, dependency audit) →
     `build-package` (build, `twine check`, entrypoint smoke test) →
     `generate-changelog` → `publish` (PyPI) → `create-github-release` →
     `update-docs` → `post-release-validation`.
   - The GitHub release is created **after** the PyPI publish succeeds.

## PyPI Trusted Publishing (OIDC)

Releases are published with [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/).
**No API tokens or secrets are stored in this repository.**

The PyPI publisher configuration must match exactly:

| Setting | Value |
|---------|-------|
| PyPI project | `trsdn-markitdown-mcp` |
| Owner / repository | `trsdn/markitdown-mcp` |
| Workflow file | `release.yml` |
| Environment | `pypi` |

The `publish` job therefore declares `environment: pypi` and
`permissions: { id-token: write }`. `id-token: write` is granted **only** to that job;
the workflow-level default is `contents: read`, and `contents: write` is scoped to the
jobs that create the release and push the changelog. Changing the workflow filename, the
job's environment, or the repository slug will break OIDC authentication.

### Local dry run

```bash
python -m pip install --upgrade build twine
python -m build
twine check dist/*
```

Never run `twine upload` manually — publishing happens only through the tagged
release workflow.
