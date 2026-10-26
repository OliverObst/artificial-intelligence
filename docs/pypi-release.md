# PyPI release preparation

The repository is now structured for PyPI distribution:

- package code lives under `src/ai9414`
- the installed CLI entry point is `ai9414 = "ai9414.cli:main"`
- frontend static assets are bundled into the wheel
- `python -m ai9414 ...` works through `src/ai9414/__main__.py`
- GitHub Actions release publishing is defined in `.github/workflows/pypi-publish.yml`

## Local release verification

Run the following from a clean working tree:

```bash
uv sync --locked --extra dev --no-default-groups
uv run --no-sync pytest
uv build
uv run twine check dist/*
```

Then verify the wheel in a fresh environment:

```bash
uv venv --clear .venv-wheel-test
uv pip install --python .venv-wheel-test dist/ai9414-*.whl
.venv-wheel-test/bin/ai9414 list
.venv-wheel-test/bin/python -m ai9414 list --examples graph-bnb
```

## PyPI project setup

The recommended release path is PyPI Trusted Publishing from GitHub Actions.

Before the first upload:

1. Create or sign in to the PyPI account that will own `ai9414`.
2. In PyPI, go to account settings and add a new GitHub trusted publisher.
3. Use these values:
   - PyPI project name: `ai9414`
   - Owner: `OliverObst`
   - Repository name: `artificial-intelligence`
   - Workflow name: `pypi-publish.yml`
   - Environment name: `pypi`
4. Leave that publisher in the pending state until the first publish.
5. In GitHub, create an environment named `pypi` for this repository.

## Release checklist

1. Bump `version` in `pyproject.toml` and run `uv lock`.
2. Run the tests, build, distribution checks and fresh-wheel verification above.
3. Commit and push the release changes to `main`.
4. Confirm that the committed version matches the tested distributions.
5. Check that the new version has not already been published.
6. Tag the release, for example `git tag v0.1.1 && git push origin v0.1.1`.
7. GitHub Actions will run the tests, build the distributions and publish them to PyPI.
8. Verify the workflow succeeded, install the published version in a fresh
   environment, and create a GitHub release with the changes and upgrade command.

## Manual fallback

If Trusted Publishing is not available for some reason, manual upload still works:

```bash
uv build
uv run twine check dist/*
uv run twine upload dist/*
```

Use `__token__` as the username and a PyPI API token as the password.
