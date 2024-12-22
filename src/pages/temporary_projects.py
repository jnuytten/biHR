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
# This file contains structure and functions to display an overview of temporary projects.
#
import dash
from dash import html, dash_table
from src.utils import config, main_functions
from src.data import data_store
from src.components.navigation import get_navigation

dash.register_page(__name__, path='/temporary_projects')

# load configuration parameters
ref_date = config.g_ref_date

# access dataframes, lists and dictionaries from the shared module
temporary_projects = data_store.temporary_projects
month_mapping = data_store.month_mapping

# layout of the page
layout = html.Div([
    get_navigation(),
    html.H1("Omzet tijdelijke projecten"),
    html.Br(),
    dash_table.DataTable(
        id='table-temporary_projects',
        columns=[{'name': col, 'id': col} for col in temporary_projects.columns],
        data=temporary_projects.to_dict('records')
    )
])