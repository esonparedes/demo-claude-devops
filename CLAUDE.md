# CLAUDE.md

## Purpose

This document defines Python coding standards, testing requirements, and deployment validations enforced in our CI/CD pipelines. It is used alongside Claude AI reviews (Anthropic) to automatically validate pipeline outcomes — build success, unit tests, coverage, security checks, and deployment policies — and to provide actionable feedback in pull requests.

**Last Updated**: 2025-10-09

## Scope

Applies to all Python services, libraries, and scripts in this repository. It covers:

- Code quality (formatting, linting, static typing)
- Test strategy (unit, integration, coverage)
- CI pipeline checks and gating rules
- Deployment validation steps and post-deploy checks
- How Claude is used to analyze artifacts and enforce standards

## Python Coding Standards (must-follow)

### Style & Formatting

- Follow PEP 8 for code layout and naming conventions.
- Use Black for automatic formatting. Config: black --line-length 88.
- Use isort to sort imports. Combine with Black via pre-commit.
- Keep functions small and single-responsibility. Prefer clear names over clever code.

### Type Safety

- Use type hints everywhere public functions/classes are defined.
- Use mypy with strict or near-strict configuration in CI (mypy --strict or tuned flags).
- Add # type: ignore only with an explanation in code comments and a linked issue when necessary.

### Static Analysis & Security

- Run flake8 for linting and complexity checks (max-complexity = 12).
- Run bandit for basic security checks on Python code.
- Integrate safety/OSS vulnerability scanning on dependencies (e.g., safety check).

### Testing Practices

- Use pytest as the test runner.
- Tests should be deterministic and not depend on external systems (use fixtures and mocking).
- Use fixtures, parametrization, and clear arrange-act-assert style in tests.
- Test names should describe behavior (e.g., test_add_returns_sum_for_positive_integers).

### Documentation & Docstrings

- Use Google-style or NumPy-style docstrings for public modules, classes, functions.
- Include type annotations in docstrings for any runtime or generated docs.
- Keep README and module-level docs up-to-date with API examples.

## Test Strategy & Requirements

### Test Types

- Unit tests: fast, isolated, required for all modules. Must be run on every push/PR.
- Integration tests: run on a schedule or pre-merge depending on cost/time. Use a separate job.
- End-to-end (E2E): run in staging, not in the primary PR gate unless small smoke tests.

### Coverage

- Minimum branch or line coverage: 80% by default. Team may raise this per-service.
- Coverage is enforced in CI; if coverage drops below threshold, the pipeline fails and Claude flags the PR.

### Test Outputs

- Tests must produce machine-readable reports:
    - JUnit XML: pytest --junitxml=results.xml
    - Coverage XML: coverage xml -o coverage.xml (or --cov-report=xml)
- Upload reports as artifacts for Claude analysis and for debugging.

## Deployment Validation

Before promoting to **production**, enforce the following validations:

1. **Successful Build & Tests**
   - All builds complete without errors.
   - All tests pass (unit, integration, smoke).

2. **Claude Review Pass**
   - No critical findings reported by Claude.
   - Coverage and quality thresholds are met.

3. **Image Tag Policy**
   - No usage of the `latest` tag for production.
   - Use immutable, versioned tags (e.g., `v1.0.3`).

4. **Secrets & Configuration Check**
   - Ensure no plaintext secrets appear in artifacts or logs.
   - Validate environment variables via secrets manager (Vault, AWS Secrets Manager, etc.).

5. **Health Check**
   - Smoke test endpoint (`/healthz` or `/readyz`) must return **HTTP 200** in staging.
   - Passes at least **two consecutive checks** before deployment approval.

6. **Rollback Plan**
   - Must exist, documented, and tested in staging.
   - Rollback triggers automatically if metrics degrade post-deployment.

### Post-Deployment Checks
After deployment, monitor:
- Canary or smoke test success
- Application error rates and latency
- Replica readiness and scaling behavior
- Automatic rollback if SLA/SLO thresholds are exceeded

## Secrets & Policies

- Store **API keys**, deploy keys, and credentials in:
  - GitHub Secrets
  - HashiCorp Vault
  - AWS Secrets Manager or Azure Key Vault

- **Never** print or log secrets to stdout or pipeline logs.  
- Configure CI/CD to use masked secrets (e.g., `***` in logs).  
- Claude’s API key (`ANTHROPIC_API_KEY`) should:
  - Have **least privilege**
  - Be stored securely in GitHub Secrets
  - Have consumption monitoring (alerts on usage or cost spikes)
- Rotate all credentials every **90 days** or per policy.

## Troubleshooting Tips

| Issue | Likely Cause | Resolution |
|-------|---------------|------------|
| `ModuleNotFoundError: No module named 'src'` | Missing `PYTHONPATH` or `src/__init__.py` | Add `PYTHONPATH=.` in test job or create `src/__init__.py` |
| **Formatting fails** (`black`, `isort`) | Code not compliant with PEP8 or import order | Run `black .` and `isort .`, commit changes |
| **mypy errors** | Missing or incorrect type hints | Add or correct type annotations, or document any `# type: ignore` usage |
| **Coverage below threshold** | Uncovered code paths | Add or refactor tests to cover missed branches |
| **Claude API errors** | Missing/invalid `ANTHROPIC_API_KEY`, network issue | Verify GitHub secret configuration and SDK version |
| **Pipeline blocked by Claude review** | Test or coverage policy not met | Review `results.xml` and `coverage.xml` outputs, rerun after fix |
| **Security scan fails** | Vulnerable dependency | Update `requirements.txt` or pin secure versions |

