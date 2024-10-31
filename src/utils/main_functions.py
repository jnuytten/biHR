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
    gen_helpers as gh, html_report


def load_dataframes(ref_date: datetime, config: configparser.ConfigParser):
    """Load all global dataframes with data from SQL database"""
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
    global_hr_values = db_supply.hr_values_get(config)
    global_workdays = calculate_calendar.build_workday_calendar(ref_date.year)


def refresh_from_officient(config: configparser.ConfigParser, ref_date: datetime):
    """Refresh all data in SQL database from Officient API and input files"""
    # log main function execution
    print(f"-- Refreshing Officient data in SQL database")
    # first create backup of the database
    gh.create_sql_dump(config)
    # update calendar and saldi for all employees in SQL
    db_retrieve.employee_calendar_compose(ref_date.year)
    db_retrieve.employee_saldi_compose(ref_date.year, config)
    # compose a list of all employee contracts and insert into SQL
    db_retrieve.employee_contract_compose()


def refresh_from_csv(config: configparser.ConfigParser):
    """Refresh all data in SQL database from Officient API and input files"""
    # log main function execution
    print(f"-- Refreshing CSV data in SQL database")
    # DEBUG
    print(config.sections())
    # compose list of employees and freelancers, and input into SQL
    db_retrieve.workers_list_compose(config.get('FILES', 'freelancers'))
    # compose a list of freelance contracts and a list of projects into SQL
    db_retrieve.project_list_compose(config.get('FILES', 'projects'))


def company_year_forecast(config: configparser.ConfigParser, ref_date: datetime):
    """Calculate the forecast of the year for the whole company and generate a dataframe summarizing this."""
    # log main function execution
    print(f"-- Calculating yearly forecast for company for {ref_date.year}")
    # get global hr values and global freelance contracts
    global_hr_values = db_supply.global_hr_values
    # get monthly summaries of employee data
    monthly_employee_data = calculate_employee.get_year_of_monthly_summaries(config, ref_date)
    # get monthly summaries of freelancer data
    monthly_freelance_data = calculate_freelance.get_year_of_monthly_summaries(ref_date)
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
        administration_cost = global_hr_values.loc['CS002', 'waarde'] / 12
        general_cost = global_hr_values.loc['CS003', 'waarde'] / 12
        # calculating the totals
        total_cost = employee_cost + freelance_cost + management_cost + administration_cost + general_cost
        total_revenue = employee_revenue + freelance_revenue
        total_margin = total_revenue - total_cost
        # adding all values to the dataframe
        month_content = html_report.forecast_company_month(month, monthly_employee_data[month],
                                                           monthly_freelance_data[month], management_cost,
                                                           administration_cost, general_cost)
        # todo: we should capture the month_content data in a buffer somewhere to quickly generate
        # month specific pages
        # maybe we should do this with a dropdown as on the employee page, and when a month is selected in
        # the dropdown, the month detail appears in a pane below the yearly summary

        # todo: we also need this but this can be on a separate function and be calculated every time again
        #employee_month_forecast(config, ref_date.replace(month=month))

        # add month summary data to year dataframe
        summary = {
            'Maand': gh.get_month_name(month),
            'Personeelskost': round(employee_cost, 0),
            'Freelance kost': round(freelance_cost, 0),
            'Management tijd': round(management_cost, 0),
            'Administratie': round(administration_cost, 0),
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


def employee_month_forecast(config: configparser.ConfigParser, ref_date: datetime):
    """Calculate the forecasted month for all employees based on the data in the SQL database
    This provides the most detailed view on the split of costs for the employees."""
    # log main function execution
    print(f"-- Calculating monthly forecast for employees for {gh.get_month_name(ref_date.month)} {ref_date.year}")
    # get location of output directory
    output_dir = config.get('PARAMETERS', 'outputdir')
    # load hr values and ignore list
    global_hr_values = db_supply.global_hr_values
    ignore_list = json.loads(config.get('PARAMETERS', 'ignore_list'))
    # load employee dataframes
    cost_frame, revenue_frame = calculate_employee.get_monthly_summary_data(ref_date)
    # calculate total costs on individual basis, only the column "enkel vakantiegeld" is not included in the total cost
    costs_to_include = ['Bezoldiging', 'Provisie vakantiegeld', 'Provisie eindejaarspremie', 'RSZ werkgever',
                        'Premie-PC200', 'Bonus', 'Nettovergoeding', 'Maaltijdcheques', 'ECO-cheques',
                        'Hospitalisatieverz.', 'Groepsverz.', 'Administratie Securex', 'Verzekering BA',
                        'Verzekering AO', 'Mobiliteitskost', 'Opleiding', 'Attenties en activiteiten', 'Preventie',
                        'ICT']
    cost_frame['Individuele kost'] = cost_frame[costs_to_include].sum(axis=1)
    # add management cost, administrative cost and general cost to the dataframes
    cost_frame['Management tijd'] = round(global_hr_values.loc['HR080', 'waarde'] / 12, 2)
    cost_frame['Administratie'] = round(global_hr_values.loc['HR081', 'waarde'] / 12, 2)
    cost_frame['Algemene kosten'] = round(global_hr_values.loc['HR200', 'waarde'] / 12, 2)
    # calculate total cost including company expenses
    cost_frame['Totaal kost'] = cost_frame[
        ['Individuele kost', 'Management tijd', 'Administratie', 'Algemene kosten']].sum(axis=1)
    # add "Inkomsten na MSP" from revenue frame to cost frame
    cost_frame['Omzet'] = round(revenue_frame['Inkomsten na MSP'], 2)
    # calculate gross margin
    cost_frame['Bruto marge'] = round(cost_frame['Omzet'] - cost_frame['Totaal kost'], 2)
    # calculate relative margin
    cost_frame['Relatieve marge'] = round(100 * cost_frame['Bruto marge'] / cost_frame['Omzet'], 2)

    # change relative margin to percentage
    cost_frame['Relatieve marge'] = cost_frame['Relatieve marge'].astype(str) + '%'

    # drop employees in ignore list
    try:
        cost_frame.drop(ignore_list, inplace=True)
    except KeyError:
        print("Some employees in Ignorelist were not found in employee cost overview, please correct this.")

    # sort dataframe by index
    cost_frame.sort_index(inplace=True)

    # creating html content for the detailed month report
    content = f'<h4>Detailoverzicht maand {gh.get_month_name(ref_date.month)}</h4>\n'
    content += ('<p>Gedetailleerde cijfers voor interne medewerkers. Opgelet! Enkel en dubbel vakantiegeld worden niet'
                'vermeld en niet verrekend aangezien dit boekhoudkundig verrekend wordt met de provisie.</p>\n')
    content += cost_frame.to_html(escape=False)
    # print month to html
    html_report.generate_html(f'{output_dir}/report-company_{ref_date.year}_{ref_date.month}_empl_details.html',
                              f'Gedetailleerde cijfers bedienden {ref_date.year}'
                              f' {gh.get_month_name(ref_date.month)}', content)


def employee_year_simulation(config: configparser.ConfigParser, employee_id: int, ref_date: datetime, ):
    """Calculate the yearly simulation for one specific employee and generate a html report, this function as it is
    currently set up uses the real calendar and does not assume a fixed number of working days per year as was the
    case in the Excel simulation."""
    # get employee name
    employee_name = gh.get_consultant_name(employee_id)
    # log main function execution
    print(f"-- Calculating yearly simulation for {employee_name} (id {str(employee_id)})")
    # get location of output directory
    output_dir = config.get('PARAMETERS', 'outputdir')
    # get yearly cost and income for employee
    cost_overview, yearly_revenue, parameters = calculate_employee.yearly_cost_income(config, employee_id, ref_date,
                                                                                      True)
    # create html content for the yearly simulation
    content = html_report.forecast_employee_year(employee_id, employee_name, ref_date, cost_overview, yearly_revenue,
                                                 parameters)
    html_report.generate_html(f'{output_dir}/report-employee_{employee_id}_{ref_date.year}_simulation.html',
                              f'Jaarlijkse simulatie {employee_name}', content)
