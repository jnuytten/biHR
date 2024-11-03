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
# This function file contains functions which perform freelancer specific calculations.
#
import pandas as pd
from datetime import datetime
from src.utils import db_supply, config, calculate_project


def monthly_project_revenue(project_id: int, workdays: float) -> (float, float):
    """Calculate expected monthly project revenue before and after substracting MSP fee"""
    # todo: in the future add to this function a monthly variable average number of days or use actual calendar to
    # calculate the number of days that can be worked in a month
    dayrate, msp_fee = calculate_project.get_project_dayrate(project_id)
    revenue = dayrate * workdays
    return revenue, revenue * (1 - msp_fee)


def monthly_cost(employee_id, monthly_revenue, days) -> (float, float):
    """Calculate expected monthly cost of a freelancer"""
    # todo: in the future add to this function the possibility to get the right contract of a freelancer linked to a
    # specific project. Now we can only select one project and one contract. If we want to have multiple simultaneous
    # projects we need to change in the database that there is a link between a project and a contract.
    # get global hr values and global freelance contracts
    global_hr_values = db_supply.global_hr_values
    global_freelance_contracts = db_supply.global_freelance_contracts
    # get hourly rate of freelancer
    freelancer_contracts = global_freelance_contracts[global_freelance_contracts['employee_id'] == employee_id]
    if len(freelancer_contracts) == 0:
        raise ValueError(f"No contracts found for freelancer {employee_id}")
    elif len(freelancer_contracts) > 1:
        raise ValueError(f"Multiple contracts found for freelancer {employee_id}")
    # calculate dayrate cost and operational cost
    dayrate_cost = freelancer_contracts['hourly_rate'].values[0] * 8 * days
    operational_cost = round((monthly_revenue * global_hr_values.loc['HR110', 'waarde']) / 12, 2)
    return dayrate_cost + operational_cost


def monthly_summary(ref_date: datetime) -> pd.DataFrame:
    """Create one dataframe giving a list of all projects executed by freelancers, including name of the freelancer,
    project monthly revenue, project monthly cost and gross margin.
    """
    worker_list = db_supply.worker_list_get('Freelance')
    project_data = []
    # loop over all freelance workers
    for index, row in worker_list.iterrows():
        # get projects active on ref date for this freelancer
        # todo: this function currently only retrieves one project, if working on multiple projects this will
        # include only one project
        project_id, start_date, end_date = calculate_project.get_consultant_project(index, ref_date)
        # if no project found, skip this freelancer
        if project_id == 99999:
            continue
        workdays = calculate_project.get_project_fte(project_id) * 217 / 12
        revenue, revenue_msp = monthly_project_revenue(project_id, workdays)
        # calculate monthly cost: hourly fee and expenses
        monthly_cost_freelance = monthly_cost(index, revenue, workdays)
        # add to list of projects
        project = {'Medewerker': row['name'],
                   'Kostprijs': round(monthly_cost_freelance, 2),
                   'Omzet': round(revenue_msp, 2),
                   'Bruto marge': round(revenue_msp - monthly_cost_freelance, 2)
                   }
        project_data.append(project)
    project_frame = pd.DataFrame.from_records(project_data).set_index(['Medewerker'])
    project_frame.sort_index(inplace=True)
    # return one dataframe which is a list of projects with 3 columns: Medewerker, Kostprijs, Omzet, Bruto marge
    # todo: if a freelancer is working on two projects this is shown on two separate lines
    return project_frame


def get_year_of_monthly_summaries():
    """Get all monthly freelance summaries, starting with current month of ref_date, for the whole year"""
    ref_date = config.g_ref_date
    # create dictionary to store the monthly employee summaries
    monthly_freelance_summaries = {}
    # loop over all months of the year, starting from the current month
    for month in range(ref_date.month, 13):
        month_date = datetime(ref_date.year, month, 1)
        # get summarized employee data for the month, and append to dictionary
        monthly_freelance_summaries[month] = monthly_summary(month_date)
    return monthly_freelance_summaries
