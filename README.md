# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MaineDSA/membership_dashboard/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                             |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|--------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/\_\_init\_\_.py              |        0 |        0 |        0 |        0 |    100% |           |
| src/app.py                       |       15 |       15 |        2 |        0 |      0% |      1-36 |
| src/components/\_\_init\_\_.py   |        0 |        0 |        0 |        0 |    100% |           |
| src/components/colors.py         |        2 |        2 |        0 |        0 |      0% |      1-15 |
| src/components/dark\_mode.py     |        7 |        7 |        2 |        0 |      0% |      1-10 |
| src/components/sidebar.py        |        7 |        7 |        0 |        0 |      0% |      1-11 |
| src/components/status\_filter.py |        5 |        5 |        0 |        0 |      0% |       1-8 |
| src/pages/\_\_init\_\_.py        |        0 |        0 |        0 |        0 |    100% |           |
| src/pages/counts.py              |       31 |       31 |        4 |        0 |      0% |     1-127 |
| src/pages/graphs.py              |       39 |       39 |        6 |        0 |      0% |     1-186 |
| src/pages/list.py                |       21 |       21 |        2 |        0 |      0% |      1-89 |
| src/pages/map.py                 |       27 |       27 |        4 |        0 |      0% |     1-100 |
| src/pages/retention.py           |       36 |       36 |        2 |        0 |      0% |     1-407 |
| src/pages/timeline.py            |       29 |       29 |        4 |        0 |      0% |      1-97 |
| src/utils/\_\_init\_\_.py        |        0 |        0 |        0 |        0 |    100% |           |
| src/utils/geocoding.py           |       47 |        8 |       10 |        3 |     77% |21, 28, 45-48, 56, 61 |
| src/utils/retention.py           |       26 |       26 |        0 |        0 |      0% |      3-81 |
| src/utils/scan\_lists.py         |      106 |       12 |       10 |        1 |     89% |64, 76-77, 154-155, 164-169, 200 |
| src/utils/schema.py              |       12 |        0 |        0 |        0 |    100% |           |
|                        **TOTAL** |  **410** |  **265** |   **46** |    **4** | **35%** |           |


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