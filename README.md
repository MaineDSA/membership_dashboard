[![Pylint](https://github.com/MaineDSA/MembershipDashboard/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/MaineDSA/MembershipDashboard/actions/workflows/pylint.yml)

# Membership Dashboard

Herein lies a Python module that builds a dashboard to analyze DSA membership lists.
It uses web frameworks to create browser-based data visualizations.

## Getting Started

To run this code, you'll need to have Python 3.9, 3.10, or 3.11 installed on your machine. You'll also need to install the required packages by running the following command from inside the project folder:

```shell
python3 -m pip install -r requirements.txt
```

## Usage

1. Clone the repository and navigate to the project folder.
2. Put the name of the membership lists you get from National DSA into a UTF-8 text file called `.list_name` in the project folder. We use `maine_membership_list`.
3. Put a [MapBox](https://www.mapbox.com/) API token into a UTF-8 text file called `.mapbox_token` in the project folder.
4. Create a folder with the same title as the membership lists you receive from National DSA (you can use subfolders).
5. Add membership lists to the folder (see [notes](#notes) below).
6. Open a terminal and run the following command to start the dashboard:

```shell
python3 -m membership_dashboard
```

3. Open your browser and go to `http://localhost:8050` to view the dashboard.

## Features

The dashboard provides the following features:

- Dropdown menus in sidebar to select an active membership list and another to compare against.
- Timeline graph showing long-term trends across all loaded lists. Choose what is shown by selecting columns from the dropdown list.
- List table displaying the active membership list with the option to export a CSV. If a compare list is selected, only the rows that changed are shown.
- Metrics showing the number of constitutional members, members in good standing, expiring members, and lapsed members.
- Graphs displaying membership counts, dues, union membership, length of membership, and racial demographics.
- Maps addresses to allow visualization of how membership metrics are distributed across the state.
- Standardizes some important membership list metrics across variances in membership list formatting going back to at least Jan 2020.

## Notes

- The membership lists should be in the form of zipped CSV files (as provided by National DSA).
- The membership list zip files should have the list date appended to the zip file name (as `name_<YYYYMMDD>.zip`) and contain a single csv file.

Feel free to explore the code and modify it according to your needs!
