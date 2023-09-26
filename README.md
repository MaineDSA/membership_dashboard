# Membership Dashboard

Herein lies a Python script that builds a dashboard to analyze membership lists.
It uses the Dash framework for creating web-based data visualizations.

## Getting Started

To run this code, you'll need to have Python installed on your machine. You'll also need to install the required packages by running the following command:

```shell
pip install dash pandas plotly numpy
```

## Usage

1. Clone the repository and navigate to the project folder.
2. Open a terminal and run the following command to start the dashboard:

```shell
python <path-to-python-file>
```

3. Open your browser and go to `http://localhost:8050` to view the dashboard.

## Features

The dashboard provides the following features:

- Dropdown menu to select the membership list date you want to view.
- Table displaying the selected membership list, a few rows at a time.
- Metrics showing the number of lifetime members, members in good standing, expiring members, and lapsed members.
- Graphs displaying membership counts, dues, union membership, racial demographics, and length of membership.

## Notes

- The membership lists should be in the form of zipped CSV files.
- The code assumes that the membership lists are located in the `maine_membership_list` folder.
- The membership lists should follow a specific naming convention: `<name>_<YYYYMMDD>.zip` containing a single csv file called `maine_membership_list.csv`.

Feel free to explore the code and modify it according to your needs!
