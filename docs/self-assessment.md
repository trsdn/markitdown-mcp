# Self-assessment

Assessed on 2026-09-21 against
[Repository Quality Standard 1.18.1](https://github.com/trsdn/.github/blob/v1.18.1/docs/repository-quality-standard.md)
by an AI agent (Claude), with no maintainer involved. The machine-readable result is
[`.github/conformance.yml`](../.github/conformance.yml); this file is the evidence behind it.

- Profiles: Baseline, Public, Software, Package. Not Deployable (row "an application or tool that users download or
  install", a CLI installed from PyPI and started by an MCP client), not Documentation, not Published Site, not Archived.
- State: **Needs work**. Two criteria fail (`R07`, `I04`), neither is critical.
- Read: the tree at `main` after pull requests #63 and #64, `gh api` settings and alert endpoints, the workflow runs,
  the v2.0.0 release and the `pyproject.toml` it was built from. Run: `ruff format --check .`, `ruff check .`,
  `mypy markitdown_mcp/` and `pytest tests/unit/` (109 passed) from a fresh virtual environment.
- Not done: the v2.0.0 wheel was not downloaded or installed; `I01` to `I03` are read from `pyproject.toml`, which
  builds it. Judgement words follow the readings the standard gives, applied as a small single-maintainer project.

## Baseline

| ID | Result | Evidence |
|---|---|---|
| `B01` | pass | The description says what the repository is: an MCP server converting many formats to Markdown |
| `B02` | pass | `README.md` has purpose, audience, status ("Project facts"), install and usage, and links to docs, issues and licence |
| `B03` | pass | `LICENSE` is MIT |
| `B04` | pass | No credential or local state is tracked; `.env.example` is a placeholder; `.gitignore` covers Python output. `schemas/` is committed generated output with its command in `AGENTS.md` |
| `B05` | pass | The command in `AGENTS.md` ("Validate before proposing a change") was run from a clean virtual environment and passed |
| `B06` | pass | Merge policy: branch protection requires a pull request. Alerts: none open in the Dependabot and secret scanning sources; the code scanning alerts open are `warning` or `high`, none `critical` |
| `B07` | pass | `pyproject.toml` declares dependencies and `requires-python >=3.10` |
| `B08` | pass | The v2.0.0 release has notes; `CHANGELOG.md` has an `[Unreleased]` section. See `R07` for the mismatch |
| `B09` | pass | Public, agrees with the open-source README; topics set; no homepage and the README names no site; not archived |
| `B10` | pass | Status and owner in "Project facts"; the owner is the account that owns the repository; `CODEOWNERS` exists |
| `B11` | pass | `.github/conformance.yml` |
| `B12` | pass | The `trsdn-standard` topic is set |
| `B13` | partial | The validation command appears in `CONTRIBUTING.md` (quality gates) and in `AGENTS.md`; the copies agree. Python 3.10 appears in the README and `pyproject.toml` and agrees |
| `B14` | pass | `AGENTS.md`, "Credentials": trusted publishing (no token), `GITHUB_TOKEN`, optional `GITLEAKS_LICENSE`, and who replaces each |
| `B15` | pass | "Project facts" states that no third-party code is redistributed and that the installer resolves dependencies |
| `B16` | pass | Branch protection blocks force pushes and deletion on `main` |

## Public

| ID | Result | Evidence |
|---|---|---|
| `P01` | pass | GitHub detects `MIT` |
| `P02` | pass | Community profile is 100%: contributing guide and code of conduct, in the repository or inherited |
| `P03` | pass | Private vulnerability reporting is enabled and the policy is inherited |
| `P04` | pass | Three issue forms and a pull-request template |
| `P05` | pass | README covers install, configuration (`.env`), examples, requirements, security (link to the policy) and support status (issues, "Project facts") |
| `P06` | pass | Community profile recognises README, licence, contributing guide and code of conduct |
| `P07` | pass | Description, 15 topics, no site so no homepage is required |
| `P08` | pass | Badge block in the convention's order: licence and Python version (both derived by a service), CI (first-party, `ci-gates.yml`), PyPI release, conformance (committed, checked by the `Conformance` workflow). The MCP badge is extra: it names the protocol the project implements |
| `P09` | pass | `stats.yml` calls the shared workflow daily, light and dark cards on the `stats` branch, no external references, shown in the README with `<picture>` |
| `P10` | pass | `bug_report.yml` asks for environment, description, steps, expected and actual result |
| `P11` | pass | The pull-request template asks for the change, tests, breaking changes and related issues |
| `P12` | pass | Dependabot alerts and security updates are enabled |
| `P13` | pass | Default setup is `not-configured`, so the repository's own `codeql.yml` (shared workflow, `actions` and `python`) is the scanner and its runs succeed. The older CodeQL job in `security.yml` sits in a workflow that is disabled |

## Software

| ID | Result | Evidence |
|---|---|---|
| `S01` | pass | Dependencies are declared with lower bounds in `pyproject.toml`, a library without a lockfile meets the pinning part; setup commands are documented |
| `S02` | pass | 109 unit tests plus integration and security suites; the main entry point and failure paths (rejected paths, invalid input) are exercised; the run is green |
| `S03` | partial | Format and lint (`ruff`) and static analysis (`bandit`) run in CI. The type check (`mypy`) runs in CI with failures ignored, so it cannot fail; it passes locally |
| `S04` | pass | The README and manifest claim Python 3.10 or later; `test.yml` runs 3.10 to 3.13 |
| `S05` | pass | GitHub secret scanning and push protection are enabled, and `secret-scan.yml` scans history on push and pull request; the scan found nothing |
| `S06` | pass | Configuration is read from the environment (`MARKITDOWN_SAFE_DIRS`, `.env`) with a committed example; no credential default. Read `server.py`; not every file |
| `S07` | pass | Errors name the operation and cause; the log lines read do not log credentials or content. The startup log prints the allowed directory paths |
| `S08` | pass | `dependabot.yml` covers `pip` and `github-actions` |
| `S09` | pass | Branch protection requires four checks; all four now report on pull requests (#64 restored two) |
| `S10` | pass | The README's "How It Works" and directory structure describe the single component; no cross-file constraint found |
| `S11` | pass | Every workflow declares `permissions` (`assess.py` reads all 19) |
| `S12` | pass | `assess.py` reports no movable reference in a job that holds a secret or can write; outside actions there are SHA-pinned |
| `S13` | pass | `pr-summary.yml` uses `workflow_run` and reads no repository secret |

## Deployable

| ID | Result | Evidence |
|---|---|---|
| `D01` | na | Not a standing deployment: a CLI installed from PyPI and started by an MCP client. Looked for a service, container, scheduled job or launch agent and found none |
| `D02` | na | Not a standing deployment, as `D01` |
| `D03` | na | Not a standing deployment, as `D01` |
| `D04` | na | Not a standing deployment, as `D01` |
| `D05` | na | Not a standing deployment, as `D01` |
| `D06` | na | Not a standing deployment, as `D01` |

## Package and release

| ID | Result | Evidence |
|---|---|---|
| `R01` | pass | `pyproject.toml` holds name, version, description, licence and repository URLs; they agree with GitHub |
| `R02` | pass | `CHANGELOG.md` names SemVer at its head |
| `R03` | pass | The tag `v2.0.0` triggers `release.yml`, which builds and publishes from it |
| `R04` | pass | Tag `v2.0.0`, `pyproject.toml` at that tag `2.0.0`, title "Release 2.0.0" |
| `R05` | partial | `release.yml` has a `post-release-validation` job that checks the release and the PyPI listing, but it does not install the published wheel and start the server; no dated record of such a run was found |
| `R06` | pass | The v2.0.0 notes name the features and fixes |
| `R07` | fail | The v2.0.0 notes are generated from commit subjects and do not match a changelog entry: `CHANGELOG.md` has no `2.0.0` section, the changes are still under `[Unreleased]`, and there is a stray `## [] - $(date ...)` heading. No gate refuses that |
| `R08` | pass | PyPI trusted publishing from the `pypi` environment of `release.yml`, documented in `AGENTS.md` and `RELEASE.md` |
| `R09` | partial | `release.yml` runs bandit and `safety check` with failures ignored before publishing, so the dependency check cannot fail the release. Today no Dependabot or secret scanning alert is open, but no dated result is recorded with a release |

## Product identity

| ID | Result | Evidence |
|---|---|---|
| `I01` | pass | The wheel is built from `pyproject.toml`: name `trsdn-markitdown-mcp`, version `2.0.0` |
| `I02` | pass | `[project.urls]` holds the repository and the issue tracker |
| `I03` | pass | `license = "MIT"` and `license-files`; the holder is named in `LICENSE` |
| `I04` | fail | `markitdown-mcp --version` and `--help` start the server and wait; neither prints a version or links |
| `I05` | na | A command-line package has no place for an icon |
| `I06` | partial | The package version comes from `pyproject.toml`, but `markitdown_mcp/__init__.py` types `__version__ = "1.0.0"` by hand, which is stale |

## Documentation and site

| ID | Result | Evidence |
|---|---|---|
| `T01` | na | The primary product is code, not documentation |
| `T02` | na | As `T01` |
| `T03` | na | As `T01` |
| `T04` | na | As `T01` |
| `T05` | na | As `T01` |
| `W01` | na | No website is published and the audience needs the package, not a page |
| `W02` | na | As `W01` |
| `W03` | na | As `W01` |
| `W04` | na | As `W01` |
| `W05` | na | As `W01` |
| `W06` | na | As `W01` |
| `W07` | na | As `W01` |
| `W08` | na | As `W01` |
| `W09` | na | As `W01` |

## Agent readiness

| ID | Result | Evidence |
|---|---|---|
| `G01` | pass | `AGENTS.md` at the root |
| `G02` | pass | "Working in this repository" states purpose, layout and the commands; the validation command passed |
| `G03` | pass | History rewriting, force pushes, secrets, releases and data-destructive behaviour are named. Deployments: none exist |
| `G04` | pass | No tool-specific instruction file exists |
| `G05` | pass | One documented sequence, run from a clean environment |
| `G06` | pass | `schemas/` and `docs/api/generated/` are named in `AGENTS.md` |
| `G07` | pass | `AGENTS.md`, "Attribution", states the trailer rule |
| `G08` | pass | `.github/github-app.yml` points at `AGENTS.md` |

## Language

| ID | Result | Evidence |
|---|---|---|
| `L01` | pass | "Project facts" declares English |
| `L02` | pass | Sampled the server's messages and the README: English only |
| `L03` | pass | The same sentence declares English only |
| `L04` | na | One locale, so no catalogs |
| `L05` | na | Nothing formats a date, number or currency for display |
| `L06` | na | No translations shipped |
| `L07` | pass | README, `docs/`, comments, recent commits and release notes are English |

## Accessibility

| ID | Result | Evidence |
|---|---|---|
| `X01` | pass | A stdio server with no interactive interface; the terminal is keyboard-operated |
| `X02` | pass | No interactive elements |
| `X03` | pass | The server sets no colours or sizes |
| `X04` | pass | "Project facts" documents plain-text output |
| `X05` | pass | "Project facts" states that no limitation is known |

## Data protection

| ID | Result | Evidence |
|---|---|---|
| `Y01` | pass | "Project facts": nothing is collected; the server reads files it is asked to convert and writes where the caller says |
| `Y02` | pass | Source contacts no network; the one destination, Google speech recognition through the optional `speechrecognition` package, is named |
| `Y03` | pass | No telemetry, analytics or crash reporting in source or dependencies |
| `Y04` | pass | Output goes only to the directory the caller names; the safe directories are named |
| `Y05` | pass | The one third party that receives content, for audio, is named |
| `Y06` | pass | "Project facts": nothing is retained beyond the files the caller asked for |

## Archived

| ID | Result | Evidence |
|---|---|---|
| `A01` | na | The repository is not archived |
| `A02` | na | As `A01` |
| `A03` | na | As `A01` |
| `A04` | na | As `A01` |
