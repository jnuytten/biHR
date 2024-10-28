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
# This file contains structure and functions to display the company forecast page.
#

from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
from app import app, global_dataframes
import configparser
from datetime import datetime
from src.utils import main_functions

# load configuration parameters
g_config = configparser.ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
g_config.read('config.ini')

ref_date = datetime(g_config.getint('PARAMETERS', 'year'), g_config.getint('PARAMETERS',
                                                                           'month'), 1)
company_forecast, monthly_employee_data, monthly_freelance_data = main_functions.company_year_forecast(g_config, ref_date)
# reset index so that it is displayed in the table
company_forecast.reset_index(inplace=True)

#todo: dropdown is defined but not showing anything on page when a month is selected

# layout of the page
layout = html.Div([
    html.H1("Simulatie bedrijf"),
    dash_table.DataTable(
        id='table-company_year',
        columns=[{'name': col, 'id': col} for col in company_forecast.columns],
        data=company_forecast.to_dict('records')
    ),
    dcc.Dropdown(
        id='month-dropdown',
        options=[{'label': row[0], 'value': row[0]} for row in company_forecast.itertuples(index=False)],
        placeholder="Select a month"
    ),
    html.Div(id='monthly-data')
])

@app.callback(
    Output('monthly-data', 'children'),
    Input('month-dropdown', 'value')
)
def update_monthly_data(selected_month):
    if selected_month is None:
        return html.Div("Please select a month.")

    # Filter the data for the selected month
    #DEBUG fixed index 11
    #todo fix index
    employee_data = monthly_employee_data[11]
    freelance_data = monthly_freelance_data[11]

    return html.Div([
        html.H2(f"Data for {selected_month}"),
        html.H3("Employee Data"),
        dash_table.DataTable(
            columns=[{'name': col, 'id': col} for col in employee_data.columns],
            data=employee_data.to_dict('records')
        ),
        html.H3("Freelance Data"),
        dash_table.DataTable(
            columns=[{'name': col, 'id': col} for col in freelance_data.columns],
            data=freelance_data.to_dict('records')
        )
    ])


#layout = html.Div([
#    html.H1("Page 1 - Cost Frame"),
#    dash_table.DataTable(
#        id='table-cost_frame',
#        columns=[{'name': col, 'id': col, 'editable': True} for col in cost_frame.columns],
#        data=cost_frame.to_dict('records'),
#        editable=True
#    ),
#    dcc.Graph(id='graph-cost_frame')
#])

#@app.callback(
#    Output('graph-cost_frame', 'figure'),
#    Input('table-cost_frame', 'data')
#)
#def update_graph_cost_frame(data):
#    df = pd.DataFrame(data)
#    fig = px.line(df, x='A', y='B', title='Cost frame Visualization')
#    return fig