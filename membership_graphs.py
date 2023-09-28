import os
import zipfile
import pandas as pd
import datetime
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.graph_objects as go
import numpy as np
import glob

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

def membership_length(date:str, **kwargs):
	return (pd.to_datetime(kwargs['list_date'], format='ISO8601') - pd.to_datetime(date, format='ISO8601')) // datetime.timedelta(days=365)

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
	dcc.Dropdown(options=memb_list_dates, value='', id='list_compare_dropdown'),
	dash_table.DataTable(
		data=memb_lists[memb_list_dates[0]].to_dict('records'),
		columns=[
			{'name': i, 'id': i, 'deletable': True} for i in memb_lists[memb_list_dates[0]].columns
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

def selectedData(date_selected:str):
	df = memb_lists[date_selected] if date_selected else pd.DataFrame()
	if date_selected:
		df.columns = df.columns.str.lower()
		df['membership_length'] = df['join_date'].apply(membership_length, list_date=date_selected)
		df['membership_status'] = df['membership_status'].replace({'expired': 'lapsed'}).str.lower()
		df['membership_type'] = np.where(df['xdate'] == '2099-11-01', 'lifetime', df['membership_type'].str.lower())
		df['race'] = df.get('race', 'unknown')
		df['race'] = df['race'].fillna('unknown')
	return df

def calculateMetric(df, df_compare, title:str, column:str, value:str):
	count = df[column].eq(value).sum()
	num = f'{title}{count}'
	if not df_compare.empty:
		count_compare = df_compare[column].eq(value).sum()
		if count > count_compare:
			return f'{num} (+{count-count_compare})'
		elif count < count_compare:
			return f'{num} (-{count_compare-count})'
	return num

COLORS = ['#f7ce63', '#f3aa79', '#f0959e', '#ee8cb5', '#c693be', '#937dc0', '#5fa3d9', '#00b2e2', '#54bcbb', '#69bca8', '#8dc05a', '#f9e442']
def createChart(df_field, df_compare_field, title:str, ylabel:str, log:bool):
	chartdf_vc = df_field.value_counts()
	chartdf_compare_vc = df_compare_field.value_counts()

	color, color_compare = COLORS, COLORS
	if not df_compare_field.empty:
		color, color_compare = COLORS[3], COLORS[8]

	chart = go.Figure(data=[
		go.Bar(name='Compare List', x=chartdf_compare_vc.index, y=chartdf_compare_vc.values, text=chartdf_compare_vc.values, marker_color=color_compare),
		go.Bar(name='Active List', x=chartdf_vc.index, y=chartdf_vc.values, text=chartdf_vc.values, marker_color=color)
	])
	if log: chart.update_yaxes(type="log")
	chart.update_layout(title=title, yaxis_title=ylabel)
	return chart
	
def multiChoiceCount(df,target_column:str,separator:str):
	return df[target_column].str.split(separator, expand=True).stack().reset_index(level=1, drop=True).to_frame(target_column).join(df.drop(target_column, axis=1))

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
	Input(component_id='list_dropdown', component_property='value'),
	Input(component_id='list_compare_dropdown', component_property='value')
)
def update_graph(date_selected, date_compare_selected):
	df = selectedData(date_selected)
	df_compare = selectedData(date_compare_selected)

	num1 = calculateMetric(df, df_compare, 'Lifetime Members: ', 'membership_type', 'lifetime')
	num2 = calculateMetric(df, df_compare, 'Members in Good Standing: ', 'membership_status', 'member in good standing')
	num3 = calculateMetric(df, df_compare, 'Expiring Members: ', 'membership_status', 'member')
	num4 = calculateMetric(df, df_compare, 'Lapsed Members: ', 'membership_status', 'lapsed')

	chart1 = createChart(
		df['membership_status'] if 'membership_status' in df else pd.DataFrame(),
		df_compare['membership_status'] if 'membership_status' in df_compare else pd.DataFrame(),
		'Membership Counts (all-time)',
		'Members',
		False
	)

	chart2 = createChart(
		df.loc[df['membership_status'] == 'member in good standing']['membership_type'] if 'membership_status' in df else pd.DataFrame(),
		df_compare.loc[df_compare['membership_status'] == 'member in good standing']['membership_type'] if 'membership_status' in df_compare else pd.DataFrame(),
		'Dues (members in good standing)',
		'Members (Logarithmic)',
		True
	)

	membersdf = df.query('membership_status != "lapsed" and membership_status != "expired"')
	membersdf_compare = df_compare.query('membership_status != "lapsed" and membership_status != "expired"') if 'membership_status' in df_compare else pd.DataFrame()

	chart3 = createChart(
		membersdf['union_member'] if 'union_member' in df else pd.DataFrame(),
		membersdf_compare['union_member'] if 'union_member' in df_compare else pd.DataFrame(),
		'Union Membership (not lapsed)',
		'Members (Logarithmic)',
		True
	)

	chart4 = createChart(
		multiChoiceCount(membersdf, 'race', ',')['race'] if 'race' in df else pd.DataFrame(),
		multiChoiceCount(membersdf_compare, 'race', ',')['race'] if 'race' in membersdf_compare else pd.DataFrame(),
		'Racial Demographics (self-reported)',
		'Members (Logarithmic)',
		True
	)

	chart5 = createChart(
		membersdf['membership_length'].clip(upper=8) if 'membership_length' in df else pd.DataFrame(),
		membersdf_compare['membership_length'].clip(upper=8) if 'membership_length' in membersdf_compare else pd.DataFrame(),
		'Length of Membership (0 - 8+yrs, not lapsed)',
		'Members',
		False
	)

	return df.to_dict('records'), num1, num2, num3, num4, chart1, chart2, chart3, chart4, chart5

# Run the app
if __name__ == '__main__':
	app.run(debug=True)
