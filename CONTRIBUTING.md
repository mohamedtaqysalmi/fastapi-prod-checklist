# Contributing

This project is maintained by one person. Issues and pull requests are welcome, but replies
can take a few days.

## Setup

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
```

## Running the checks

CI runs the same commands on Python 3.11 and 3.14.

```bash
ruff check .
ruff format --check .
mypy
pytest
```

Coverage must stay at or above 85%.

## Branches and commits

Branch from `main` and name the branch `type/short-description`, for example
`feat/request-id-middleware` or `fix/cors-defaults`. Use the same types as commit messages:
`feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).
Pull requests are squash-merged, so the PR title becomes the commit message on `main`.

## Pull requests

- Keep a PR to one change. Open an issue first for anything large.
- Add or update tests. A bug fix should come with a test that fails without it.
- Fill in the PR template and make sure CI is green.
- Add a line under `Unreleased` in `CHANGELOG.md` for user-visible changes.

By contributing you agree that your work is released under the MIT license.
