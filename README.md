# artificial-intelligence

Phase 1 reference implementation of the `ai9414` educational AI platform infrastructure.

## What is included

- shared `ai9414` namespace package
- common FastAPI launcher and route contract
- common JSON schema models
- support for `precomputed` and `incremental` execution modes
- static solution replay export
- placeholder demo app proving the infrastructure
- basic automated tests and developer documentation

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
python examples/placeholder_precomputed.py
```

Or run the incremental variant:

```bash
python examples/placeholder_incremental.py
```

## Student-facing example

```python
from ai9414.demo import PlaceholderDemo

app = PlaceholderDemo(execution_mode="precomputed")
app.load_example("count_to_three")
app.set_options(pace="normal")
app.show()
```

## Repository structure

```text
src/ai9414/
  core/
  demo/
  frontend/
examples/
tests/
docs/
```
