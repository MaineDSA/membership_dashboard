import os
import zipfile
import pandas as pd
import datetime
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.graph_objects as go
import numpy as np
import glob

FONT = dict(
	size=14,
	color="white"
)

memb_lists = {}
memb_list_dates = []

def scan_membership_list(directory: str, filename: str):
	print(f'Scanning {filename} for membership list.')
	date_from_name = datetime.datetime.strptime(os.path.splitext(filename)[0].split('_')[3], '%Y%m%d').date()
	if not date_from_name:
		print('No date detected. Skipping file.')
		return
	with zipfile.ZipFile(os.path.join(directory, filename)) as memb_list_zip:
		with memb_list_zip.open(f'{directory}.csv') as memb_list:
			date_formatted = date_from_name.isoformat()
			memb_lists[date_formatted] = pd.read_csv(memb_list, header=0)
			memb_list_dates.append(date_formatted)

def scan_all_membership_lists(directory:str):
	print(f'Scanning {directory} for zipped membership lists.')
	files = sorted(glob.glob(os.path.join(directory, '*.zip')), reverse=True)
	[scan_membership_list(directory, os.path.basename(filepath)) for filepath in files]

scan_all_membership_lists('maine_membership_list')

def membership_length(date:str):
	return (pd.to_datetime(datetime.date.today()) - pd.to_datetime(date, format='%Y-%m-%d')) // datetime.timedelta(days=365)

# Initialize the app
app = Dash(__name__)

style_metrics = {'display': 'inline-block', 'width': '25%', 'text-align': 'center', 'padding-top': '3em', 'padding-bottom': '1em'}
style_graphs_2 = {'display': 'inline-block', 'width': '50%'}
style_graphs_3 = {'display': 'inline-block', 'width': '33.33%'}
style_graphs_4 = {'display': 'inline-block', 'width': '25%'}

# App layout
app.layout = html.Div([
	html.Div(children='Membership Lists'),
	html.Hr(),
	dcc.Dropdown(options=memb_list_dates, value=memb_list_dates[0], id='list_dropdown'),
	dash_table.DataTable(
		data=memb_lists[memb_list_dates[0]].to_dict('records'),
		columns=[
			{'name': i, 'id': i, 'deletable': True} for i in sorted(memb_lists[memb_list_dates[0]].columns)
		],
		sort_action="native",
		sort_mode='multi',
		filter_action='native',
		page_size=10,
		style_table={'overflowY': 'auto', 'overflowX': 'auto'},
		id='membership_list'
	),
	html.Div(id='metrics-container', children=[
		html.Div(id='members_lifetime', style=style_metrics),
		html.Div(id='members_migs', style=style_metrics),
		html.Div(id='members_expiring', style=style_metrics),
		html.Div(id='members_lapsed', style=style_metrics),
	]),
	html.Div(id='graphs-container', children=[
		dcc.Graph(figure={}, id='membership_status', style=style_graphs_3),
		dcc.Graph(figure={}, id='membership_type', style=style_graphs_3),
		dcc.Graph(figure={}, id='union_member', style=style_graphs_3),
		dcc.Graph(figure={}, id='race', style=style_graphs_2),
		dcc.Graph(figure={}, id='membership_length', style=style_graphs_2),
	]),
])

def splitDataFrameList(df,target_column,separator):
	row_accumulator = []

	def splitListToRows(row, separator):
		if type(row[target_column]) == float:
			row[target_column] = 'unknown'
		split_row = row[target_column].split(separator)
		for s in split_row:
			new_row = row.to_dict()
			new_row[target_column] = s
			row_accumulator.append(new_row)

	df.apply(splitListToRows, axis=1, args = (separator, ))
	new_df2 = pd.DataFrame(row_accumulator)
	return new_df2

# Add controls to build the interaction
@callback(
	Output(component_id='membership_list', component_property='data'),
	Output(component_id='members_lifetime', component_property='children'),
	Output(component_id='members_migs', component_property='children'),
	Output(component_id='members_expiring', component_property='children'),
	Output(component_id='members_lapsed', component_property='children'),
	Output(component_id='membership_status', component_property='figure'),
	Output(component_id='membership_type', component_property='figure'),
	Output(component_id='union_member', component_property='figure'),
	Output(component_id='race', component_property='figure'),
	Output(component_id='membership_length', component_property='figure'),
	Input(component_id='list_dropdown', component_property='value')
)
def update_graph(date_selected):
	df = memb_lists[date_selected]
	df['membership_length'] = df['join_date'].apply(membership_length)
	df['membership_status'] = np.where(df['membership_status'] == 'expired', 'lapsed', df['membership_status'].str.lower())
	df['membership_type'] = np.where(df['xdate'] == '2099-11-01', 'lifetime', df['membership_type'].str.lower())
	if (not 'race' in df): df['race'] = 'unknown'

	lifetime = df['membership_type'].eq('lifetime').sum()
	num1 = f'Lifetime Members: {lifetime}'

	migs = df['membership_status'].eq('member in good standing').sum()
	num2 = f'Members in Good Standing: {migs}'

	expiring = df['membership_status'].eq('member').sum()
	num3 = f'Expiring Members: {expiring}'

	lapsed = df['membership_status'].eq('lapsed').sum()
	num4 = f'Lapsed Members: {lapsed}'

	colors1 = ['#ef4338', '#8a66c9', '#418e9d']
	chart1df_vc = df['membership_status'].value_counts()
	chart1 = go.Figure(data=[go.Bar(x=chart1df_vc.index, y=chart1df_vc.values, text=chart1df_vc.values, marker_color=colors1)])
	chart1.update_layout(title='Membership Counts (all-time)', yaxis_title='Members')

	colors2 = ['#ef4338', '#df4997', '#8a66c9', '#3989c4', '#418e9d']
	chart2df_vc = df.loc[df['membership_status'] == 'member in good standing']['membership_type'].value_counts()
	chart2 = go.Figure(data=[go.Bar(x=chart2df_vc.index, y=chart2df_vc.values, text=chart2df_vc.values, marker_color=colors2)])
	chart2.update_layout(title='Dues (members in good standing)', yaxis_title='Members')

	membersdf = df.loc[(df['membership_status'] != 'lapsed') & (df['membership_status'] != 'expired')]

	colors3 = ['#ef4338', '#df4997', '#8a66c9', '#3989c4', '#418e9d']
	chart3df_vc = membersdf['union_member'].value_counts()
	chart3 = go.Figure(data=[go.Bar(x=chart3df_vc.index, y=chart3df_vc.values, text=chart3df_vc.values, marker_color=colors3)])
	chart3.update_layout(title='Union Membership (not lapsed)', yaxis_title='Members')

	colors4 = ['#ef4338', '#ef3b71', '#d750a2', '#ac69c2', '#777ccf', '#4487c8', '#2b8db5', '#418e9d']
	chart4df_vc = splitDataFrameList(membersdf, 'race', ',')['race'].value_counts()
	chart4 = go.Figure(data=[go.Bar(x=chart4df_vc.index, y=chart4df_vc.values, text=chart4df_vc.values, marker_color=colors4)])
	chart4.update_yaxes(type="log")
	chart4.update_layout(title='Racial Demographics (self-reported)', yaxis_title='Members (Logarithmic)')

	colors5 = ['#ef4338', '#ef3b71', '#d750a2', '#ac69c2', '#777ccf', '#4487c8', '#2b8db5', '#418e9d']
	chart5df_vc = membersdf['membership_length'].clip(upper=8).value_counts()
	chart5 = go.Figure(data=[go.Bar(x=chart5df_vc.index, y=chart5df_vc.values, text=chart5df_vc.values, marker_color=colors5)])
	chart5.update_layout(title='Length of Membership (0 - 8+yrs, not lapsed)', yaxis_title='Members')

	return df.to_dict('records'), num1, num2, num3, num4, chart1, chart2, chart3, chart4, chart5

# Run the app
if __name__ == '__main__':
	app.run(debug=True)
