[![Pylint](https://github.com/MaineDSA/MembershipDashboard/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/MaineDSA/MembershipDashboard/actions/workflows/pylint.yml)

# Membership Dashboard

Herein lies a Python module that builds a dashboard to analyze DSA membership lists.
It uses web frameworks to create browser-based data visualizations.

## Getting Started

To run this code, you'll need to have Python 3.9, 3.10, 3.11, or 3.12 installed on your machine. You'll also need to install the required packages by running the following command from inside the project folder:

```shell
python3 -m pip install -r requirements.txt
```

## Usage

1. Clone the repository and navigate to the project folder.
2. Put the name of the membership lists you get from National DSA into a UTF-8 text file called `.list_name` in the project folder. We use `maine_membership_list` and the repo includes the `test_membership_list` submodule which includes a single randomly-generated list in the correct format.
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

## Screenshots (based on random testing data for demonstration/development purposes)
![Screenshot from 2023-12-09 22-40-04](https://github.com/MaineDSA/MembershipDashboard/assets/1916835/a9dadd59-e995-4a4b-b732-88f94e157e84)
![Screenshot from 2023-12-09 22-40-14](https://github.com/MaineDSA/MembershipDashboard/assets/1916835/c179e4ae-b300-4131-9647-f5df9be6511e)
![Screenshot from 2023-12-09 22-40-31](https://github.com/MaineDSA/MembershipDashboard/assets/1916835/294e89d5-2d65-4156-b8f5-7fd170d457c1)
![Screenshot from 2023-12-09 22-40-53](https://github.com/MaineDSA/MembershipDashboard/assets/1916835/30895742-4fda-43d1-a66c-729da1193a4a)
![Screenshot from 2023-12-09 22-42-01](https://github.com/MaineDSA/MembershipDashboard/assets/1916835/f0be090b-4188-439f-8b27-b4e567bb81c7)
![Screenshot from 2023-12-09 22-42-11](https://github.com/MaineDSA/MembershipDashboard/assets/1916835/b6449275-6c87-445e-bda9-47591d430c97)
