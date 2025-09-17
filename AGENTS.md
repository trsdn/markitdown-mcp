# AI Agents Integration Guide

This guide provides comprehensive information for AI agents and assistants on how to effectively use the MarkItDown MCP server for document conversion tasks.

## 🤖 Quick Reference for AI Agents

### Primary Use Cases
- Convert documents (PDF, Word, Excel, PowerPoint) to markdown
- Extract readable text from various file formats
- Batch process directories of documents
- Support users with document analysis workflows

### Available Tools
1. **`convert_file`** - Convert individual files
2. **`convert_directory`** - Batch convert directories
3. **`list_supported_formats`** - Show supported formats

## 🛠️ Tool Usage Guide

### `convert_file` Tool

**When to use:**
- User provides a file path for conversion
- User shares base64 content that needs conversion
- Single document analysis required

**Parameters:**
```json
{
  "file_path": "/path/to/document.pdf",     // For local files
  "file_content": "base64encoded...",      // For shared content
  "filename": "document.pdf"               // Required with file_content
}
```

**Example scenarios:**
- "Convert this PDF to markdown"
- "Extract text from this Word document"
- "Make this Excel file readable"

### `convert_directory` Tool

**When to use:**
- User wants to process multiple files
- Batch conversion workflows
- Directory cleanup/organization tasks

**Parameters:**
```json
{
  "input_directory": "/path/to/input",
  "output_directory": "/path/to/output"    // Optional
}
```

**Example scenarios:**
- "Convert all documents in this folder"
- "Process my downloads directory"
- "Batch convert these reports"

### `list_supported_formats` Tool

**When to use:**
- User asks about supported file types
- Error troubleshooting (unsupported format)
- Capability discovery

**Parameters:** None

**Example scenarios:**
- "What file types can you convert?"
- "Can you handle PowerPoint files?"
- "Is Excel supported?"

## 💡 Best Practices for AI Agents

### 1. Format Detection
```python
# Always check format support first if unsure
if user_asks_about_unknown_format:
    call_tool("list_supported_formats")
```

### 2. Error Handling
- Check file paths exist before conversion
- Validate base64 content before processing
- Provide helpful error explanations to users

### 3. File Size Awareness
- Warn users about large files (>50MB may be slow)
- Suggest breaking up large directories
- Monitor conversion time for user experience

### 4. Security Considerations
- Never process files outside safe directories
- Validate file paths for security
- Be cautious with user-provided paths

## 🔧 Common Integration Patterns

### Pattern 1: Document Analysis Workflow
```python
def analyze_document(file_path):
    # Step 1: Convert to markdown
    result = convert_file(file_path=file_path)

    # Step 2: Extract and analyze content
    markdown_content = result['content'][0]['text']

    # Step 3: Provide analysis to user
    return analyze_markdown(markdown_content)
```

### Pattern 2: Batch Processing
```python
def process_document_folder(input_dir, output_dir):
    # Convert entire directory
    result = convert_directory(
        input_directory=input_dir,
        output_directory=output_dir
    )

    # Report results to user
    return summarize_conversion_results(result)
```

### Pattern 3: Format Validation
```python
def validate_and_convert(file_path):
    # Check if format is supported
    formats = list_supported_formats()

    # Extract file extension
    file_ext = get_extension(file_path)

    if file_ext in supported_formats:
        return convert_file(file_path=file_path)
    else:
        return suggest_alternative_formats()
```

## 🎯 User Experience Guidelines

### Helpful Responses
- **Good**: "I'll convert your PDF to markdown so we can analyze the content..."
- **Better**: "Converting your 15-page PDF report to markdown format for analysis. This may take a moment..."

### Error Handling
- **Good**: "The file couldn't be converted."
- **Better**: "This file format isn't supported. I can convert PDF, Word, Excel, and PowerPoint files. Would you like me to show all supported formats?"

### Progress Communication
- **Large files**: "Processing your 45MB document, this may take 30-60 seconds..."
- **Directories**: "Converting 23 files in your directory, processing in batches..."

## 🚨 Common Pitfalls to Avoid

### ❌ Don't Do This
```python
# Don't assume all files can be converted
convert_file(mystery_file_path)

# Don't ignore errors
result = convert_file(file_path)
# ... proceed without checking if conversion succeeded

# Don't process unsafe paths
convert_file("/etc/passwd")
```

### ✅ Do This Instead
```python
# Check format support first
formats = list_supported_formats()
if is_supported(file_path, formats):
    result = convert_file(file_path)
    if result.get('error'):
        handle_conversion_error(result['error'])
    else:
        process_markdown(result['content'])
```

## 🔍 Troubleshooting Guide

### Common Issues

| Issue | Cause | Solution |
|-------|--------|----------|
| "File not found" | Invalid path | Verify file exists and path is correct |
| "Permission denied" | File access rights | Check file permissions or use different file |
| "Unsupported format" | File type not supported | Use `list_supported_formats` to check alternatives |
| "Conversion failed" | File corrupted/encrypted | Try different file or check file integrity |

### Performance Issues
- **Slow conversion**: Normal for large files, inform user
- **Memory errors**: File too large, suggest breaking into smaller parts
- **Timeout**: Increase patience, very large files can take minutes

## 📊 Supported Formats Reference

### Documents
- **PDF**: `.pdf` (requires markitdown[pdf] dependencies)
- **Word**: `.docx`, `.doc`
- **PowerPoint**: `.pptx`, `.ppt`
- **Excel**: `.xlsx`, `.xls`

### Web & Markup
- **HTML**: `.html`, `.htm`
- **XML**: `.xml`
- **Markdown**: `.md`, `.markdown`

### Data
- **CSV**: `.csv`
- **JSON**: `.json`
- **Text**: `.txt`

### Usage Notes
- PDF conversion requires additional dependencies
- Office formats work best with newer file versions
- Large Excel files may have content limits

## 🔒 Security Features

### Path Protection
- Server only operates in configured safe directories
- Path traversal attacks are prevented
- Temporary files are automatically cleaned up

### Content Safety
- Base64 content is processed in secure temporary files
- No permanent storage of user content
- Memory is efficiently managed and cleaned

### Usage Limits
- File size limits prevent resource exhaustion
- Request rate limiting protects against DoS
- Timeout protections prevent hanging processes

## 📈 Performance Optimization

### For AI Agents
- Cache format lists to reduce API calls
- Batch similar operations when possible
- Provide progress feedback for long operations
- Handle errors gracefully with helpful messages

### For Users
- Process smaller files first for faster feedback
- Use specific output directories for organization
- Consider file size when setting expectations

## 🤝 Integration Examples

### Claude Code Integration
```json
{
  "mcpServers": {
    "markitdown": {
      "command": "markitdown-mcp",
      "description": "Convert documents to markdown for analysis"
    }
  }
}
```

### Custom Agent Integration
```python
class DocumentConverter:
    def __init__(self, mcp_client):
        self.mcp = mcp_client

    async def convert_and_analyze(self, file_path):
        # Convert document
        result = await self.mcp.call_tool(
            "convert_file",
            {"file_path": file_path}
        )

        # Extract content
        markdown = result['content'][0]['text']

        # Perform analysis
        return self.analyze_content(markdown)
```

## 🚀 Release Management for AI Agents

AI agents and development tools should follow these guidelines when contributing to releases:

### Conventional Commits

**ALWAYS** use conventional commit format for automated version management:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

#### Commit Types for AI Agents

| Type | When to Use | Version Impact |
|------|-------------|----------------|
| `feat` | Adding new MCP tools or major functionality | Minor (0.1.0) |
| `fix` | Bug fixes, security patches | Patch (0.0.1) |
| `docs` | Documentation updates, AI agent guides | None |
| `refactor` | Code improvements without functionality change | None |
| `perf` | Performance optimizations | Patch (0.0.1) |
| `test` | Test additions or improvements | None |
| `chore` | Dependencies, build configuration | None |
| `BREAKING CHANGE` | API changes that break compatibility | Major (1.0.0) |

#### AI Commit Examples

```bash
# When adding new functionality
feat(mcp): add support for Excel chart extraction

# When fixing bugs
fix(security): resolve path traversal in file validation

# When improving performance
perf(conversion): optimize large PDF processing

# When making breaking changes
feat(api): redesign tool response format

BREAKING CHANGE: tool responses now return structured data instead of plain text
```

### AI-Driven Version Detection

AI agents should analyze commit history to determine appropriate version bumps:

```python
def analyze_version_impact(commits_since_last_release):
    """
    Analyze commits to determine semantic version bump needed.

    Returns: 'major', 'minor', 'patch', or 'none'
    """
    has_breaking = any('BREAKING CHANGE' in commit.body for commit in commits)
    has_features = any(commit.type == 'feat' for commit in commits)
    has_fixes = any(commit.type in ['fix', 'perf'] for commit in commits)

    if has_breaking:
        return 'major'
    elif has_features:
        return 'minor'
    elif has_fixes:
        return 'patch'
    else:
        return 'none'
```

### Release Readiness Validation

Before suggesting releases, AI agents should verify:

```python
def validate_release_readiness():
    """Check if codebase is ready for release."""
    checks = {
        'format_check': run_ruff_format(),
        'lint_check': run_ruff_lint(),
        'type_check': run_mypy(),
        'tests_pass': run_test_suite(),
        'coverage_ok': check_coverage_threshold(),
        'docs_updated': verify_documentation(),
        'security_clean': run_security_scan()
    }

    failed_checks = [name for name, passed in checks.items() if not passed]

    if failed_checks:
        return False, f"Failed checks: {', '.join(failed_checks)}"
    return True, "All checks passed"
```

### Automated Changelog Generation

AI agents can generate changelog entries from commits:

```python
def generate_changelog_entry(commits, version):
    """Generate changelog section from conventional commits."""
    changelog = f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n"

    # Group commits by type
    features = [c for c in commits if c.type == 'feat']
    fixes = [c for c in commits if c.type == 'fix']
    breaking = [c for c in commits if 'BREAKING CHANGE' in c.body]

    if breaking:
        changelog += "### ⚠️ BREAKING CHANGES\n"
        for commit in breaking:
            changelog += f"- {commit.description}\n"
        changelog += "\n"

    if features:
        changelog += "### ✨ Features\n"
        for commit in features:
            changelog += f"- {commit.description}\n"
        changelog += "\n"

    if fixes:
        changelog += "### 🐛 Bug Fixes\n"
        for commit in fixes:
            changelog += f"- {commit.description}\n"
        changelog += "\n"

    return changelog
```

### AI Release Workflow Integration

When AI agents detect release-worthy changes:

1. **Analyze Commits**: Parse conventional commits since last release
2. **Determine Version**: Calculate semantic version bump
3. **Validate Quality**: Ensure all quality gates pass
4. **Generate Changelog**: Create changelog entry from commits
5. **Suggest Release**: Propose release with rationale

```python
async def suggest_release_if_needed():
    """AI agent workflow for release detection."""

    # Get commits since last release
    last_tag = get_latest_git_tag()
    commits = get_commits_since(last_tag)

    # Analyze version impact
    version_impact = analyze_version_impact(commits)

    if version_impact == 'none':
        return "No release needed - no significant changes"

    # Validate readiness
    ready, message = validate_release_readiness()
    if not ready:
        return f"Not ready for release: {message}"

    # Calculate new version
    current_version = parse_version(last_tag)
    new_version = bump_version(current_version, version_impact)

    # Generate changelog
    changelog = generate_changelog_entry(commits, new_version)

    return {
        'action': 'suggest_release',
        'version': new_version,
        'changelog': changelog,
        'commits_included': len(commits),
        'impact': version_impact
    }
```

### Release Communication

AI agents should communicate release information clearly:

```python
def format_release_summary(release_info):
    """Format release information for users."""
    return f"""
🚀 **Release Suggestion: v{release_info['version']}**

**Impact**: {release_info['impact'].title()} version bump
**Changes**: {release_info['commits_included']} commits included
**Type**: {'🔥 Breaking changes' if release_info['impact'] == 'major' else '✨ New features' if release_info['impact'] == 'minor' else '🐛 Bug fixes'}

**Changelog Preview**:
{release_info['changelog'][:500]}...

**Next Steps**:
1. Review the proposed changes
2. Run final quality checks
3. Create release tag: `git tag v{release_info['version']}`
4. Push tag to trigger automated release: `git push origin v{release_info['version']}`
"""
```

### Emergency Release Handling

For critical security issues, AI agents should:

1. **Identify Severity**: Recognize security-related commits
2. **Fast-Track Process**: Bypass normal review for critical fixes
3. **Immediate Notification**: Alert maintainers of urgent release need
4. **Hotfix Branch**: Suggest hotfix branch workflow

```python
def detect_emergency_release(commits):
    """Detect if commits contain critical security fixes."""
    security_keywords = ['security', 'vulnerability', 'cve', 'exploit', 'xss', 'injection']

    for commit in commits:
        commit_text = f"{commit.description} {commit.body}".lower()
        if any(keyword in commit_text for keyword in security_keywords):
            return True, "Security vulnerability detected - emergency release recommended"

    return False, "No critical security issues detected"
```

## 🔧 CI/CD Maintenance Process

### For AI Agents Working with CI/CD

**CRITICAL**: CI/CD workflow changes require special handling to avoid infinite loops where workflows validate themselves.

### Branch Strategy for Different Types of Changes

**Use `ci-cd-maintenance` branch for:**
- GitHub Actions workflows (`.github/workflows/*.yml`)
- CI/CD configuration files
- Infrastructure-as-code files
- Security-sensitive automation
- Scripts used by workflows (e.g., `scripts/analyze-version.py`)

**Use feature/fix branches for:**
- Application code changes (e.g., `markitdown_mcp/server.py`)
- Test files (e.g., `tests/unit/*.py`)
- Documentation updates
- Configuration files that don't affect CI/CD

**Rule of thumb**: If the change affects how CI/CD workflows run or could create validation loops, use `ci-cd-maintenance`. If it's regular code that gets validated by CI/CD, use a normal feature branch.

### When to Use CI/CD Maintenance Process

Use the `ci-cd-maintenance` branch and process when making changes to:
- GitHub Actions workflows (`.github/workflows/*.yml`)
- CI/CD configuration files
- Infrastructure-as-code files
- Security-sensitive automation
- Version analysis scripts (`scripts/analyze-version.py`)
- Workflow dependencies and tools

### CI/CD Maintenance Workflow

```python
async def update_cicd_infrastructure(changes_description):
    """AI agent workflow for CI/CD changes."""

    # 1. Create ci-cd-maintenance branch
    await run_command("git checkout -b ci-cd-maintenance")

    # 2. Make CI/CD changes
    # ... implement changes ...

    # 3. Commit changes with clear description
    commit_message = f"ci: {changes_description}\n\nRequires manual review and merge"
    await run_command(f"git commit -m '{commit_message}'")

    # 4. Push to trigger CI/CD maintenance workflow
    await run_command("git push origin ci-cd-maintenance")

    # 5. Wait for validation
    validation_result = await wait_for_workflow("ci-cd-maintenance.yml")

    # 6. Create merge instructions
    return generate_merge_instructions(validation_result)

def generate_merge_instructions(validation_result):
    """Generate clear instructions for manual merge."""
    return f"""
🔧 **CI/CD Maintenance Ready for Review**

**Validation Status**: {validation_result.status}
**Security Check**: {validation_result.security_status}

**Manual Review Required**:
1. Review workflow changes carefully
2. Check for security implications
3. Verify no circular dependencies
4. Test rollback plan if needed

**To merge**:
```bash
git checkout main
git merge ci-cd-maintenance
git push origin main
git branch -d ci-cd-maintenance
```

**Rollback plan** (if issues found after merge):
```bash
git revert <merge-commit-hash>
git push origin main
```
"""
```

### Security Considerations for CI/CD Changes

AI agents must be extra careful with CI/CD changes:

```python
def validate_cicd_security(workflow_content):
    """Security validation for workflow changes."""

    security_issues = []

    # Check for shell injection risks
    if re.search(r'run:.*\$\{\{(?!github\.|inputs\.|secrets\.)', workflow_content):
        security_issues.append("Potential shell injection with user input")

    # Check for dangerous pull_request_target usage
    if 'pull_request_target' in workflow_content and 'actions/checkout' in workflow_content:
        security_issues.append("pull_request_target with checkout - verify safety")

    # Check for secret exposure
    if re.search(r'echo.*\$\{\{.*secrets\.', workflow_content):
        security_issues.append("Potential secret exposure in echo statement")

    return security_issues

def safe_workflow_update(file_path, new_content):
    """Safely update workflow files with validation."""

    # Validate YAML syntax
    try:
        yaml.safe_load(new_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {e}")

    # Security validation
    security_issues = validate_cicd_security(new_content)
    if security_issues:
        raise SecurityError(f"Security issues found: {security_issues}")

    # Write file
    with open(file_path, 'w') as f:
        f.write(new_content)

    return f"Safely updated {file_path}"
```

### Common CI/CD Patterns for AI Agents

**Adding new workflow**:
```python
def create_new_workflow(name, triggers, jobs):
    """Template for creating new GitHub Actions workflows."""

    workflow = {
        'name': name,
        'on': triggers,
        'permissions': {
            'contents': 'read',
            'pull-requests': 'write'
        },
        'jobs': jobs
    }

    # Validate before writing
    yaml_content = yaml.dump(workflow, default_flow_style=False)
    return safe_workflow_update(f'.github/workflows/{name.lower()}.yml', yaml_content)
```

**Updating existing workflow**:
```python
def update_workflow_safely(file_path, updates):
    """Safely update existing workflow with changes."""

    # Read current workflow
    with open(file_path, 'r') as f:
        workflow = yaml.safe_load(f)

    # Apply updates
    for key, value in updates.items():
        workflow[key] = value

    # Convert back to YAML and validate
    yaml_content = yaml.dump(workflow, default_flow_style=False)
    return safe_workflow_update(file_path, yaml_content)
```

### Emergency CI/CD Fixes

For broken CI that blocks development:

1. **Create hotfix branch**: `ci-cd-hotfix-{issue}`
2. **Minimal fix**: Only change what's necessary
3. **Fast-track review**: Ping maintainer for immediate merge
4. **Monitor closely**: Watch for issues after merge

```python
def emergency_cicd_fix(issue_description, fix_changes):
    """Handle emergency CI/CD fixes."""

    branch_name = f"ci-cd-hotfix-{issue_description.replace(' ', '-')}"

    return f"""
🚨 **EMERGENCY CI/CD FIX REQUIRED**

**Issue**: {issue_description}
**Branch**: {branch_name}
**Changes**: {fix_changes}

**URGENT**: This fix is needed to unblock development.
Please review and merge immediately.

**Risk Assessment**: [Explain why this is safe to merge quickly]
**Testing**: [Describe how the fix was validated]
"""
```

### Best Practices for AI Agents

1. **Always use ci-cd-maintenance branch** for workflow changes
2. **Never auto-merge CI/CD changes** - always require manual review
3. **Validate thoroughly** before pushing changes
4. **Provide clear review instructions** for humans
5. **Plan rollback strategy** before making changes
6. **Monitor CI health** after changes are merged

## 📚 Additional Resources

- **[Release Process Guide](RELEASE.md)** - Complete release documentation
- **[API Documentation](docs/api/)** - Technical specifications
- **[Configuration Examples](examples/)** - MCP client configurations
- **[Testing Guide](docs/development/TESTING_STRATEGY.md)** - Testing approach
- **[Known Issues](docs/guides/KNOWN_ISSUES.md)** - Common problems and solutions

---

*This guide is maintained for AI agents and assistants using the MarkItDown MCP server. For human developers, see the main [README.md](README.md) and [development documentation](docs/development/).*