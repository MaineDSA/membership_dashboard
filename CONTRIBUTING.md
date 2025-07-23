## Getting Started

To run this code, you'll need to have Python 3.9, 3.10, 3.11, or 3.12 installed on your machine. You'll also need to
install the required packages by running the following commands from inside the project folder:

```shell
pip install -U pip uv
```

```shell
uv venv
```

```shell
source .venv/bin/activate
```

```shell
uv pip install -e .[dev]
```

```shell
pre-commit install
```

```shell
python3 -m src.app
```

## Code Submissions

### Tests

Some parts of this module (mostly those involving list scanning) feature unit tests, so please run `pytest` in the
project directory before committing.

### Dependencies

If you add or modify any dependencies, be sure to list them in pyproject.toml.
The optional dependency group [dev] is used for dependencies used by developers working on this codebase.

### Style

If your text editor doesn't support [.editorconfig](https://editorconfig.org/), please reference
the [.editorconfig file](.editorconfig) for some basic formatting norms.
Regardless, `ruff format .` should be run to standardize formatting before attempting to commit.
