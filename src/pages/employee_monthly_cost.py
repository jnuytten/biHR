# Copyright (C) 2025 Joachim Nuyttens
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
from dash import dcc, html, dash_table, callback, Input, Output
from src.utils import config, main_functions
from src.data import data_store
from src.components.navigation import get_navigation

dash.register_page(__name__, path='/employee_monthly_cost')

# load configuration parameters
ref_date = config.g_ref_date

# access dataframes, lists and dictionaries from the shared module
company_forecast = data_store.company_forecast
month_mapping = data_store.month_mapping
worker_names = data_store.worker_names

# select default month and calculate employee monthly cost
selected_month = company_forecast['index'].iloc[0]
employee_monthly_cost = main_functions.employee_month_forecast(ref_date)
employee_monthly_cost = employee_monthly_cost.rename(index=worker_names)
# DEBUG
#employee_monthly_cost.index = employee_monthly_cost.index.map(lambda x: worker_names.get(int(x), x))
#print(employee_monthly_cost)

# layout of the page
layout = html.Div([
    get_navigation(),
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
    # set ref_date to the selected month
    month_number = month_mapping.get(selected_month.lower())
    ref_date = config.g_ref_date.replace(month=month_number)
    # calculate employee monthly cost for the selected month
    employee_monthly_cost = main_functions.employee_month_forecast(ref_date)
    employee_monthly_cost = employee_monthly_cost.rename(index=worker_names)
    return (f"Gedetailleerde data voor maand {selected_month}",
            employee_monthly_cost.to_dict('records'),
            )