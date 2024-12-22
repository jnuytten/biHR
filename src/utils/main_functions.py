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
# This function file contains the top level functions which should be called in main.py
# later-on these functions can be called from a reporting tool or a web interface
#
from datetime import datetime
import configparser
import pandas as pd
import json
from src.utils import calculate_freelance, calculate_calendar, calculate_employee, db_retrieve, db_supply, \
    config, gen_helpers as gh
from src.utils.config import g_config


def load_dataframes():
    """Load all global dataframes with data from SQL database"""
    ref_date = config.g_ref_date
    global global_calendar
    global global_saldi
    global global_projects
    global global_freelance_contracts
    global global_hr_values
    global global_workdays
    global global_multiyear_calendar
    global_calendar = db_supply.calendar_get(ref_date.year)
    global_multiyear_calendar = db_supply.calendar_multiyear_get(ref_date.year - 1, ref_date.year)
    global_saldi = db_supply.saldi_get()
    global_projects = db_supply.projects_get()
    global_freelance_contracts = db_supply.freelance_contracts_get()
    global_hr_values = db_supply.hr_values_get()
    global_workdays = calculate_calendar.build_workday_calendar(ref_date.year)


def refresh_from_officient():
    """Refresh all data in SQL database from Officient API and input files"""
    ref_date = config.g_ref_date
    # log main function execution
    print(f"-- Refreshing Officient data in SQL database")
    # first create backup of the database
    gh.create_sql_dump()
    # update calendar and saldi for all employees in SQL
    db_retrieve.employee_calendar_compose(ref_date.year)
    db_retrieve.employee_saldi_compose(ref_date.year)
    # compose a list of all employee contracts and insert into SQL
    db_retrieve.employee_contract_compose()


def refresh_from_csv():
    """Refresh all data in SQL database from Officient API and input files"""
    # log main function execution
    print(f"-- Refreshing CSV data in SQL database")
    # compose list of employees and freelancers, and input into SQL
    db_retrieve.workers_list_compose(config.g_config.get('FILES', 'freelancers'))
    # compose a list of freelance contracts and a list of projects into SQL
    db_retrieve.project_list_compose(config.g_config.get('FILES', 'projects'))


def company_year_forecast():
    """Calculate the forecast of the year for the whole company and generate a dataframe summarizing this."""
    ref_date = config.g_ref_date
    # log main function execution
    print(f"-- Calculating yearly forecast for company for {ref_date.year}")
    # get global hr values and global freelance contracts
    global_hr_values = db_supply.global_hr_values
    # get monthly summaries of employee data
    monthly_employee_data = calculate_employee.get_year_of_monthly_summaries()
    # get monthly summaries of freelancer data
    monthly_freelance_data = calculate_freelance.get_year_of_monthly_summaries()
    # define dictionary to store monthly summary data for the year overview
    year_data = {}
    # loop over monthly summaries and calculate company-wide forecast
    for month in range(ref_date.month, 13):
        # calculate employee totals
        employee_cost = monthly_employee_data[month]['Kostprijs'].sum()
        employee_revenue = monthly_employee_data[month]['Omzet'].sum()
        # calculate freelance totals
        freelance_cost = monthly_freelance_data[month]['Kostprijs'].sum()
        freelance_revenue = monthly_freelance_data[month]['Omzet'].sum()
        # calculate general costs
        management_cost = global_hr_values.loc['CS001', 'waarde'] / 12
        general_cost = global_hr_values.loc['CS003', 'waarde'] / 12
        # calculating the totals
        total_cost = employee_cost + freelance_cost + management_cost + general_cost
        total_revenue = employee_revenue + freelance_revenue
        total_margin = total_revenue - total_cost

        # add month summary data to year dataframe
        summary = {
            'Maand': gh.get_month_name(month),
            'Personeelskost': round(employee_cost, 0),
            'Freelance kost': round(freelance_cost, 0),
            'Management tijd': round(management_cost, 0),
            'Algemene kosten': round(general_cost, 0),
            'Totaal kosten': round(total_cost, 0),
            'Omzet internen': round(employee_revenue, 0),
            'Omzet freelancers': round(freelance_revenue, 0),
            'Omzet': round(total_revenue, 0),
            'Bruto marge': round(total_margin, 0)
        }
        year_data[month] = summary

    # assemble dataframe with full year overview
    overview_frame = pd.DataFrame.from_records(year_data)
    overview_frame = overview_frame.transpose()
    overview_frame.set_index(['Maand'], inplace=True)
    # calculate sum totals in final row
    cal_sum = overview_frame.sum()
    sum_series = pd.Series(cal_sum, name='Totaal')
    overview_frame = pd.concat([overview_frame, sum_series.to_frame().T])

    return overview_frame, monthly_employee_data, monthly_freelance_data


def employee_month_forecast(ref_date: datetime) -> pd.DataFrame:
    """Calculate the forecasted month for all employees based on the data in the SQL database
    This provides the most detailed view on the split of costs for the employees.
    The resulting dataframe does NOT include the management, administration and general company costs."""
    # log main function execution
    print(f"-- Calculating monthly forecast for employees for {gh.get_month_name(ref_date.month)} {ref_date.year}")
    # load employee dataframes
    cost_frame, revenue_frame = calculate_employee.get_monthly_summary_data(ref_date)
    # calculate total costs on individual basis, only the column "enkel vakantiegeld" is not included in the total cost
    costs_to_include = ['Bezoldiging', 'Provisie vakantiegeld', 'Provisie eindejaarspremie', 'RSZ werkgever',
                        'Premie-PC200', 'Bonus', 'Nettovergoeding', 'Maaltijdcheques', 'ECO-cheques',
                        'Hospitalisatieverz.', 'Groepsverz.', 'Administratie Securex', 'Verzekering BA',
                        'Verzekering AO', 'Mobiliteitskost', 'Opleiding', 'Attenties en activiteiten', 'Preventie',
                        'ICT']
    cost_frame['Individuele kost'] = cost_frame[costs_to_include].sum(axis=1).round(2)
    # add "Inkomsten na MSP" from revenue frame to cost frame
    cost_frame['Omzet'] = round(revenue_frame['Inkomsten na MSP'], 2)
    # sort dataframe by index
    cost_frame.sort_index(inplace=True)
    # calculate totals
    employee_sum = cost_frame.sum().round(2)
    employee_sum_series = pd.Series(employee_sum, name='Totaal')
    cost_frame = pd.concat([cost_frame, employee_sum_series.to_frame().T])
    # reset index so that it is displayed in the table
    cost_frame.reset_index(inplace=True)

    return cost_frame
