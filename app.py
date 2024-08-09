# biHR does data analysis of cost, income and margin of a consultancy company, or other company working with
# daily or hourly rates. The data is retrieved from the Officient API and CSV files, and stored in a MySQL database.
#
# Copyright (C) 2024 Joachim Nuyttens
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.  If not, see
# <https://www.gnu.org/licenses/>.
#
#
# This file is used to start the Dash app and contains the main layout and callbacks.
#

import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import locale
import configparser
from datetime import datetime
import plotly.express as px
from src.utils import calculate_employee, gen_helpers as gh, main_functions

### LOAD GENERAL SETTINGS ###
#############################

locale.setlocale(locale.LC_ALL, "nl_BE.utf8")

# load configuration parameters
g_config = configparser.ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
g_config.read('config.ini')

# date that acts as reference point for the calculation
ref_date = datetime(g_config.getint('PARAMETERS', 'year'), g_config.getint('PARAMETERS',
                                                                           'month'), 1)

## LOAD ESSENTIAL DATA ##
###############################
# load all global dataframes with data from SQL database
main_functions.load_dataframes(ref_date, g_config)

### INITIALIZE DASH APP ###
###########################

app = dash.Dash(__name__)


cost_frame, revenue_frame = calculate_employee.get_monthly_summary_data(ref_date)
#df1 = data_processing.get_data_frame_1()
#df2 = data_processing.get_data_frame_2()

app.layout = html.Div([
    html.H1(f"Maandoverzicht {gh.get_month_name(ref_date.month)}"),
    dash_table.DataTable(
        id='table-cost_frame',
        columns=[{'name': col, 'id': col, 'editable': True} for col in cost_frame.columns],
        data=cost_frame.to_dict('records'),
        editable=True
    ),
    dcc.Graph(id='graph-cost_frame'),

    html.Hr(),

    dash_table.DataTable(
        id='table-revenue_frame',
        columns=[{'name': col, 'id': col, 'editable': True} for col in revenue_frame.columns],
        data=revenue_frame.to_dict('records'),
        editable=True
    ),
    dcc.Graph(id='graph-revenue_frame')
])

@app.callback(
    Output('graph-cost_frame', 'figure'),
    Input('table-cost_frame', 'data')
)

def update_graph_cost_frame(data):
    df = pd.DataFrame(data)
    fig = px.line(df, x='A', y='B', title='Cost frame Visualization')
    return fig

@app.callback(
    Output('graph-revenue_frame', 'figure'),
    Input('table-revenue_frame', 'data')
)
def update_graph_revenue_frame(data):
    df = pd.DataFrame(data)
    fig = px.line(df, x='X', y='Y', title='Revenue frame Visualization')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
