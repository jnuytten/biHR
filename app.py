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
from dash import Dash, dcc, html
import locale
from src.utils import main_functions
from src.data import data_store

print("biHR Copyright (C) 2024 Joachim Nuyttens")
print("This program comes with ABSOLUTELY NO WARRANTY.")
print("This is free software, and you are welcome to redistribute it under version 3 of the GNU General Public"
      " License.")

### LOAD GENERAL SETTINGS ###
#############################

locale.setlocale(locale.LC_ALL, "nl_BE.utf8")

## LOAD ESSENTIAL DATA ##
###############################
# load all global dataframes with data from SQL database
main_functions.load_dataframes()

# Initialize the dataframes and store them in the shared module
(data_store.company_forecast, data_store.monthly_employee_data, data_store.monthly_freelance_data,
 data_store.temporary_projects) = main_functions.company_year_forecast()
data_store.company_forecast.reset_index(inplace=True)

# Initialize some lists and dictionaries
data_store.month_mapping = {
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


### INITIALIZE DASH APP ###
###########################

app = Dash(__name__, use_pages=True, pages_folder='src/pages')

if __name__ == '__main__':
    app.run(debug=True)

app.layout = html.Div([
    html.H1('Multi-page app with Dash Pages'),
    html.Div([
        html.Div(
            dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"])
        ) for page in dash.page_registry.values()
    ]),
    dash.page_container
])

