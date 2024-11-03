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

import dash
from dash import dcc, html, dash_table, Input, Output, callback
import pandas as pd
import configparser
from datetime import datetime
from src.utils import calculate_employee, db_supply

dash.register_page(__name__, path='/employee_simulation')

def get_employee_data(employee_id):
    cost_overview, yearly_revenue, parameters = calculate_employee.yearly_cost_income(g_config, employee_id, ref_date)
    # calculate yearly cost and margin
    yearly_cost = float(cost_overview.sum().sum())
    yearly_gross_margin = yearly_revenue - yearly_cost
    yearly_margin_percentage = yearly_gross_margin / yearly_revenue * 100
    # transpose the cost_overview dataframe for better display
    cost_overview_transposed = cost_overview.transpose().reset_index()
    cost_overview_transposed.columns = ['Onkost', 'Bedrag']
    # create summary dataframe
    summary = pd.DataFrame({
        'Jaarlijkse omzet': [round(yearly_revenue,2)],
        'Jaarlijkse kosten': [round(yearly_cost,2)],
        'Jaarlijkse brutowinst': [round(yearly_gross_margin,2)],
        'Brutowinstpercentage': [str(round(yearly_margin_percentage,2)) + "%"]
    })
    return cost_overview_transposed, summary, parameters

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

# initial data setup (showing default employee)
cost_overview_transposed, summary, parameters = get_employee_data(employee_id)

# layout of the page
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
        columns=[{'name': col, 'id': col} for col in parameters.columns],
        data=parameters.to_dict('records')
    ),
    html.H3("Overzicht kosten"),
    dash_table.DataTable(
        id='table-cost_overview',
        columns=[{'name': col, 'id': col} for col in cost_overview_transposed.columns],
        data=cost_overview_transposed.to_dict('records'),
    ),
    html.H3("Synthese"),
    dash_table.DataTable(
        id='table-summary',
        columns=[{'name': col, 'id': col} for col in summary.columns],
        data=summary.to_dict('records'),
    )
])

@callback(
    [Output('employee-info', 'children'),
     Output('table-parameters', 'data'),
     Output('table-cost_overview', 'data'),
     Output('table-summary', 'data')],
    Input('employee-dropdown', 'value')
    )
def update_employee_info(selected_employee_id):
    if selected_employee_id is None:
        return ("No employee selected", [], [], "No revenue data")
    cost_overview_transposed, summary, parameters = get_employee_data(selected_employee_id)
    return (f"Simulatie wordt getoond voor werknemer {selected_employee_id}",
            parameters.to_dict('records'),
            cost_overview_transposed.to_dict('records'),
            summary.to_dict('records')
            )