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
# This file contains the navigation block of the Dash app.
#

from dash import dcc, html

def get_navigation():
    return html.Div([
        dcc.Link('Company Forecast', href='/'),
        html.Span(' | '),
        dcc.Link('Employee Monthly Cost', href='/employee_monthly_cost'),
        html.Span(' | '),
        dcc.Link('Employee Simulation', href='/employee_simulation'),
    ], style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderBottom': '1px solid #dee2e6'})