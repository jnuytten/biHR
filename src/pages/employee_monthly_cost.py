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
from src.utils import config
from src.utils import main_functions

dash.register_page(__name__, path='/employee_monthly_cost')

# load configuration parameters
#g_config = configparser.ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
#g_config.read('config.ini')

#ref_date = datetime(g_config.getint('PARAMETERS', 'year'), g_config.getint('PARAMETERS',
#                                                                           'month'), 1)

employee_monthly_cost = main_functions.employee_month_forecast(config.g_ref_date)

# layout of the page
layout = html.Div([
    html.H1("Detail werknemerskosten"),
    dash_table.DataTable(
        id='table-employee_cost',
        columns=[{'name': col, 'id': col} for col in employee_monthly_cost.columns],
        data=employee_monthly_cost.to_dict('records')
    )
])

