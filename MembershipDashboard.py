import os
import glob
import numpy as np
import zipfile
import pandas as pd
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

MEMB_LIST_NAME = 'maine_membership_list'
COLORS = ['#ee8cb5', '#c693be', '#937dc0', '#5fa3d9', '#00b2e2', '#54bcbb', '#69bca8', '#8dc05a', '#f9e442', '#f7ce63', '#f3aa79', '#f0959e']

memb_lists = {}
memb_lists_metrics = {}

def membership_length(date:str, **kwargs):
	return (pd.to_datetime(kwargs['list_date']) - pd.to_datetime(date)) // pd.Timedelta(days=365)

def fill_empties(date_formatted, column, default):
	if not column in memb_lists[date_formatted]: memb_lists[date_formatted][column] = default
	memb_lists[date_formatted][column] = memb_lists[date_formatted][column].fillna(default)

def data_fixes(date_formatted):
	memb_lists[date_formatted].columns = memb_lists[date_formatted].columns.str.lower()
	if not 'actionkit_id' in memb_lists[date_formatted]: memb_lists[date_formatted]['actionkit_id'] = memb_lists[date_formatted]['ak_id']
	if not 'actionkit_id' in memb_lists[date_formatted]: memb_lists[date_formatted]['actionkit_id'] = memb_lists[date_formatted]['akid']
	memb_lists[date_formatted].set_index('actionkit_id')
	memb_lists[date_formatted]['membership_length'] = memb_lists[date_formatted]['join_date'].apply(membership_length, list_date=date_formatted)
	if not 'membership_status' in memb_lists[date_formatted]: memb_lists[date_formatted]['membership_status'] = np.where(memb_lists[date_formatted]['memb_status'] == 'M', 'member in good standing', 'n/a')
	memb_lists[date_formatted]['membership_status'] = memb_lists[date_formatted]['membership_status'].replace({'expired': 'lapsed'}).str.lower()
	memb_lists[date_formatted]['membership_type'] = np.where(memb_lists[date_formatted]['xdate'] == '2099-11-01', 'lifetime', memb_lists[date_formatted]['membership_type'].str.lower())
	memb_lists[date_formatted]['membership_type'] = memb_lists[date_formatted]['membership_type'].replace({'annual': 'yearly'}).str.lower()
	fill_empties(date_formatted, 'do_not_call', False)
	fill_empties(date_formatted, 'p2ptext_optout', False)
	fill_empties(date_formatted, 'race', 'unknown')
	fill_empties(date_formatted, 'union_member', 'unknown')
	memb_lists[date_formatted]['union_member'] = memb_lists[date_formatted]['union_member'].replace({
		0: 'No',
		1: 'Yes',
		'Yes, retired union member': 'Yes, retired',
		'Yes, current union member': 'Yes, current',
		'Currently organizing my workplace': 'No, organizing',
		'No, but former union member': 'No, former',
		'No, not a union member': 'No'
	}).str.lower()
	fill_empties(date_formatted, 'accomodations', 'no')
	memb_lists[date_formatted]['accomodations'] = memb_lists[date_formatted]['accomodations'].str.lower().replace({
		'n/a': None,
		'no.': None,
		'no': None,
	})
	fill_empties(date_formatted, 'accommodations', 'no')
	memb_lists[date_formatted]['accommodations'] = memb_lists[date_formatted]['accommodations'].str.lower().replace({
		'n/a': None,
		'no.': None,
		'no': None,
	})

def scan_membership_list(filename: str, filepath: str):
	print(f'Scanning {filename} for membership list.')
	date_from_name = pd.to_datetime(os.path.splitext(filename)[0].split('_')[3], format='%Y%m%d').date()
	if not date_from_name:
		print('No date detected. Skipping file.')
		return

	with zipfile.ZipFile(filepath) as memb_list_zip:
		with memb_list_zip.open(f'{MEMB_LIST_NAME}.csv') as memb_list:
			date_formatted = date_from_name.isoformat()

			memb_lists[date_formatted] = pd.read_csv(memb_list, header=0)
			data_fixes(date_formatted)

			for column in memb_lists[date_formatted].columns:
				if not column in memb_lists_metrics: memb_lists_metrics[column] = {}
				memb_lists_metrics[column][date_formatted] = memb_lists[date_formatted][column]

def scan_all_membership_lists(directory:str):
	print(f'Scanning {directory} for zipped membership lists.')
	files = sorted(glob.glob(os.path.join(directory, '**/*.zip'), recursive=True), reverse=True)
	for count, file in enumerate(files):
		scan_membership_list(os.path.basename(file), os.path.abspath(file))
		if count > 10: break
	#[scan_membership_list(os.path.basename(file), os.path.abspath(file)) for file in files]

# Initialize the app
scan_all_membership_lists(MEMB_LIST_NAME)
app = Dash(
	external_stylesheets=[dbc.themes.DARKLY],
	# these meta_tags ensure content is scaled correctly on different devices
	# see: https://www.w3schools.com/css/css_rwd_viewport.asp for more
	meta_tags=[
		{"name": "viewport", "content": "width=device-width, initial-scale=1"}
	],
	suppress_callback_exceptions=True
)
load_figure_template(["darkly"])

# we use the Row and Col components to construct the sidebar header
# it consists of a title, and a toggle, the latter is hidden on large screens
sidebar_header = dbc.Row(
	[
		dbc.Col(html.H2("Maine DSA", className="display-4")),
		dbc.Col(
			[
				dbc.Button(
					# use the Bootstrap navbar-toggler classes to style
					html.Span(className="navbar-toggler-icon"),
					className="navbar-toggler",
					# the navbar-toggler classes don't set color
					style={
						"color": "rgba(0,0,0,.5)",
						"border-color": "rgba(0,0,0,.1)",
					},
					id="navbar-toggle",
				),
				dbc.Button(
					# use the Bootstrap navbar-toggler classes to style
					html.Span(className="navbar-toggler-icon"),
					className="navbar-toggler",
					# the navbar-toggler classes don't set color
					style={
						"color": "rgba(0,0,0,.5)",
						"border-color": "rgba(0,0,0,.1)",
					},
					id="sidebar-toggle",
				),
			],
			# the column containing the toggle will be only as wide as the
			# toggle, resulting in the toggle being right aligned
			width="auto",
			# vertically align the toggle in the center
			align="center",
		),
	]
)

sidebar = html.Div(
	[
		sidebar_header,
		# we wrap the horizontal rule and short blurb in a div that can be
		# hidden on a small screen
		html.Div(
			[
				html.Hr(),
				html.P("Membership Dasboard", className="lead"),
			],
			id="blurb",
		),
		dcc.Dropdown(options=list(memb_lists.keys()), value=list(memb_lists.keys())[0], id='list_dropdown', className="dash-bootstrap"),
		html.Div(
			[
				html.P("Active List"),
			],
			id="list_dropdown_label",
		),
		dcc.Dropdown(options=list(memb_lists.keys()), value='', id='list_compare_dropdown', className="dash-bootstrap"),
		html.Div(
			[
				html.P("Compare To"),
			],
			id="list_compare_dropdown_label",
		),
		# use the Collapse component to animate hiding / revealing links
		dbc.Collapse(
			dbc.Nav(
				[
					dbc.NavLink("Timeline", href="/", active="exact"),
					dbc.NavLink("List", href="/list", active="exact"),
					dbc.NavLink("Metrics", href="/metrics", active="exact"),
					dbc.NavLink("Graphs", href="/graphs", active="exact"),
					dbc.NavLink("Map", href="/map", active="exact"),
				],
				vertical=True,
				pills=True,
			),
			id="collapse",
		),
	],
	id="sidebar",
)

content = html.Div(id="page-content")

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

timeline = html.Div(id='timeline-container', children=[
	dcc.Dropdown(options=list(memb_lists_metrics.keys()), value=['membership_status'], multi=True, id='timeline_columns', className="dash-bootstrap"),
	dcc.Graph(figure={}, id='membership_timeline', className="dash-bootstrap", style={
		'display': 'inline-block',
		'width': '100%',
		'padding-left': '-1em',
		'padding-right': '-1em',
		'padding-bottom': '-1em'
		}
	),
])

member_list_page = html.Div(id='list-container', className="dbc", children=[
	dash_table.DataTable(
		data=memb_lists[list(memb_lists.keys())[0]].to_dict('records'),
		columns=[
			{'name': i, 'id': i, 'selectable': True} for i in memb_lists[list(memb_lists.keys())[0]].columns
		],
		sort_action="native",
		sort_by=[{'column_id': 'last_name', 'direction': 'asc'},{'column_id': 'first_name', 'direction': 'asc'}],
		filter_action='native',
		filter_options={'case': 'insensitive'},
		export_format='csv',
		page_size=20,
		style_table={'overflowY': 'auto', 'overflowX': 'auto', 'padding-left': '-.5em'},
		id='membership_list',
	),
])

def create_jumbotron(title, id):
  return dbc.Col(
	html.Div(
	  [
		html.H3(title, className="display-8"),
		html.Hr(className="my-2"),
		html.P("0", id=id),
	  ],
	  className="h-100 p-5 text-white bg-dark rounded-3",
	),
	md=6,
  )

const_jumbotron = create_jumbotron("Constitutional Members", "members_constitutional")
migs_jumbotron = create_jumbotron("Members in Good Standing", "members_migs")
expiring_jumbotron = create_jumbotron("Expiring Members", "members_expiring")
lapsed_jumbotron = create_jumbotron("Lapsed Members", "members_lapsed")

metrics = dbc.Col(
	[
		dbc.Row(
			[const_jumbotron, migs_jumbotron],
			className="align-items-md-stretch"
		),
		dbc.Row(
			[expiring_jumbotron, lapsed_jumbotron],
			className="align-items-md-stretch"
		),
	], className="d-grid gap-4"
)

	
style_graphs_2 = {'display': 'inline-block', 'width': '50%'}
style_graphs_3 = {'display': 'inline-block', 'width': '33.33%'}

graphs = html.Div(id='graphs-container', children=[
	dcc.Graph(figure={}, id='membership_status', className="dash-bootstrap", style=style_graphs_3),
	dcc.Graph(figure={}, id='membership_type', className="dash-bootstrap", style=style_graphs_3),
	dcc.Graph(figure={}, id='union_member', className="dash-bootstrap", style=style_graphs_3),
	dcc.Graph(figure={}, id='membership_length', className="dash-bootstrap", style=style_graphs_2),
	dcc.Graph(figure={}, id='race', className="dash-bootstrap", style=style_graphs_2),
])

def selectedData(date_selected:str):
	return memb_lists[date_selected] if date_selected else pd.DataFrame()

## Pages

@callback(
	Output(component_id='membership_timeline', component_property='figure'),
	Input(component_id='timeline_columns', component_property='value'),
)
def update_timeline(selected_columns):
	timeline = go.Figure()
	selected_metrics = {}
	for selected_column in selected_columns:
		selected_metrics[selected_column] = {}
		for date in memb_lists_metrics[selected_column]:
			value_counts = memb_lists_metrics[selected_column][date].value_counts()
			for value in value_counts.keys():
				if not value in selected_metrics[selected_column]: selected_metrics[selected_column][value] = {}
				selected_metrics[selected_column][value][date] = value_counts[value]
		for column in selected_metrics:
			for count, value in enumerate(selected_metrics[column]):
				timeline.add_trace(go.Scatter(
					name=value,
					x=list(selected_metrics[column][value].keys()),
					y=list(selected_metrics[column][value].values()),
					mode='lines',
					marker_color=COLORS[count % len(COLORS)]
				))
	timeline.update_layout(title='Membership Trends Timeline', yaxis_title='Members')

	return timeline

@callback(
	Output(component_id='membership_list', component_property='data'),
	Input(component_id='list_dropdown', component_property='value'),
	Input(component_id='list_compare_dropdown', component_property='value')
)
def update_list(date_selected, date_compare_selected):
	df = selectedData(date_selected)
	df_compare = selectedData(date_compare_selected)

	return df.to_dict('records')

@callback(
	Output(component_id='members_constitutional', component_property='children'),
	Output(component_id='members_migs', component_property='children'),
	Output(component_id='members_expiring', component_property='children'),
	Output(component_id='members_lapsed', component_property='children'),
	Input(component_id='list_dropdown', component_property='value'),
	Input(component_id='list_compare_dropdown', component_property='value')
)
def update_metrics(date_selected, date_compare_selected):
	df = selectedData(date_selected)
	df_compare = selectedData(date_compare_selected)

	def calculateMetric(df, df_compare, column:str, value:str):
		count = df[column].eq(value).sum()
		if not df_compare.empty:
			count_compare = df_compare[column].eq(value).sum()
			count_delta = count - count_compare
			if count_delta > 0:
				return f'{count} (+{count_delta})'
			elif count_delta < 0:
				return f'{count} ({count_delta})'
		return f'{count}'

	num1 = calculateMetric(df, df_compare, 'membership_type', 'lifetime')
	num2 = calculateMetric(df, df_compare, 'membership_status', 'member in good standing')
	num3 = calculateMetric(df, df_compare, 'membership_status', 'member')
	num4 = calculateMetric(df, df_compare, 'membership_status', 'lapsed')

	return num1, num2, num3, num4

@callback(
	Output(component_id='membership_status', component_property='figure'),
	Output(component_id='membership_type', component_property='figure'),
	Output(component_id='union_member', component_property='figure'),
	Output(component_id='membership_length', component_property='figure'),
	Output(component_id='race', component_property='figure'),
	Input(component_id='list_dropdown', component_property='value'),
	Input(component_id='list_compare_dropdown', component_property='value')
)
def update_graph(date_selected, date_compare_selected):
	df = selectedData(date_selected)
	df_compare = selectedData(date_compare_selected)

	def createChart(df_field, df_compare_field, title:str, ylabel:str, log:bool):
		chartdf_vc = df_field.value_counts()
		chartdf_compare_vc = df_compare_field.value_counts()

		color, color_compare = COLORS, COLORS
		active_labels = [str(val) for val in chartdf_vc.values]
		
		if not df_compare_field.empty:
			color, color_compare = COLORS[0], COLORS[5]
			active_labels = [
				f"{count} (+{count - chartdf_compare_vc.get(val, 0)})"
				if count - chartdf_compare_vc.get(val, 0) > 0
				else f"{count} ({count - chartdf_compare_vc.get(val, 0)})"
				for val, count in zip(chartdf_vc.index, chartdf_vc.values)
			]

		chart = go.Figure(data=[
			go.Bar(name='Compare List', x=chartdf_compare_vc.index, y=chartdf_compare_vc.values, text=chartdf_compare_vc.values, marker_color=color_compare),
			go.Bar(name='Active List', x=chartdf_vc.index, y=chartdf_vc.values, text=active_labels, marker_color=color)
		])
		if log:
			chart.update_yaxes(type="log")
			ylabel = ylabel + ' (Logarithmic)'
		chart.update_layout(title=title, yaxis_title=ylabel)
		return chart

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
		'Members',
		True
	)

	membersdf = df.query('membership_status != "lapsed" and membership_status != "expired"')
	membersdf_compare = df_compare.query('membership_status != "lapsed" and membership_status != "expired"') if 'membership_status' in df_compare else pd.DataFrame()

	chart3 = createChart(
		membersdf['union_member'] if 'union_member' in df else pd.DataFrame(),
		membersdf_compare['union_member'] if 'union_member' in df_compare else pd.DataFrame(),
		'Union Membership (not lapsed)',
		'Members',
		True
	)

	chart4 = createChart(
		membersdf['membership_length'].clip(upper=8) if 'membership_length' in df else pd.DataFrame(),
		membersdf_compare['membership_length'].clip(upper=8) if 'membership_length' in membersdf_compare else pd.DataFrame(),
		'Length of Membership (0 - 8+yrs, not lapsed)',
		'Members',
		False
	)
	
	def multiChoiceCount(df,target_column:str,separator:str):
		return df[target_column].str.split(separator, expand=True).stack().reset_index(level=1, drop=True).to_frame(target_column).join(df.drop(target_column, axis=1))

	chart5 = createChart(
		multiChoiceCount(membersdf, 'race', ',')['race'] if 'race' in df else pd.DataFrame(),
		multiChoiceCount(membersdf_compare, 'race', ',')['race'] if 'race' in membersdf_compare else pd.DataFrame(),
		'Racial Demographics (self-reported)',
		'Members',
		True
	)

	return chart1, chart2, chart3, chart4, chart5

## Sidebar

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
	if pathname == "/":
		return timeline
	elif pathname == "/list":
		return member_list_page
	elif pathname == "/metrics":
		return metrics
	elif pathname == "/graphs":
		return graphs
	elif pathname == "/map":
		return html.P("Oh cool, this is page 4!")
	# If the user tries to reach a different page, return a 404 message
	return html.Div(
		[
			html.H1("404: Not found", className="text-danger"),
			html.Hr(),
			html.P(f"The pathname {pathname} was not recognised..."),
		],
		className="p-3 bg-light rounded-3",
	)


@app.callback(
	Output("sidebar", "className"),
	[Input("sidebar-toggle", "n_clicks")],
	[State("sidebar", "className")],
)
def toggle_classname(n, classname):
	if n and classname == "":
		return "collapsed"
	return ""


@app.callback(
	Output("collapse", "is_open"),
	[Input("navbar-toggle", "n_clicks")],
	[State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
	if n:
		return not is_open
	return is_open


if __name__ == "__main__":
	app.run_server(debug=True)