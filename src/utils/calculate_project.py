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
# This function file contains functions to get info regarding projects.
#
from datetime import datetime
import calendar
import pandas as pd
from src.utils import db_supply, gen_helpers as gh


def get_consultant_project(consultant_id: int, ref_date: datetime) -> (int, datetime, datetime):
    """Retrieve current project of consultant with start and end dates"""
    global_projects = db_supply.global_projects
    # filter out projects of consultant
    consultant_projects = global_projects[global_projects['employee_id'] == consultant_id]
    # set window of dates to look for project
    start_window = ref_date.replace(day=1)
    end_window = ref_date.replace(day=(calendar.monthrange(ref_date.year, ref_date.month)[1]))
    for x in consultant_projects.index:
        if (consultant_projects.loc[x, 'start_date'] <= end_window and
                consultant_projects.loc[x, 'end_date'] >= start_window):
            return (consultant_projects.loc[x, 'id'], consultant_projects.loc[x, 'start_date'],
                    consultant_projects.loc[x, 'end_date'])
    gh.logger(f'No project found for employee {consultant_id} {gh.get_consultant_name(consultant_id)} in month '
          f'{ref_date.month}, setting project ID to 99999.')
    # no project found, return impossible values
    return 99999, datetime(2100, 1, 1), datetime(2100, 1, 1)


def get_project_dayrate(project_id: int) -> (float, float):
    """Retrieve current dayrate of project and applicable MSP fee"""
    global_projects = db_supply.global_projects
    for x in global_projects.index:
        if global_projects.loc[x, 'id'] == project_id:
            return global_projects.loc[x, 'hourly_rate'] * 8, global_projects.loc[x, 'msp_percentage']
    # no project found, means dayrate is 0
    gh.logger(f'No dayrate for project {project_id}, setting dayrate to 0.00.')
    return 0.00, 0.00


def get_project_fte(project_id: int) -> float:
    """Retrieve current FTE of project"""
    global_projects = db_supply.global_projects
    for x in global_projects.index:
        if global_projects.loc[x, 'id'] == project_id:
            return global_projects.loc[x, 'percentage']
    # no project found, defaulting to 1
    print(f'No percentage defined for project {project_id}, setting FTE to 1.00.')
    return 1.00


def temporary_project_compose(csvfile: str) -> pd.DataFrame:
    """Get a list of projects from csv file into a dataframe"""
    dtype = {'Offerte': str, 'Eindklant': str, 'Klant': str, 'Bedrag ex. BTW': float, 'Status': str, 'Periode': str,
             '25 procent': float, '50 procent': float, '100 procent': float}
    csv_project_frame = pd.read_csv(csvfile, dtype=dtype, decimal=',', sep=';')
    # Convert percentage columns back to integers, handling NA values
    csv_project_frame['25 procent'] = csv_project_frame['25 procent'].fillna(0).astype(int)
    csv_project_frame['50 procent'] = csv_project_frame['50 procent'].fillna(0).astype(int)
    csv_project_frame['100 procent'] = csv_project_frame['100 procent'].fillna(0).astype(int)
    # create frome the CSV file a temporary project dataframe with general info columns, total amount and depending on
    # the month indicated in 25, 50 and 100 procent columns a split of the invoice amount over the months
    temporary_project_frame = csv_project_frame[['Offerte', 'Eindklant', 'Bedrag ex. BTW', 'Status']].copy()

    # Add 12 columns named 1 to 12
    for month in range(1, 13):
        temporary_project_frame[str(month)] = 0.0

    # Distribute the "Bedrag ex. BTW" amount based on the percentages
    for index, row in csv_project_frame.iterrows():
        amount = row['Bedrag ex. BTW']
        if row['25 procent'] in range(1, 13):
            temporary_project_frame.at[index, str(row['25 procent'])] += amount * 0.25
        if row['50 procent'] in range(1, 13):
            temporary_project_frame.at[index, str(row['50 procent'])] += amount * 0.50
        if row['100 procent'] in range(1, 13):
            remaining_amount = amount
            if row['25 procent'] in range(1, 13):
                remaining_amount -= temporary_project_frame.at[index, str(row['25 procent'])]
            if row['50 procent'] in range(1, 13):
                remaining_amount -= temporary_project_frame.at[index, str(row['50 procent'])]
            temporary_project_frame.at[index, str(row['100 procent'])] += remaining_amount
    return temporary_project_frame