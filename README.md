# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MaineDSA/membership_dashboard/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                 |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/utils/\_\_init\_\_.py            |        0 |        0 |        0 |        0 |    100% |           |
| src/utils/geocoding.py               |       46 |        8 |       10 |        3 |     77% |20, 27, 44-47, 55, 60 |
| src/utils/scan\_lists.py             |      112 |       14 |       16 |        3 |     87% |63, 75-76, 153-154, 163-169, 198-199 |
| src/utils/schema.py                  |       11 |        0 |        0 |        0 |    100% |           |
| tests/\_\_init\_\_.py                |        0 |        0 |        0 |        0 |    100% |           |
| tests/utils/\_\_init\_\_.py          |        0 |        0 |        0 |        0 |    100% |           |
| tests/utils/conftest.py              |       31 |        3 |        0 |        0 |     90% |36, 48, 60 |
| tests/utils/test\_branch\_tagging.py |       12 |        0 |        0 |        0 |    100% |           |
| tests/utils/test\_data\_cleaning.py  |       35 |        0 |        0 |        0 |    100% |           |
| tests/utils/test\_data\_schema.py    |        8 |        2 |        2 |        1 |     70% |     13-14 |
|                            **TOTAL** |  **255** |   **27** |   **28** |    **7** | **87%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/MaineDSA/membership_dashboard/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/MaineDSA/membership_dashboard/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/MaineDSA/membership_dashboard/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/MaineDSA/membership_dashboard/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FMaineDSA%2Fmembership_dashboard%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/MaineDSA/membership_dashboard/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.