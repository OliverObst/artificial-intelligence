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
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
python -m build
python -m twine check dist/*
```

Then verify the wheel in a fresh environment:

```bash
python -m venv .venv-wheel-test
source .venv-wheel-test/bin/activate
pip install dist/ai9414-*.whl
ai9414 list
python -m ai9414 list --examples graph-bnb
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

1. Bump `version` in `pyproject.toml`.
2. Commit and push the version bump to `main`.
3. Rebuild locally with `python -m build`.
4. Re-run `python -m twine check dist/*`.
5. Test-install the wheel in a fresh virtual environment.
6. Tag the release, for example `git tag v0.1.0 && git push origin v0.1.0`.
7. GitHub Actions will build the distributions and publish them to PyPI.

## Manual fallback

If Trusted Publishing is not available for some reason, manual upload still works:

```bash
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

Use `__token__` as the username and a PyPI API token as the password.
