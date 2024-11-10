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
# This file contains structure and functions to display the employee monthly cost forecast.
#

import dash
import pandas as pd
from dash import dcc, html, dash_table, callback, Input, Output
from src.utils import config
from src.utils import main_functions

dash.register_page(__name__, path='/employee_monthly_cost')

ref_date = config.g_ref_date
month_mapping = {
    'januari': 1,
    'februari': 2,
    'maart': 3,
    'april': 4,
    'mei': 5,
    'juni': 6,
    'juli': 7,
    'augustus': 8,
    'september': 9,
    'oktober': 10,
    'november': 11,
    'december': 12
}


# we need to get company_forecast just as a means to get the required months for the dropdown
company_forecast, monthly_employee_data, monthly_freelance_data = main_functions.company_year_forecast()
# reset index so that this works correctly to get the months
company_forecast.reset_index(inplace=True)
# select the first month in company_forecast as default
selected_month = company_forecast['index'].iloc[0]

employee_monthly_cost = main_functions.employee_month_forecast(ref_date)

# layout of the page
layout = html.Div([
    html.H1("Detail werknemerskosten"),
    html.Br(),
    dcc.Dropdown(
        id='month-dropdown',
        options=[{'label': row[0], 'value': row[0]} for row in company_forecast.itertuples(index=False)],
        value=selected_month),
    html.P(id='month-info'),
    html.Br(),
    dash_table.DataTable(
        id='table-employee_cost',
        columns=[{'name': col, 'id': col} for col in employee_monthly_cost.columns],
        data=employee_monthly_cost.to_dict('records')
    )
])

@callback(
    [Output('month-info', 'children'),
     Output('table-employee_cost', 'data')],
    Input('month-dropdown', 'value')
    )
def update_employee_data(selected_month):
    if selected_month is None:
        return ("No month selected", [])
    month_number = month_mapping.get(selected_month.lower())
    ref_date = config.g_ref_date.replace(month=month_number)
    employee_monthly_cost = main_functions.employee_month_forecast(ref_date)
    return (f"Gedetailleerde data voor maand {selected_month}",
            employee_monthly_cost.to_dict('records'),
            )