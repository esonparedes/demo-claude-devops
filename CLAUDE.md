# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Python DevOps demo project that showcases CI/CD automation with Claude AI code review integration. The project includes a simple calculator module with comprehensive test coverage and automated deployment workflows.

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH for local development
export PYTHONPATH=.
```

### Building
```bash
# Build the package
python setup.py build
```

### Testing
```bash
# Run all tests with coverage
pytest --junitxml=results.xml --cov=src --cov-report=xml --verbose

# Run a single test file
pytest tests/test_calculator.py -v

# Run a specific test function
pytest tests/test_calculator.py::test_add -v

# Run tests without coverage
pytest tests/ -v
```

### Code Quality
The CI pipeline enforces code quality standards. While specific linting tools (black, isort, flake8, mypy, bandit) are referenced in CLAUDE.local.md, they are not currently installed in requirements.txt. If you need to add these checks:

```bash
# Install linting/formatting tools
pip install black isort flake8 mypy bandit

# Run formatters
black .
isort .

# Run linters
flake8 src/ tests/
mypy src/
bandit -r src/
```

## Architecture

### Project Structure
```
demo-claude-devops/
├── src/
│   └── calculator.py       # Core calculator module with basic math operations
├── tests/
│   └── test_calculator.py  # Pytest-based unit tests
├── scripts/
│   ├── claude_review.py    # Standalone script for Claude AI test analysis
│   └── deploy_staging.sh   # Deployment automation script
└── .github/workflows/
    └── ci.yml              # Main CI/CD pipeline with Claude integration
```

### CI/CD Pipeline Architecture

The GitHub Actions workflow (`.github/workflows/ci.yml`) implements a multi-stage pipeline:

1. **Setup** - Configures Python 3.11 and installs dependencies
2. **Build** - Builds the package using setuptools
3. **Unit Tests** - Runs pytest with coverage reporting and uploads artifacts
4. **Claude Review** - Uses `anthropics/claude-code-action@v1` to perform automated code review on pull requests
5. **Deploy** - Deploys to staging if all checks pass

### Claude AI Integration

The repository uses Claude in two ways:

1. **GitHub Action** (`.github/workflows/ci.yml:54-89`): The `claude_review` job runs on every PR and uses the `anthropics/claude-code-action@v1` to review code quality, test coverage, security, and performance. Claude posts comments directly to the PR using `gh pr comment`.

2. **Standalone Script** (`scripts/claude_review.py`): A Python script that analyzes pytest XML reports using the Anthropic API. It uses `claude-sonnet-4-5-20250929` model to summarize test results.

### Key Configuration Details

- **Python Version**: 3.11 (set in CI pipeline)
- **Test Framework**: pytest with pytest-cov for coverage
- **Coverage Reports**: Generated as both XML (for CI) and HTML (for local review in `tests/htmlcov/`)
- **Test Artifacts**: JUnit XML (`results.xml`) and coverage XML uploaded as GitHub Actions artifacts
- **PYTHONPATH**: Must be set to `.` for tests to import from `src/`

### Module Details

**src/calculator.py** provides seven mathematical functions:
- `add(a, b)` - Addition
- `subtract(a, b)` - Subtraction
- `multiply(a, b)` - Multiplication
- `divide(a, b)` - Division with zero-check (raises ValueError)
- `power(a, b)` - Exponentiation
- `modulus(a, b)` - Modulo with zero-check (raises ValueError)
- `absolute(a)` - Absolute value

All functions use simple implementations and include docstrings. Error handling is implemented for division and modulus operations.

## Important Policies

Refer to `CLAUDE.local.md` for comprehensive coding standards including:
- PEP 8 style requirements and formatting with Black
- Type hints and mypy strict checking
- Security scanning with bandit
- 80% minimum test coverage requirement
- Deployment validation requirements (no `latest` tags, health checks, rollback plans)
- Secrets management policies

## Branch Information

- **Main branch**: `main`
- **Current branch**: `additional-test-cases`
- Always create PRs targeting `main` branch

## Notes for Claude Code

- The `PYTHONPATH=.` environment variable is critical for running tests locally and in CI
- Test reports are uploaded as artifacts in CI for Claude review analysis
- The Claude review step has restricted tool access for security (only `gh` commands allowed)
- Deployment only proceeds if all previous jobs (including Claude review) succeed
