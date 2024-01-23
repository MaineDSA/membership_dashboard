## Getting Started

To run this code, you'll need to have Python 3.9, 3.10, 3.11, or 3.12 installed on your machine. You'll also need to
install the required packages by running the following commands from inside the project folder:

```shell
python3 -m venv venv
```
```shell
source venv/bin/activate
```
```shell
python3 -m pip install .[dev]
```
```shell
pre-commit install
```

## Code Submissions

If your text editor doesn't support `.editorconfig`, please reference [this file](https://github.com/MaineDSA/membership_dashboard/blob/main/.editorconfig) for some basic formatting norms.

`ruff format .` should be run to standardize formatting before attempting to commit. 

Some parts of this module (mostly those involving list scanning) feature unit tests, so please run `pytest` in the project directory before committing.
