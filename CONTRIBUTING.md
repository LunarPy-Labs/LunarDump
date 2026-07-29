# Contributing to LunarDump 🌔

First off, thank you for considering contributing to **LunarDump**! It's open-source projects like this that make the developer community such an amazing place to learn, inspire, and create.

All types of contributions are encouraged and appreciated:
- 🐛 **Reporting Bugs & Edge Cases**
- 💡 **Proposing New Features & Database Engine Plugins**
- 📝 **Improving Documentation & Usage Examples**
- 🔧 **Submitting Pull Requests (PRs)**

---

## 🛠️ Development Setup

Follow these steps to set up your local development environment:

### 1. Fork and Clone the Repository

Fork [indhifarhandika/LunarDump](https://github.com/indhifarhandika/LunarDump) on GitHub, then clone your fork:

```bash
git clone https://github.com/YOUR-USERNAME/LunarDump.git
cd LunarDump
```

### 2. Set Up Virtual Environment & Dependencies

LunarDump supports Python 3.10+. Create a clean virtual environment and install all development dependencies:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate environment (Linux/macOS)
source .venv/bin/activate

# On Windows PowerShell:
# .venv\Scripts\Activate.ps1

# Install package in editable mode with development & GCS dependencies
pip install -e ".[dev,gcs]"
```

---

## 📐 Project Architecture Overview

To help you navigate the codebase:

```text
LunarDump/
├── lunardump/
│   ├── main.py              # Typer CLI application entry point
│   ├── config/              # Pydantic v2 schemas and YAML/env loader
│   ├── core/
│   │   ├── dumpers/         # Database plugins (PostgreSQL, MySQL, MongoDB)
│   │   ├── security/        # AES-256-GCM cipher streaming & keygen
│   │   ├── storage/         # Cloud storage providers (S3, GCS, Local)
│   │   ├── notification/    # Webhook notifiers (Telegram, Slack)
│   │   └── utils/           # Subprocess runner & Rich logger
├── tests/                   # Pytest test suite (100% mocked, no real DB required)
├── pyproject.toml           # Hatchling build metadata & dependencies
└── README.md
```

---

## 🧪 Testing & Code Quality Guidelines

We maintain high code quality standards. All Pull Requests must pass the automated test suite and maintain **high test coverage (>= 80%)**.

### Run Tests and Coverage

Before submitting a PR, run pytest with coverage reporting:

```bash
pytest --cov=lunardump --cov-report=term-missing
```

### Writing Tests for New Features

- If you add a new database driver (e.g. SQLite, Oracle), add a corresponding test in `tests/test_dumpers.py`.
- If you add a new storage driver, add test coverage in `tests/test_storage.py`.
- Use `unittest.mock.patch` for external network calls and subprocess executions so tests run fast and offline.

---

## 🔀 Pull Request (PR) Workflow

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feat/add-oracle-dumper
   # or
   git checkout -b fix/s3-retention-bug
   ```

2. **Commit Convention**:
   Use clear and descriptive commit messages following Conventional Commits:
   - `feat: add support for Azure Blob Storage`
   - `fix: resolve GCS retention date comparison issue`
   - `docs: update cron job configuration examples`
   - `test: add unit tests for Telegram webhook notifier`

3. **Push to Your Fork & Open PR**:
   ```bash
   git push origin feat/add-oracle-dumper
   ```
   Go to GitHub and open a Pull Request against the `main` branch of `indhifarhandika/LunarDump`.

---

## ❓ Need Help?

If you have questions, feel free to open a [GitHub Discussion](https://github.com/indhifarhandika/LunarDump/discussions) or create an issue.

Thank you for helping make **LunarDump** better! 🚀
