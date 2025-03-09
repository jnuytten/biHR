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
# This function file contains all functions used to retrieve data from the SQL database.
#
import calendar
import configparser
from typing import Concatenate

import pandas as pd
from datetime import datetime
from src.utils import config, gen_helpers as gh


def worker_list_get(scope: str = "all",
                    ref_date: datetime = False,
                    teams: list = ["Projects & Business Development", "Testing", "Operations"]) -> pd.DataFrame:
    """Get DataFrame with all workers from SQL, optional argument can be set to
    'all' (default) showing all workers
    'intern' showing all workers except freelancers
    other values, showing workers which match exactly with the role_name
    optional argument ref_date can be set to a datetime object, only employees with contract valid in that month are
    included"""
    # define list of teams
    teams_list = "(" + ", ".join(f"'{team}'" for team in teams) + ")"
    # if optional ref_date is set, only employees with contract valid in that month are included
    if ref_date and scope == 'intern':
        # only contracts not ending before ref_date's month start are included, end_date_bracket equals 1st of the month
        end_date_bracket = ref_date.replace(day=1).strftime('%Y-%m-%d')
        # only contracts starting before ref_date's month end are included, start_date_bracket equals last of the month
        last_day = calendar.monthrange(ref_date.year, ref_date.month)[1]
        start_date_bracket = ref_date.replace(day=last_day).strftime('%Y-%m-%d')
        query = f"""
        SELECT DISTINCT pec.employee_id, pw.name, pw.role_name
        FROM people_employee_contracts pec
        JOIN people_workers pw ON pec.employee_id = pw.id
        WHERE pec.start_date <= '{start_date_bracket}' AND (pec.end_date > '{end_date_bracket}' OR pec.end_date IS
        NULL) AND pw.team IN {teams_list};
        """
    else:
        if scope == 'all':
            query = f"SELECT id, name, role_name FROM people_workers WHERE team IN {teams_list}"
        elif scope == 'intern':
            query = (f"SELECT id, name, role_name FROM people_workers WHERE role_name != 'Freelance'"
                     f" AND team IN {teams_list}")
        else:
            query = (f"SELECT id, name, role_name FROM people_workers WHERE role_name = '{scope}'"
                     f" AND team IN {teams_list}")
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=['id', 'name', 'role_name'])
    df.set_index('id', inplace=True)
    return df


def employee_contracts_get(ref_date: datetime,
                           teams: list = ["Projects & Business Development", "Testing", "Operations"])\
        -> pd.DataFrame:
    """Get DataFrame with all employee contracts valid in a certain month, excluding those which expired before start
    of the month and those which start after the end of the month."""
    # define list of teams
    teams_list = "(" + ", ".join(f"'{team}'" for team in teams) + ")"
    # only contracts not ending before ref_date's month start are included, end_date_bracket equals 1st of the month
    end_date_bracket = ref_date.replace(day=1).strftime('%Y-%m-%d')
    # only contracts starting before ref_date's month end are included, start_date_bracket equals last of the month
    last_day = calendar.monthrange(ref_date.year, ref_date.month)[1]
    start_date_bracket = ref_date.replace(day=last_day).strftime('%Y-%m-%d')
    query = f"""
    SELECT pec.*
    FROM people_employee_contracts pec
    JOIN people_workers pw ON pec.employee_id = pw.id 
    WHERE pec.start_date <= '{start_date_bracket}' AND (pec.end_date > '{end_date_bracket}' OR pec.end_date IS NULL)
    AND pw.team IN {teams_list};
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
    df.set_index('id', inplace=True)
    pd.set_option('display.max_columns', None)
    return df


def employee_calendar_get(employee_id: int, year: int) -> pd.DataFrame:
    """Get dataframe with calendar for year of one specific employee"""
    query = f"""
    SELECT * FROM calendar_workday
    WHERE employee_id = {employee_id} AND YEAR(date) = {year};
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index(['employee_id', 'date'], inplace=True)
    return df


def calendar_get(year: int):
    """Get dataframe with calendar for year of all employees"""
    global global_calendar
    query = f"""
    SELECT * FROM calendar_workday WHERE YEAR(date) = {year};
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            global_calendar = pd.DataFrame(rows, columns=columns)
    global_calendar['date'] = pd.to_datetime(global_calendar['date'])
    global_calendar.set_index(['employee_id', 'date'], inplace=True)


def calendar_multiyear_get(start_year: int, end_year: int):
    """Get dataframe with calendar for multiple years"""
    global global_multiyear_calendar
    query = f"""
    SELECT * FROM calendar_workday WHERE YEAR(date) >= {start_year} AND YEAR(date) <= {end_year};
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            global_multiyear_calendar = pd.DataFrame(rows, columns=columns)
    global_multiyear_calendar['date'] = pd.to_datetime(global_multiyear_calendar['date'])
    global_multiyear_calendar.set_index(['employee_id', 'date'], inplace=True)


def saldi_get():
    """Get dataframe with saldi for year of all employees"""
    global global_saldi
    query = f"""
    SELECT * FROM calendar_saldi;
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            global_saldi = pd.DataFrame(rows, columns=columns)
    global_saldi.set_index('employee_id', inplace=True)


def projects_get():
    """Get DataFrame with all projects"""
    global global_projects
    query = f"""
    SELECT * FROM projects
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            global_projects = pd.DataFrame(rows, columns=columns)
            global_projects['end_date'] = pd.to_datetime(global_projects['end_date'])
            global_projects['start_date'] = pd.to_datetime(global_projects['start_date'])


def freelance_contracts_get():
    """Get DataFrame with all freelance contracts"""
    global global_freelance_contracts
    query = f"""
    SELECT * FROM people_freelance_contracts
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            global_freelance_contracts = pd.DataFrame(rows, columns=columns)
    global_freelance_contracts.set_index('id', inplace=True)


def hr_values_get():
    """Get DataFrame with hr values"""
    global global_hr_values
    global_hr_values = pd.read_csv(config.g_config.get('FILES', 'hrvalues'), decimal=',', sep=';')
    global_hr_values = global_hr_values.set_index(['Code'])
