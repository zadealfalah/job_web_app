
import os
import ast
from dash import Dash, dcc, html, Input, Output, State
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objs as go

from dotenv import load_dotenv

load_dotenv()

# Retrieve the keyword list from the environment variable
keyword_list = json.loads(os.getenv("keyword_list"))
# print(f"Keyword list: {keyword_list}")

# Create a Dash web application
app = Dash(__name__)

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



# Define the layout of your app
app.layout = html.Div([
    html.H1("Indeed Jobs By Day"),
    dcc.DatePickerRange(
        id='date-range-selector',
        start_date=min(data.keys()),  # Set the minimum date
        end_date=max(data.keys()),    # Set the maximum date
    ),
    dcc.Dropdown(
        id='term-selector',
        options=[{'label': term.title(), 'value': term} for term in keyword_list],
        multi=True,  # Allow multiple selections
        value=keyword_list  # Select all terms by default
    ),
    dcc.Graph(id='line-graph'),
    html.Button(
        id='reset-button',
        n_clicks=0,
        children='Reset Date Range'
    )
])

# Define callback to update the line graph
@app.callback(
    Output('line-graph', 'figure'),
    Input('term-selector', 'value'),
    Input('date-range-selector', 'start_date'),
    Input('date-range-selector', 'end_date'),
    Input('reset-button', 'n_clicks'),
    State('date-range-selector', 'start_date'),
    State('date-range-selector', 'end_date')
)
def update_line_graph(selected_terms, start_date, end_date, reset_button_clicks, initial_start_date, initial_end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    # Check if the reset button was clicked and reset the date range
    if reset_button_clicks > 0:
        start_date = datetime.strptime(initial_start_date, '%Y-%m-%d')
        end_date = datetime.strptime(initial_end_date, '%Y-%m-%d')
        

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
