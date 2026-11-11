# fastapi-prod-checklist

A FastAPI template where production readiness is enforced by tests, not by a README promise.

**Status: early scaffold, the template is not usable yet.** Right now the repo only contains
packaging and tooling. The application, the readiness tests and the container setup are not
written yet, and this README will change as they land.

## Development setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
```

## Running the checks

```bash
ruff check .
ruff format --check .
mypy
pytest
```

## License

MIT, see [LICENSE](LICENSE).
