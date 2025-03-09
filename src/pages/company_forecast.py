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
# This file contains structure and functions to display the company forecast page.
#

import dash
import urllib.parse
from dash import dcc, html, dash_table, callback, Input, Output
import pandas as pd
from src.utils import config
from src.data import data_store
from src.components.navigation import get_navigation

dash.register_page(__name__, path='/')

# Load configuration parameters
g_config = config.g_config
ref_date = config.g_ref_date

# Layout of the page
layout = html.Div([
    dcc.Location(id='url', refresh=False),  # Capture URL parameters
    get_navigation(),
    html.H1("Simulatie bedrijf"),
    html.Div([
        html.A("Alle", href="/"),
        " | ",
        html.A("Enkel testafdeling", href="/?scope=testing"),
        " | ",
        html.A("Alle behalve testafdeling", href="/?scope=notesting"),
    ]),
    html.Br(),
    html.Div(id='output_scope'),
    html.Br(),
    dash_table.DataTable(id='table-company_year'),
    html.Br(),
    dcc.Dropdown(id='month-dropdown'),
    html.H2(id='month_title'),
    html.H3("Werknemers"),
    dash_table.DataTable(id='employee_data-table'),
    html.H3("Freelancers"),
    dash_table.DataTable(id='freelance_data-table')
])

@callback(
    [Output('output_scope', 'children'),
     Output('table-company_year', 'columns'),
     Output('table-company_year', 'data'),
     Output('month-dropdown', 'options'),
     Output('month-dropdown', 'value'),
     Output('month_title', 'children'),
     Output('employee_data-table', 'columns'),
     Output('employee_data-table', 'data'),
     Output('freelance_data-table', 'columns'),
     Output('freelance_data-table', 'data')],
    [Input('url', 'search'),
     Input('month-dropdown', 'value')]
)

def update_page(search, selected_month):
    # Extract scope from URL
    query_params = urllib.parse.parse_qs(search.lstrip("?"))
    scope_value = query_params.get("scope", [""])[0]

    # Select data based on scope
    if scope_value == "testing":
        company_forecast = data_store.company_forecast_testing
        monthly_employee_data = data_store.monthly_employee_data_testing
        monthly_freelance_data = data_store.monthly_freelance_data_testing
    elif scope_value == "notesting":
        company_forecast = data_store.company_forecast_notesting
        monthly_employee_data = data_store.monthly_employee_data_notesting
        monthly_freelance_data = data_store.monthly_freelance_data_notesting
    else:
        company_forecast = data_store.company_forecast
        monthly_employee_data = data_store.monthly_employee_data
        monthly_freelance_data = data_store.monthly_freelance_data

    # Get month mapping and worker names
    month_mapping = data_store.month_mapping
    worker_names = data_store.worker_names

    # Default selected month
    if selected_month is None:
        selected_month = company_forecast['index'].iloc[0]

    # Function to get month-specific data
    def get_month_data(month):
        if month is None:
            return pd.DataFrame(), pd.DataFrame()
        month_number = month_mapping.get(month.lower())
        if month_number is None:
            return pd.DataFrame(), pd.DataFrame()
        employee_data = monthly_employee_data.get(month_number, pd.DataFrame()).rename(index=worker_names)
        freelance_data = monthly_freelance_data.get(month_number, pd.DataFrame()).rename(index=worker_names)
        if not employee_data.empty:
            employee_data.loc['Totaal'] = employee_data.drop(columns=["Team"], errors='ignore').sum().round(2)
            employee_data.reset_index(inplace=True)
        if not freelance_data.empty:
            freelance_data.loc['Totaal'] = freelance_data.drop(columns=["Team"], errors='ignore').sum().round(2)
            freelance_data.reset_index(inplace=True)
        return employee_data, freelance_data

    # Get data for the selected month
    employee_data, freelance_data = get_month_data(selected_month)

    return (
        f"Scope: {scope_value}",
        [{'name': col, 'id': col} for col in company_forecast.columns],
        company_forecast.to_dict('records'),
        [{'label': row[0], 'value': row[0]} for row in company_forecast.itertuples(index=False)],
        selected_month,
        f"Detail voor de maand {selected_month}",
        [{'name': col, 'id': col} for col in employee_data.columns],
        employee_data.to_dict('records'),
        [{'name': col, 'id': col} for col in freelance_data.columns],
        freelance_data.to_dict('records')
    )
