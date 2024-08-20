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
from dash import dcc, html, Input, Output
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
global_dataframes = {
    'cost_frame': cost_frame,
    'revenue_frame': revenue_frame
}

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])

def display_page(pathname):
    if pathname == '/company_forecast':
        from src.pages import company_forecast
        return company_forecast.layout
    elif pathname == '/employee_simulation':
        from src.pages import employee_simulation
        employee_simulation.register_callbacks(app)
        return employee_simulation.layout
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=True)
