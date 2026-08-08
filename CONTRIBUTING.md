## Getting Started

To run this code, you'll need to have Python 3.12, 3.13, or 3.14 installed on your machine. You'll also need to
install the required packages by running the following commands from inside the project folder:

```shell
pip install -U pip uv
```

```shell
uv sync
```

```shell
uv run pre-commit install
```

```shell
uv run src/app.py
```

To aid in testing, you should add `DEBUG=TRUE` to your `.env` file.
This will run dash in [debug mode](https://dash.plotly.com/devtools#configuring-with-run).

## Code Submissions

### Tests

Some parts of this module (mostly those involving list scanning and data processing) feature unit tests,
so please run `pytest` in the project directory before committing.

### Dependencies

If you add or modify any dependencies, be sure to list them in pyproject.toml.
The optional dependency group [dev] is used for dependencies used by developers working on this codebase.
These will not be installed for end-users.

### Style

`pre-commit run -a` should be run to standardize style and formatting before attempting to commit.
