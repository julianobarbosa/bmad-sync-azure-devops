# Contributing

Thank you for your interest in contributing to BMAD Sync Azure DevOps!

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/bmad-sync-azure-devops.git
   cd bmad-sync-azure-devops
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Requirements

- Python 3.6+ (scripts use stdlib only — no pip install needed)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) with `azure-devops` extension (for integration testing)
- [pytest](https://docs.pytest.org/) (for running tests)

### Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Tests cover parsing, hashing, normalization, and slug generation — no Azure DevOps connection required.

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use 4-space indentation (no tabs)
- Include type hints on all function signatures
- Add docstrings to all public functions
- Keep scripts stdlib-only — do not add external dependencies

### Example

```python
def my_function(items: List[Dict[str, str]], verbose: bool = False) -> Dict[str, int]:
    """Short description of what this function does."""
    ...
```

## Commit Messages

- Use imperative mood: "Add feature" not "Added feature"
- Keep the first line under 72 characters
- Reference issues when applicable: "Fix #42"

## Pull Request Process

1. Ensure all tests pass (`pytest tests/ -v`)
2. Update `CHANGELOG.md` under `[Unreleased]` with your changes
3. Update documentation if your change affects user-facing behavior
4. Submit a PR with a clear description of the change and its motivation

## What to Contribute

- Bug fixes (especially cross-platform issues)
- Test coverage improvements
- Documentation improvements
- New parsing patterns for BMAD artifact formats
- Process template support improvements

## Reporting Issues

- Use the [GitHub Issues](https://github.com/cfpeterkozak/bmad-sync-azure-devops/issues) page
- Include your OS, Python version, and Azure DevOps process template
- For parsing issues, include a (sanitized) sample of the markdown that fails

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
