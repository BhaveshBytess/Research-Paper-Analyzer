# Contributing to Research Paper Analyzer

Thank you for considering contributing to Research Paper Analyzer! This document outlines the process for contributing and helps ensure a smooth collaboration.

---

## 🎯 How Can I Contribute?

### Reporting Bugs
- **Search existing issues** before creating a new one
- **Use the bug report template** when opening an issue
- **Include**:
  - PDF characteristics (page count, venue, etc.)
  - Error messages and stack traces
  - Expected vs. actual behavior
  - Steps to reproduce

### Suggesting Enhancements
- **Check the roadmap** to avoid duplicates
- **Explain the use case** — why is this useful?
- **Provide examples** if possible
- **Consider scope** — does it fit the project goals?

### Pull Requests
- **Fork** the repository
- **Create a feature branch** from `main`
- **Write clear commit messages**
- **Add tests** for new functionality
- **Update documentation** if needed
- **Ensure CI passes** before requesting review

---

## 🏗️ Development Setup

### Prerequisites
- Python 3.10+
- Git
- Virtual environment tool (venv, conda, etc.)

### Setup Steps

```bash
# 1. Fork and clone
git clone https://github.com/BhaveshBytess/research-paper-analyzer.git
cd research-paper-analyzer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Install pre-commit hooks (optional but recommended)
pre-commit install

# 5. Set up API keys
export OPENROUTER_API_KEY="your-key-here"
```

---

## 📝 Code Style

### Python Style Guide
We follow **PEP 8** with some modifications:

- **Line length**: 100 characters (not 79)
- **Formatter**: Black
- **Import sorting**: isort
- **Type hints**: Required for all new functions
- **Docstrings**: Google style

### Running Formatters

```bash
# Format code
black research-paper-analyzer/

# Sort imports
isort research-paper-analyzer/

# Check types
mypy research-paper-analyzer/

# Lint
flake8 research-paper-analyzer/
```

### Example Function

```python
def extract_methods(
    pages: list[str],
    model: str = "deepseek",
    temperature: float = 0.3
) -> list[Method]:
    """
    Extract method descriptions from paper pages.

    Args:
        pages: List of page text strings
        model: LLM model identifier
        temperature: Sampling temperature for generation

    Returns:
        List of Method objects with name, category, components

    Raises:
        ValueError: If pages is empty
        APIError: If LLM call fails
    """
    pass
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_schema.py

# With coverage
pytest --cov=research_paper_analyzer --cov-report=html

# Integration tests (requires API key)
pytest tests/integration/ -m integration
```

### Test Structure

```
tests/
├── unit/                   # Fast, no external dependencies
│   ├── test_schema.py
│   ├── test_pdf_parser.py
│   └── test_evidence_matcher.py
├── integration/            # Requires API/models
│   ├── test_deepseek_extraction.py
│   └── test_end_to_end.py
└── fixtures/               # Sample data
    ├── sample_papers/
    └── expected_outputs/
```

### Writing Tests

```python
import pytest
from research_paper_analyzer.schema import Method

def test_method_validation():
    """Test Method model validates correctly."""
    method = Method(
        name="Transformer",
        category="Transformer",
        components=["MHA", "FFN"],
        description="Attention-based architecture"
    )
    assert method.name == "Transformer"
    assert len(method.components) == 2
```

---

## 🔀 Git Workflow

### Branch Naming

- `feature/add-ocr-support`
- `fix/evidence-matching-bug`
- `docs/update-api-examples`
- `refactor/pdf-parser-cleanup`

### Commit Messages

Use **conventional commits**:

```
feat: add OCR support for scanned PDFs
fix: correct evidence page numbering
docs: update installation instructions
refactor: simplify schema validation logic
test: add unit tests for pdf_parser
chore: update dependencies
```

### Pull Request Process

1. **Update your branch**
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature
   git rebase main
   ```

2. **Push and create PR**
   ```bash
   git push origin your-feature
   # Go to GitHub and create PR
   ```

3. **PR Checklist**
   - [ ] Code follows style guidelines
   - [ ] Tests pass locally
   - [ ] New tests added (if applicable)
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   - [ ] PR description explains changes

4. **Review Process**
   - Maintainer reviews within 3-5 business days
   - Address feedback with new commits
   - Don't force-push after review starts
   - Squash commits before merge (maintainer handles this)

---

## 📚 Documentation

### When to Update Docs

- **README.md**: Major features, API changes, installation steps
- **API docs**: Any public function/class changes
- **Examples**: New use cases or workflows
- **CHANGELOG.md**: All user-facing changes

### Documentation Standards

- Use **clear, concise language**
- Include **code examples** for complex features
- Add **screenshots/GIFs** for UI changes
- Update **table of contents** if adding sections

---

## 🐛 Bug Triage Labels

| Label | Meaning |
|-------|---------|
| `bug` | Something isn't working |
| `enhancement` | New feature or request |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention needed |
| `question` | Further information requested |
| `wontfix` | Will not be worked on |
| `duplicate` | Already reported |

---

## 🏆 Recognition

Contributors are recognized in:
- **README.md** acknowledgments section
- **CHANGELOG.md** for significant contributions
- **GitHub Contributors** page

---

## 📋 Review Checklist (for Maintainers)

- [ ] Code quality meets standards
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] No breaking changes (or clearly documented)
- [ ] Performance is acceptable
- [ ] Security implications considered
- [ ] Licensing is compatible

---

## ❓ Questions?

- **General questions**: [GitHub Discussions](https://github.com/BhaveshBytess/research-paper-analyzer/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/BhaveshBytess/research-paper-analyzer/issues)
- **Direct contact**: 10bhavesh7.11@gmail.com

---

## 🙏 Thank You!

Every contribution helps make Research Paper Analyzer better. Whether it's:
- Reporting a bug
- Fixing a typo
- Adding a feature
- Improving documentation

**Your effort is appreciated!**

---

**Last Updated:** 2025-11-03  
**Maintainers:** [Bhavesh Bytess](https://github.com/BhaveshBytess)
