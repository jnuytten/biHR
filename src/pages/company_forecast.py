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

import dash
from dash import dcc, html, dash_table, callback, Input, Output
import pandas as pd
from src.utils import config
from src.data import data_store

dash.register_page(__name__, path='/')

# load configuration parameters
g_config = config.g_config
ref_date = config.g_ref_date

# access dataframes, lists and dictionaries from the shared module
company_forecast = data_store.company_forecast
monthly_employee_data = data_store.monthly_employee_data
monthly_freelance_data = data_store.monthly_freelance_data
month_mapping = data_store.month_mapping

def get_month_data(selected_month):
    if selected_month is None:
        return None, None
    month_number = month_mapping.get(selected_month.lower())
    # filter data for selected month
    employee_data = monthly_employee_data[month_number]
    freelance_data = monthly_freelance_data[month_number]
    # calculate sum totals in final row
    employee_sum = employee_data.sum().round(2)
    employee_sum_series = pd.Series(employee_sum, name='Totaal')
    employee_data = pd.concat([employee_data, employee_sum_series.to_frame().T])
    freelance_sum = freelance_data.sum().round(2)
    freelance_sum_series = pd.Series(freelance_sum, name='Totaal')
    freelance_data = pd.concat([freelance_data, freelance_sum_series.to_frame().T])
    # reset index so that it is displayed in the table
    employee_data.reset_index(inplace=True)
    freelance_data.reset_index(inplace=True)
    return employee_data, freelance_data

# select the first month in company_forecast as default
selected_month = company_forecast['index'].iloc[0]
employee_data, freelance_data = get_month_data(selected_month)

# layout of the page
layout = html.Div([
    html.H1("Simulatie bedrijf"),
    dash_table.DataTable(
        id='table-company_year',
        columns=[{'name': col, 'id': col} for col in company_forecast.columns],
        data=company_forecast.to_dict('records')
    ),
    html.Br(),
    dcc.Dropdown(
        id='month-dropdown',
        options=[{'label': row[0], 'value': row[0]} for row in company_forecast.itertuples(index=False)],
        value=selected_month
    ),
    html.H2(f"Detail voor de maand {selected_month}", id='month_title'),
    html.H3("Werknemers"),
    dash_table.DataTable(
        id='employee_data-table',
        columns=[{'name': col, 'id': col} for col in employee_data.columns],
        data=employee_data.to_dict('records')
    ),
    html.H3("Freelancers"),
    dash_table.DataTable(
        id = 'freelance_data-table',
        columns=[{'name': col, 'id': col} for col in freelance_data.columns],
        data=freelance_data.to_dict('records')
    )
])
@callback(
    [Output('month_title', 'children'),
     Output('employee_data-table', 'data'),
     Output('freelance_data-table', 'data')],
    Input('month-dropdown', 'value')
)
def update_monthly_data(selected_month):
    print("Running update_monthly_data")
    if selected_month is None:
        return html.Div("Please select a month.")
    # filter data for selected month
    employee_data, freelance_data = get_month_data(selected_month)
    return (f"Detail voor de maand {selected_month}",
            employee_data.to_dict('records'),
            freelance_data.to_dict('records'))