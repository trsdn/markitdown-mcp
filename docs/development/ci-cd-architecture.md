# CI/CD Architecture Diagrams

This document contains visual representations of the CI/CD system architecture and workflow flows.

## Overall Tiered System Architecture

```mermaid
graph TB
    subgraph "Tier 1: Required PR Gates"
        A[Developer PR / Push] --> C[CI Quality Gates]
        C --> F{All CI Gates Passed?}
    end

    subgraph "Tier 2: Comprehensive Matrix & Audits"
        A --> D[Security Scan]
        A --> E[Test Suite Matrix]
    end

    subgraph "Branch Protection Decision"
        F -->|Pass| G[Merge Approved]
        F -->|Fail| H[Block Merge]

        G --> I[Merge to Main]
        H --> J[Fix Required]
    end

    subgraph "Release Pipeline"
        I --> K[Version Bump Analysis]
        K --> L{Release Needed?}
        L -->|Yes| M[Create Version PR]
        L -->|No| N[Continue Development]

        M --> O[Review & Merge]
        O --> P[Auto Tag Creation]
        P --> Q[Release Workflow]
        Q --> R[GitHub Release]
        Q --> S[PyPI Publication]
    end

    subgraph "Documentation"
        A --> T[Docs CI]
        T --> U[Build Validation]
        U --> V[Deploy Docs]
    end

    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style Q fill:#e3f2fd
```

## Workflow Trigger Matrix

```mermaid
graph LR
    subgraph "Triggers"
        A[Push to Main]
        B[Pull Request]
        C[Schedule]
        D[Manual]
        E[Tag Creation]
    end

    subgraph "Workflows"
        F[Fast Tests]
        G[CI Quality Gates]
        H[Test Suite]
        I[Security]
        J[Documentation]
        K[Version Bump]
        L[Release]
        M[Pre-Release]
    end

    A --> F
    A --> G
    A --> H
    A --> I
    A --> K

    B --> F
    B --> G
    B --> H
    B --> I
    B --> J

    C --> I
    C --> J
    C --> K

    D --> H
    D --> M
    D --> K

    E --> L
```

## Quality Gates Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GH as GitHub
    participant Fast as Fast Tests
    participant Gates as CI Quality Gates
    participant Test as Test Suite
    participant Sec as Security
    participant Merge as Auto-Merge

    Dev->>GH: Create PR
    GH->>Fast: Trigger Fast Tests
    GH->>Gates: Trigger Quality Gates
    GH->>Test: Trigger Test Suite
    GH->>Sec: Trigger Security Scan

    Fast->>GH: ✅ Unit tests pass
    Gates->>GH: ✅ Coverage 85%
    Test->>GH: ✅ Multi-platform OK
    Sec->>GH: ✅ No vulnerabilities

    GH->>Merge: All checks passed
    Merge->>GH: PR approved for merge

    Dev->>GH: Merge PR
    GH->>GH: Merge to main
```

## Release Pipeline Flow

```mermaid
flowchart TD
    A[Commits Merged to Main] --> B[Version Bump Workflow]
    B --> C{Analyze Commits}

    C -->|feat:| D[Minor Bump 1.X.0]
    C -->|fix:| E[Patch Bump 1.0.X]
    C -->|BREAKING:| F[Major Bump X.0.0]
    C -->|No significant changes| G[Skip Release]

    D --> H[Generate Changelog]
    E --> H
    F --> H

    H --> I[Create Version Bump PR]
    I --> J[Maintainer Review]
    J --> K[Merge PR]

    K --> L[Auto-Create Tag v1.2.3]
    L --> M[Release Workflow Triggered]

    M --> N[Quality Validation]
    N --> O[Build Package]
    O --> P[Run Tests]
    P --> Q[Create GitHub Release]
    Q --> R[Publish to PyPI]

    R --> S[Success Notification]

    style D fill:#e8f5e8
    style E fill:#e1f5fe
    style F fill:#ffebee
    style Q fill:#e3f2fd
    style R fill:#f3e5f5
```

## Security Scanning Pipeline

```mermaid
graph TB
    subgraph "Security Workflows"
        A[Code Push] --> B[Security Workflow]
        B --> C[Bandit SAST]
        B --> D[Safety Dependency Scan]
        B --> E[GitLeaks Secret Scan]
        B --> F[CodeQL Analysis]

        C --> G{High Severity?}
        D --> H{Vulnerabilities?}
        E --> I{Secrets Found?}
        F --> J{Security Issues?}

        G -->|Yes| K[Block Merge]
        G -->|No| L[Continue]

        H -->|Yes| K
        H -->|No| L

        I -->|Yes| K
        I -->|No| L

        J -->|Yes| K
        J -->|No| L

        K --> M[Notify Security Team]
        L --> N[Security Cleared]
    end

    style K fill:#ffebee
    style N fill:#e8f5e8
```

## Test Strategy Architecture

```mermaid
graph LR
    subgraph "Fast Tests (2-3 min)"
        A[Unit Tests] --> A1[Core Logic]
        A --> A2[MCP Protocol]
        A --> A3[File Operations]

        B[Integration Smoke] --> B1[Server Startup]
        B --> B2[Tool Discovery]
        B --> B3[Basic Conversion]

        C[Security Quick] --> C1[Bandit High Only]
        C --> C2[Dependency Basic]
    end

    subgraph "Full Test Suite (5-8 min)"
        D[Comprehensive Tests] --> D1[Multi-Platform]
        D --> D2[Python Matrix]
        D --> D3[Full Integration]

        E[Performance Tests] --> E1[Load Testing]
        E --> E2[Memory Usage]
        E --> E3[Timeout Validation]

        F[Compatibility] --> F1[File Format Tests]
        F --> F2[MCP Client Tests]
        F --> F3[Environment Tests]
    end

    style A fill:#e1f5fe
    style D fill:#e8f5e8
```

## Documentation Workflow

```mermaid
graph TB
    A[Doc Changes] --> B[Documentation CI]
    B --> C[Docstring Validation]
    B --> D[Sphinx Build]
    B --> E[Link Checking]
    B --> F[Spell Check]
    B --> G[MCP Tool Doc Validation]

    C --> H{All Pass?}
    D --> H
    E --> H
    F --> H
    G --> H

    H -->|Yes| I[Deploy Documentation]
    H -->|No| J[Block Merge]

    I --> K[Update GitHub Pages]
    I --> L[Update API Docs]

    style I fill:#e8f5e8
    style J fill:#ffebee
```

## Monitoring and Alerting

```mermaid
graph TB
    subgraph "Monitoring Sources"
        A[Workflow Results] --> D[Status Dashboard]
        B[Test Metrics] --> D
        C[Security Alerts] --> D
    end

    subgraph "Alert Channels"
        D --> E[GitHub Notifications]
        D --> F[PR Comments]
        D --> G[Slack Alerts]
        D --> H[Email Reports]
    end

    subgraph "Metrics Tracked"
        I[Test Success Rate]
        J[Build Duration]
        K[Coverage Percentage]
        L[Security Issues]
        M[Dependency Health]
    end

    D --> I
    D --> J
    D --> K
    D --> L
    D --> M
```

## Dependency Management Flow

```mermaid
sequenceDiagram
    participant Dep as Dependabot
    participant GH as GitHub
    participant CI as CI/CD
    participant Auto as Auto-Approve
    participant Rev as Reviewer

    Note over Dep: Weekly scan
    Dep->>GH: Create dependency PR
    GH->>CI: Run full test suite
    CI->>GH: Tests pass ✅

    alt Safe update (patch/minor)
        GH->>Auto: Auto-approve & merge
        Auto->>GH: Merged automatically
    else Major update or security
        GH->>Rev: Request manual review
        Rev->>GH: Review and approve
        Rev->>GH: Merge manually
    end

    GH->>CI: Trigger post-merge checks
    CI->>GH: Validation complete
```

This architecture ensures:

- **Fast Feedback**: Quick validation for common issues
- **Comprehensive Coverage**: Full validation before release
- **Security First**: Multiple security layers
- **Quality Gates**: Enforced standards at every step
- **Automated Releases**: Minimal manual intervention
- **Monitoring**: Full visibility into system health