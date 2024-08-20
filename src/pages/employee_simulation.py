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

from dash import dcc, html, dash_table, Input, Output, callback
import plotly.express as px
import pandas as pd
import configparser
from datetime import datetime
from app import app, global_dataframes
from src.utils import calculate_employee, db_supply

# load configuration parameters
g_config = configparser.ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
g_config.read('config.ini')

ref_date = datetime(g_config.getint('PARAMETERS', 'year'), g_config.getint('PARAMETERS',
                                                                           'month'), 1)
# generate page specific dataframes
employee_df = db_supply.worker_list_get('intern', ref_date)
employee_df.sort_values(by='name', inplace=True)
employee_df.reset_index(inplace=True) # Reset index to ensure 'id' column is accessible
employee_id = employee_df['id'].iloc[0] # default employee id
cost_overview, yearly_revenue, parameters = calculate_employee.yearly_cost_income(
    g_config, employee_id, ref_date
)
# Transpose the dataframe
cost_overview_transposed = cost_overview.transpose().reset_index()
cost_overview_transposed.columns = ['Onkost', 'Bedrag']

# todo: insert a separate empty table for parameter overwrites, don't do that in the parameter table itself because it will get complicated

layout = html.Div([
    html.H1("Simulatie werknemer"),
    dcc.Dropdown(
        id='employee-dropdown',
        options=[{'label': str(row['id']) + ' - ' + row['name'], 'value': row['id']} for index, row in employee_df.iterrows()],
        value=employee_id  # Default value
    ),
    html.P(id='employee-info'),
    html.Br(),
    html.H3("Parameters berekening"),
    dash_table.DataTable(
        id='table-parameters',
        columns=[{'name': col, 'id': col, 'editable': True} for col in parameters.columns],
        data=parameters.to_dict('records'),
        editable=True
    ),
    html.H3("Overzicht kosten"),
    dash_table.DataTable(
        id='table-cost_overview',
        columns=[{'name': col, 'id': col, 'editable': True} for col in cost_overview_transposed.columns],
        data=cost_overview_transposed.to_dict('records'),
        editable=True
    ),
    html.P(id='yearly-revenue')
])

def register_callbacks(app):
    @app.callback(
        [Output('employee-info', 'children'),
         Output('table-parameters', 'data'),
         Output('table-cost_overview', 'data'),
         Output('yearly-revenue', 'children')],
        Input('employee-dropdown', 'value')
    )
    def update_employee_info(selected_employee_id):
        if selected_employee_id is None:
            print("No employee ID selected")  # Debug statement
            return ("No employee selected", [], [], "No revenue data")
        cost_overview, yearly_revenue, parameters = calculate_employee.yearly_cost_income(g_config, selected_employee_id, ref_date)
        cost_overview_transposed = cost_overview.transpose().reset_index()
        cost_overview_transposed.columns = ['Onkost', 'Bedrag']
        return (f"Simulatie wordt getoond voor werknemer {selected_employee_id}",
                parameters.to_dict('records'),
                cost_overview_transposed.to_dict('records'),
                f"Yearly revenue is {yearly_revenue}")