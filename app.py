
import os
# import ast
from dash import Dash, dcc, html, Input, Output, State
import json
from datetime import datetime
# from dateutil.relativedelta import relativedelta
import plotly.graph_objs as go

import dash_bootstrap_components as dbc

from dotenv import load_dotenv

load_dotenv()

# Retrieve the keyword list from the environment variable
keyword_list = json.loads(os.getenv("keyword_list"))
# print(f"Keyword list: {keyword_list}")


# Read data from JSON files in the 'data' folder
data_folder = os.getenv("datapath")
# print(f"data_folder: {data_folder}")
json_files = [f for f in os.listdir(data_folder) if f.startswith('p-raw_data-') and f.endswith('.json')]
# print(f"Json files: {json_files}")
data = {}

for file in json_files:
    file_name = os.path.splitext(file)[0]  # Remove the '.json' extension
    date_parts = file_name.split('-')[-3:]  # Extract the date parts from the file name
    date_str = '-'.join(date_parts)  # Construct a date string
    file_date = datetime.strptime(date_str, '%d-%m-%y')  # Convert to a datetime object
    file_date_str = file_date.strftime('%Y-%m-%d')  # Convert back to a string for consistency
    with open(os.path.join(data_folder, file), 'r') as f:
        data[file_date_str] = json.load(f)
# print(data['2023-10-30'])
# Process the data to count the number of job_id entries by day
job_count_by_day = {}

for date, entries in data.items():
    job_count_by_day[date] = len(entries)







# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}



app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY],
                           meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
            )

# Create sidebar card
sidebar = dbc.Card([
    dbc.Button(
        "Toggle Nav Bar",
        id="collapse-nav-button",
        className="mb-3",
        n_clicks=0,
        ),
    dbc.Collapse(
        dbc.CardBody([
            # html.H2("Navigation", className="display-4"),
            html.Hr(),
            html.P("Page Selection", className="text-center"),
            dbc.Nav(
                [
                    dbc.NavLink("Home" ,href="/", active="exact"),
                    dbc.NavLink("Indeed Jobs Graph" ,href="/page-2", active="exact"),
                    dbc.NavLink("Page 3 - WIP" ,href="/page-3", active="exact"),
                ],
                vertical=True,
                pills=True
            )
        ]),
        id="collapse-nav",
        is_open=False,
        )
], color="light", style={"height":"100vh",
                         "width":"16rem", 
                         "position":"fixed"}
)

@app.callback(
    Output("collapse-nav", "is_open"),
    [Input("collapse-nav-button", "n_clicks")],
    [State("collapse-nav", "is_open")],
)
def toggle_collapse_nav(n, is_open):
    if n:
        return not is_open
    return is_open

content = html.Div(id="page-content")

# Overall App Layout
app.layout = dbc.Container([
        dcc.Location(id='url'),
        dbc.Row([
            dbc.Col(sidebar,width=2),
            dbc.Col(content)
        ])
    ], fluid=True
)

# # Define the layout for the home page
home_layout = dbc.Container(
    [
        dbc.Container(
            [
                html.H1("Job Requirements Analysis", className="text-center")
            ],
            fluid=True,
        ),
    ],
    fluid=True,
)

# Page2 layout for jobs over time graph
page2_layout = dbc.Container(
    [
        dbc.Container(
            [
                html.H1("Indeed Jobs By Day", className='display-4 mb-4'),
                dcc.DatePickerRange(
                    id='date-range-selector',
                    start_date=min(data.keys()),  # Set the minimum date
                    end_date=max(data.keys()),    # Set the maximum date
                    className='form-control mb-3'
                ),
                dcc.Dropdown(
                    id='term-selector',
                    options=[{'label': term.title(), 'value': term} for term in keyword_list],
                    multi=True,  # Allow multiple selections
                    value=keyword_list  # Select all terms by default
                ),
                dcc.Graph(id='line-graph', className='mb-3'),
            ],
            fluid=True,
        ),
    ],
    fluid=True,
)



# # Define the layout for the third page (blank for now)
# page3_layout = html.Div([
#     html.H1("This is Page 3 (Blank for Now)"),
#     # dcc.Link('Go to Page 2', href='/page-2')
# ])



# Define callback to update the page content based on the URL
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return home_layout
    elif pathname == "/page-2":
        return page2_layout
    # elif pathname == "/page-3":
    #     return page3_layout
    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )


# Define callback to update the line graph
@app.callback(
    Output('line-graph', 'figure'),
    Input('term-selector', 'value'),
    Input('date-range-selector', 'start_date'),
    Input('date-range-selector', 'end_date'),
)
def update_line_graph(selected_terms, start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')


    data_to_plot = []

    x_values = sorted([date for date in data if start_date <= datetime.strptime(date, '%Y-%m-%d') <= end_date])

    for term in selected_terms:
        y_values = []
        for date in x_values:
            count = 0
            for entry in data[date].values():
                terms = entry.get('terms', [])
                if term in terms:
                    count += 1
            y_values.append(count)

        trace = go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name=term,
        )
        data_to_plot.append(trace)

    layout = go.Layout(
        title='Job Counts by Day',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Number of Unique Jobs'),
        xaxis_rangeslider=dict(
            visible=False,
        ),
    )

    layout['xaxis']['range'] = [start_date, end_date]

    return {'data': data_to_plot, 'layout': layout}







# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
