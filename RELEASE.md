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
   - `.github/workflows/release.yml` builds the sdist + wheel, runs `twine check`,
     smoke-tests the wheel, and publishes to PyPI.

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
`permissions: { id-token: write }`. Changing the workflow filename, the job's
environment, or the repository slug will break OIDC authentication.

### Local dry run

```bash
python -m pip install --upgrade build twine
python -m build
twine check dist/*
```

Never run `twine upload` manually — publishing happens only through the tagged
release workflow.
