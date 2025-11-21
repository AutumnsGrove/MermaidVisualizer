# Agent Tool Guidance for MermaidVisualizer

This document provides essential guidance for AI agents working with the MermaidVisualizer codebase. Read this before making any changes to ensure proper setup and adherence to project conventions.

## Quick Start for Agents

### 1. Environment Setup (CRITICAL)

Before running any Python commands or tests, you MUST set up the environment:

```bash
# Install Node.js dependencies (required for Mermaid rendering)
npm install -g @mermaid-js/mermaid-cli

# Install Chrome headless shell for Puppeteer
npx puppeteer browsers install chrome-headless-shell

# Install Python package with UV (for system-wide command)
uv tool install --editable .

# OR for development
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Verify mermaid-cli
mmdc --version
# OR via npx
npx @mermaid-js/mermaid-cli --version

# Verify Chrome is available
ls ~/.cache/puppeteer/

# Verify Python tool
mermaid --help
```

## Project Architecture

### Core Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Extractor | `src/extractor.py` | Extracts Mermaid blocks from markdown |
| Generator | `src/generator.py` | Generates PNG/SVG using mermaid-cli |
| File Handler | `src/file_handler.py` | File discovery, output management, HTML index |
| CLI | `src/cli.py` | Click-based command-line interface |
| Gist Handler | `src/gist_handler.py` | GitHub Gist fetching support |

### Web App (PWA)

Located in `web-app/` - a separate Progressive Web App that works entirely client-side using Mermaid.js from CDN. This does NOT use the Python CLI.

## Critical Dependencies

### External Tools (Must Install)

1. **mermaid-cli** - The core rendering engine
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. **Chrome Headless Shell** - Required by Puppeteer for rendering
   ```bash
   npx puppeteer browsers install chrome-headless-shell
   ```

3. **Node.js** - Required for npx and mermaid-cli

4. **UV Package Manager** - Python package management
   - Install from: https://github.com/astral-sh/uv

### Python Dependencies

All defined in `requirements.txt` and `pyproject.toml`:
- `click` - CLI framework
- `pyyaml` - Configuration parsing
- `watchdog` - File watching
- `rich` - Beautiful CLI output
- `requests` - HTTP for Gist fetching

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_integration.py

# Run with verbose output
pytest -v
```

**Current test status**: 7 integration tests, all passing

## Code Style Requirements

### Formatting
- **Black** for code formatting with default settings
- Run before committing: `black src/ tests/`

### Type Hints
- All functions MUST have complete type hints (PEP 484)
- Use `mypy src/` to check types

### Docstrings
- All public functions require docstrings
- Use Google-style docstrings with Args, Returns, Raises sections
- Include usage examples where helpful

### Example
```python
def extract_diagrams(content: str, source_file: str) -> list[MermaidDiagram]:
    """Extract all Mermaid diagram blocks from markdown content.

    Args:
        content: Raw markdown content to parse
        source_file: Path to the source file for metadata

    Returns:
        List of MermaidDiagram objects with content and metadata

    Raises:
        ValueError: If content is empty or invalid

    Example:
        >>> diagrams = extract_diagrams("```mermaid\\nflowchart TD\\n```", "doc.md")
        >>> len(diagrams)
        1
    """
```

## Git Commit Conventions

This project uses **Conventional Commits**. See `GIT_COMMIT_STYLE_GUIDE.md` for full details.

### Commit Format
```
<type>: <description>

[optional body]
```

### Types
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code formatting (no logic changes)
- `refactor:` - Code restructuring
- `test:` - Test additions/modifications
- `chore:` - Maintenance tasks

### Examples
```bash
git commit -m "feat: Add support for mindmap diagrams"
git commit -m "fix: Resolve Chrome detection on Linux"
git commit -m "docs: Update installation instructions"
git commit -m "test: Add integration tests for gist handler"
```

### Rules
- Keep subject under 50 characters
- Use imperative mood ("Add", not "Added")
- No period at end of subject line
- One logical change per commit

## Common Tasks

### Adding a New Diagram Type

1. Update `DIAGRAM_TYPE_PREFIXES` in `src/file_handler.py`
2. Add detection pattern in `src/extractor.py` if needed
3. Add test case in `tests/sample_data/test.md`
4. Run tests to verify

### Modifying the CLI

1. Edit `src/cli.py`
2. Use Click decorators for commands/options
3. Use Rich for user-facing output
4. Test with `python -m src.cli <command>`

### Working with the PWA

The web app is independent of the Python CLI:
- Edit `web-app/js/app.js` for functionality
- Edit `web-app/index.html` for structure
- Uses Tailwind CSS for styling
- Test by opening `web-app/index.html` in a browser

## Troubleshooting

### "Could not find Chrome"

```bash
npx puppeteer browsers install chrome-headless-shell
ls ~/.cache/puppeteer/  # Verify installation
```

### "mmdc: command not found"

```bash
npm install -g @mermaid-js/mermaid-cli
```

### Tests fail with import errors

```bash
# Ensure you're in the virtual environment
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Diagram generation timeout

- Increase timeout in `config.yaml` (default: 60 seconds)
- Check Mermaid syntax validity at https://mermaid.live

## Important Files Reference

| File | Purpose |
|------|---------|
| `README.md` | User documentation |
| `PROJECT_STATUS.md` | Implementation status and next steps |
| `GIT_COMMIT_STYLE_GUIDE.md` | Detailed commit conventions |
| `config.yaml` | Default configuration |
| `pyproject.toml` | Package metadata and dependencies |
| `requirements.txt` | Python dependencies |

## Do's and Don'ts

### Do
- Run tests before committing
- Follow the commit message format
- Add type hints to all functions
- Update docstrings when changing function signatures
- Use Rich for CLI output formatting

### Don't
- Skip the mermaid-cli installation
- Commit without running `black`
- Use print() for user output (use Rich console)
- Modify generated files in `diagrams/`
- Push directly to main without testing

## Questions?

- Check `README.md` for user-facing documentation
- Check `PROJECT_STATUS.md` for implementation details
- Check `web-app/README.md` for PWA-specific guidance
