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
# This file is used initialize configuration global variables.
#

import configparser
from datetime import datetime

# Define and initialize the global configuration object
g_config = configparser.ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
g_config.read('config.ini')

# Define and initialize the global reference date
g_ref_date = datetime(g_config.getint('PARAMETERS', 'year'),
                      g_config.getint('PARAMETERS', 'month'), 1)

