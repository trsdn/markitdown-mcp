# Release Process

This document outlines the release process for markitdown-mcp.

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
   - Tag the release: `git tag -a v1.0.0 -m "Release v1.0.0"`
   - Push tags: `git push origin --tags`

4. **Publish to PyPI**
   - Build: `python -m build`
   - Upload: `python -m twine upload dist/*`

## Automated Releases

GitHub Actions automatically publishes to PyPI when a new tag is pushed.