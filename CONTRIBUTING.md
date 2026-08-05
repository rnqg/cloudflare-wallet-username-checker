# Contributing

Contributions are welcome.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
mypy
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Pull requests

- Keep changes focused.
- Add or update tests for behavior changes.
- Update both `README.md` and `README.ru.md` when user-facing behavior changes.
- Never include bot tokens, databases, checkpoints or mass-scan exports.
- Describe API compatibility assumptions and rate-limit impact.
