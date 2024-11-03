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

import configparser
import locale
from datetime import datetime
from src.utils import main_functions


def main():
    print("biHR Copyright (C) 2024 Joachim Nuyttens")
    print("This program comes with ABSOLUTELY NO WARRANTY.")
    print("This is free software, and you are welcome to redistribute it under version 3 of the GNU General Public"
          " License.")

    ### LOAD GENERAL SETTINGS ###
    #############################

    locale.setlocale(locale.LC_ALL, "nl_BE.utf8")

    # load configuration parameters
    g_config = configparser.ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
    g_config.read('config.ini')

    # date that acts as reference point for the calculation
    ref_date = datetime(g_config.getint('PARAMETERS', 'year'), g_config.getint('PARAMETERS',
                                                                               'month'), 1)

    ### DATA RETRIEVAL FROM OFFICIENT API and CSV files###
    ######################################################
    #main_functions.load_dataframes(ref_date, g_config)
    #main_functions.refresh_from_officient(g_config, ref_date)
    #main_functions.refresh_from_csv(g_config)

    # manual update of calendar for another year, e.g. 2023, normally this should not be executed
    #db_retrieve.employee_calendar_compose(2023)

    ## LOAD ESSENTIAL DATA ##
    ###############################
    # load all global dataframes with data from SQL database
    main_functions.load_dataframes(ref_date, g_config)

    ## RUN REPORTING ##
    ###################
    main_functions.company_year_forecast(g_config, ref_date)
    #alt_date = datetime(2024, 9, 1)
    #main_functions.employee_month_forecast(g_config, alt_date)


    ## OPTIONAL: RUN YEARLY SIMULATION FOR INDIVIDUAL EMPLOYEE ##
    #############################################################
    employee_id = 95124
    main_functions.employee_year_simulation(g_config, employee_id, ref_date)


if __name__ == "__main__":
    main()


# DEBUGGING

#gh.create_sql_dump()
#print(db_supply.worker_list_get('intern'))
#print(calculate_project.get_project_fte(11))

#saldi = db_retrieve.employee_saldi_get(408955, ref_date.year, g_config)
#print(saldi)
