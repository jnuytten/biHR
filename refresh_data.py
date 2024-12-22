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
# This script is used to refresh the data in the SQL database. It is used to update the data in the SQL database with
# the latest data from the Officient API and CSV files.
#

import locale
from src.utils import main_functions


def main():
    print("biHR Copyright (C) 2024 Joachim Nuyttens")
    print("This program comes with ABSOLUTELY NO WARRANTY.")
    print("This is free software, and you are welcome to redistribute it under version 3 of the GNU General Public"
          " License.")

    ### LOAD GENERAL SETTINGS ###
    #############################

    locale.setlocale(locale.LC_ALL, "nl_BE.utf8")

    ### DATA RETRIEVAL FROM OFFICIENT API and CSV files###
    ######################################################
    main_functions.load_dataframes()
    main_functions.refresh_from_officient()
    main_functions.refresh_from_csv()

    # manual update of calendar for another year, e.g. 2023, normally this should not be executed
    #db_retrieve.employee_calendar_compose(2023)

if __name__ == "__main__":
    main()