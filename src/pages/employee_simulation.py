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
# This file contains structure and functions to display the employee simulation page.
#

from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
import pandas as pd
import configparser
from datetime import datetime
from app import app, global_dataframes
from src.utils import calculate_employee

# load configuration parameters
g_config = configparser.ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
g_config.read('config.ini')

# generate page specific dataframes
ref_date = datetime(g_config.getint('PARAMETERS', 'year'), g_config.getint('PARAMETERS',
                                                                           'month'), 1)  # Define or import the reference date
employee_id = 95126
cost_overview, yearly_revenue, parameters = calculate_employee.yearly_cost_income(
    g_config, employee_id, ref_date
)
# Transpose the dataframe
cost_overview_transposed = cost_overview.transpose().reset_index()
cost_overview_transposed.columns = ['Onkost', 'Bedrag']

layout = html.Div([
    html.H1("Employee simulation"),
    dash_table.DataTable(
        id='table-parameters',
        columns=[{'name': col, 'id': col, 'editable': True} for col in parameters.columns],
        data=parameters.to_dict('records'),
        editable=True
    ),
    dash_table.DataTable(
        id='table-cost_overview',
        columns=[{'name': col, 'id': col, 'editable': True} for col in cost_overview_transposed.columns],
        data=cost_overview_transposed.to_dict('records'),
        editable=True
    ),
    html.P("Yearly revenue is " + str(yearly_revenue))
])

# Set the layout for the employee simulation page
app.Layout = layout

#@app.callback(
#    Output('graph-revenue_frame', 'figure'),
#    Input('table-revenue_frame', 'data')
#)

#def update_graph_revenue_frame(data):
#    df = pd.DataFrame(data)
#    fig = px.line(df, x='X', y='Y', title='Revenue frame Visualization')
#    return fig