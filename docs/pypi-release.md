# PyPI release preparation

The repository is now structured for PyPI distribution:

- package code lives under `src/ai9414`
- the installed CLI entry point is `ai9414 = "ai9414.cli:main"`
- frontend static assets are bundled into the wheel
- `python -m ai9414 ...` works through `src/ai9414/__main__.py`

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

Before the first upload:

1. Create or sign in to the PyPI account that will own `ai9414`.
2. Confirm that the project name `ai9414` is available on PyPI.
3. Create an API token or configure trusted publishing for the repository.
4. Upload the built distributions in `dist/` when ready.

## Release checklist

1. Bump `version` in `pyproject.toml`.
2. Rebuild with `python -m build`.
3. Re-run `python -m twine check dist/*`.
4. Test-install the wheel in a fresh virtual environment.
5. Upload `dist/*.tar.gz` and `dist/*.whl` to PyPI.
