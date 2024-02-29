[![Python Check](https://github.com/MaineDSA/membership_dashboard/actions/workflows/lint-python.yml/badge.svg)](https://github.com/MaineDSA/membership_dashboard/actions/workflows/lint-python.yml) [![Pytest](https://github.com/MaineDSA/membership_dashboard/actions/workflows/pytest.yml/badge.svg)](https://github.com/MaineDSA/membership_dashboard/actions/workflows/pytest.yml) [![CodeQL](https://github.com/MaineDSA/membership_dashboard/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/MaineDSA/membership_dashboard/actions/workflows/github-code-scanning/codeql)

# Membership Dashboard

Herein lies a Python module that builds a dashboard to analyze DSA membership lists.
It uses web frameworks to create browser-based data visualizations.

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
uv pip install .
```

## Usage

1. Clone the repository and open the folder.
2. Put the name of the membership lists you get from National DSA into a `.env` configuration file in the project folder
   after the prefix `LIST=`. Here in Maine, we use `LIST=maine_membership_list`.
3. Put a [MapBox](https://www.mapbox.com/) API token into the same file (on another line) after the
   prefix `MAPBOX=`. [OPTIONAL]
4. Put a CSV called `branch_zips.csv` containing zip codes matched with branch names in the project folder. [OPTIONAL]
5. Create a folder with the same title as the membership lists you receive from National DSA.
6. Add membership lists to the folder (see [notes](#notes) below).
7. Open a terminal and run the following command to start the dashboard:

    ```shell
    python3 -m src.app
    ```

8. Open your browser and go to `http://localhost:8050` to view the dashboard.

## Features

The dashboard provides the following features:

- Light and Dark modes via toggle switch in sidebar.
- Standardizes some important membership list metrics across variances in membership list formatting going back to at
  least Jan 2020.
- Tags members with the appropriate branch for their zip code, if a branch_zips.csv file is provided with the columns
  zip and branch. As tagging reoccurs each time the program is loaded, all branch labeling is based on the current
  branch zip codes allocations, as opposed to historical zip code allocations.
- Dropdown menus in sidebar to select an active membership list and another for seeing changes between lists.
- Timeline graph showing long-term trends across all loaded lists. Choose what is shown by selecting columns from the
  dropdown list.
- List table displaying the active membership list with the option to export a CSV. If a compare list is selected, only
  the rows that changed are shown.
- Metrics showing the number of constitutional members, members in good standing, expiring members, and lapsed members.
- Graphs displaying membership counts, dues, union membership, length of membership, and racial demographics.
- Provides comprehensive retention data tracking based on join date, length of membership, and more.
- Maps addresses to allow visualization of how membership metrics are distributed across the state.

## Notes

- The membership lists should be in the form of zipped CSV files (as provided by National DSA).
- The membership list zip files should have the list date appended to the zip file name (as `name_<YYYYMMDD>.zip`) and
  contain a single csv file.
- The project folder contains the submodule `fake_membership_list` for testing/demonstration purposes. It contains no
  real member information.

Feel free to explore the code and modify it according to your needs!

## Screenshots (based on random testing data for demonstration/development purposes)

![timeline](https://github.com/MaineDSA/membership_dashboard/assets/1916835/032d5eaf-34f1-4bd7-96ec-d9927d243d05)
![member list](https://github.com/MaineDSA/membership_dashboard/assets/1916835/394b6855-434f-4162-937f-a77e62395b8c)
![metrics](https://github.com/MaineDSA/membership_dashboard/assets/1916835/65ae26bd-9776-4536-8a38-4ca2aa8a673c)
![graphs](https://github.com/MaineDSA/membership_dashboard/assets/1916835/4ef8ecbb-c4f5-4141-8414-58b81b5ffe90)
![retention graphs 1](https://github.com/MaineDSA/membership_dashboard/assets/1916835/bc65a45a-8343-4dad-8c01-7a91b7517833)
![retention graphs 2](https://github.com/MaineDSA/membership_dashboard/assets/1916835/25eac558-4a29-4069-b000-e2639fc405c8)
![map](https://github.com/MaineDSA/MembershipDashboard/assets/1916835/f0be090b-4188-439f-8b27-b4e567bb81c7)
![light mode](https://github.com/MaineDSA/MembershipDashboard/assets/1916835/b6449275-6c87-445e-bda9-47591d430c97)
