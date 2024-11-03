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
# This function file contains functions which perform employee specific calculations.
#
import pandas as pd
from datetime import datetime
import configparser
import json
import calendar
from src.utils import calculate_calendar, config, db_supply, calculate_project, gen_helpers as gh


def get_bonus(contract_id: int, contract_frame: pd.DataFrame, hr_values: pd.DataFrame) -> float:
    """Retrieve the bonus amount for employee with specified contract"""
    ref_date = config.g_ref_date
    # get number of bonus workdays from calendar
    reference_period_start = ref_date.replace(year=ref_date.year - 1, month=12, day=1)
    reference_period_end = ref_date.replace(month=11, day=30)
    company_paid_ratio, vacation_time_ratio =(
        calculate_calendar.get_fte_ratios(contract_frame.loc[contract_id, 'employee_id'],
                                          reference_period_start,
                                          reference_period_end,
                                          True))
    if contract_frame.loc[contract_id, 'function_category'].startswith('JUN'):
        return hr_values.loc['HR020', 'waarde'] * company_paid_ratio
    elif contract_frame.loc[contract_id, 'function_category'].startswith('EXP'):
        return hr_values.loc['HR021', 'waarde'] * company_paid_ratio
    elif (contract_frame.loc[contract_id, 'function_category'].startswith('SEN') or
          contract_frame.loc[contract_id, 'function_category'].startswith('BUS')):
        return hr_values.loc['HR022', 'waarde'] * company_paid_ratio
    else:
        return 0


def get_eco_cheques(employee_id: int, hr_values: pd.DataFrame) -> float:
    """Retrieve the ECO cheques amount for an employee"""
    ref_date = config.g_ref_date
    # calculate pro-rata factor based on reference period
    reference_period_start = ref_date.replace(year=ref_date.year - 1, month=6, day=1)
    reference_period_end = ref_date.replace(month=5, day=31)
    company_paid_ratio, vacation_time_ratio = (
        calculate_calendar.get_fte_ratios(employee_id, reference_period_start, reference_period_end,
                                          True))
    # return ECO cheques amount based on configured values and pro rata factor
    return hr_values.loc['HR011', 'waarde'] * hr_values.loc['HR013', 'waarde'] * company_paid_ratio


def get_pc200_premium(employee_id: int, hr_values: pd.DataFrame) -> float:
    """Retrieve the PC200 premium amount for an employee"""
    ref_date = config.g_ref_date
    # calculate pro-rata factor based on reference period
    reference_period_start = ref_date.replace(year=ref_date.year - 1, month=6, day=1)
    reference_period_end = ref_date.replace(month=5, day=31)
    company_paid_ratio, vacation_time_ratio = (
        calculate_calendar.get_fte_ratios(employee_id, reference_period_start, reference_period_end,
                                          True))
    # return ECO cheques amount based on configured values and pro rata factor
    return hr_values.loc['HR025', 'waarde'] * company_paid_ratio


def get_vakantiegeld(monthly_salary: float, first_month: int) -> float:
    """Calculate vakantiegeld, rough estimate"""
    # this function should only be used as a rough indicator, e.g. for salary simulation on employee level
    # because it does no exact calculation, does not take into account what period was worked in the previous year
    if first_month > 1:
        return 0
    else:
        return monthly_salary * 0.92


def get_net_allowance(contract_id: int, contract_frame: pd.DataFrame, hr_values: pd.DataFrame) -> float:
    """Calculate the net allowance for employee with specified initials"""
    # to replace based on calculation depending on mobility type, and selecting right value in HR values
    if contract_frame.loc[contract_id, 'mobility_type'] == 'car':
        return hr_values.loc['HR030', 'waarde']
    else:
        return hr_values.loc['HR031', 'waarde']


def monthly_cost(contract_id: int, ref_date: datetime, contract_frame: pd.DataFrame, worker_list: pd.DataFrame,
                 monthly_revenue: float) -> dict:
    """Retrieve and calculate monthly salary cost for employee contract with specified id
    This function does not yield a proper result on employee level but is only to be used on the company level. It does
    NOT include general company costs (e.g. accounting), management and administration cost
    """
    # get global hr values
    global_hr_values = db_supply.global_hr_values
    # get employee name
    employee_id = contract_frame.loc[contract_id, 'employee_id']
    employee_name = worker_list.loc[employee_id, 'name']
    # get number of expected workdays from calendar
    expected_workdays = calculate_calendar.get_workhours(
        employee_id,
        ref_date.replace(day=1),
        ref_date.replace(day=calendar.monthrange(ref_date.year, ref_date.month)[1]),
        False) / 8
    # evaluate if contract is starting or ending in the current month
    contract_change = evaluate_contract_start_end(contract_id, contract_frame, ref_date, 'm')
    if contract_change:
        gh.logger(f"Contract for {employee_name} is starting or ending in month {ref_date.month}.")
    # calculate correction factor FTE, to take into the actual fte time that are paid hours
    company_paid_ratio, vacation_time_ratio = calculate_calendar.get_fte_ratios(
        employee_id,
        ref_date.replace(day=1),
        ref_date.replace(day=calendar.monthrange(ref_date.year, ref_date.month)[1]),
        contract_change)
    # set certain advantages to 0 by default
    bonus = 0
    ecocheque = 0
    pc200premie = 0
    # include ECO cheques if month is may
    if ref_date.month == 5:
        ecocheque = round(get_eco_cheques(employee_id, global_hr_values), 2)
    # include PC200 premie if month is june
    if ref_date.month == 6:
        pc200premie = round(get_pc200_premium(employee_id, global_hr_values), 2)
    # include bonus if month is december
    if ref_date.month == 12:
        bonus = round(get_bonus(contract_id, contract_frame, global_hr_values), 2)
    # bezoldiging to calculate is the gross salary without the 'enkel vakantiegeld', but for RSZ calculations we have to take into account the full gross salary
    bezoldiging = (contract_frame.loc[contract_id, 'monthly_salary'] * company_paid_ratio * (1 - vacation_time_ratio)
                   * config.g_config.getfloat('PARAMETERS', 'inflator'))
    bezoldiging_rsz_basis = (contract_frame.loc[contract_id, 'monthly_salary'] * company_paid_ratio
                             * config.g_config.getfloat('PARAMETERS', 'inflator'))
    # create cost overview of the employee
    cost_overview = {
        'Medewerker': employee_name,
        'Bezoldiging': round(bezoldiging, 2),
        'Provisie vakantiegeld': round(bezoldiging * 0.182, 2),
        'Provisie eindejaarspremie': round(bezoldiging * (1 + global_hr_values.loc['HR401', 'waarde']) / 12, 2),
        'RSZ werkgever': round(bezoldiging_rsz_basis * global_hr_values.loc['HR401', 'waarde'], 2),
        'Premie-PC200': pc200premie,
        'Bonus': bonus,
        'Nettovergoeding': round(get_net_allowance(contract_id, contract_frame, global_hr_values), 2),
        'Maaltijdcheques': round((global_hr_values.loc['HR010', 'waarde'] * global_hr_values.loc['HR012', 'waarde'] *
                                  expected_workdays), 2),
        'ECO-cheques': ecocheque,
        'Hospitalisatieverz.': round(global_hr_values.loc['HR041', 'waarde'] * 1.25 / 12, 2),
        'Groepsverz.': round(global_hr_values.loc['HR113', 'waarde'] * contract_frame.loc[contract_id, 'fte']
                             * company_paid_ratio / 12, 2),
        'Administratie Securex': round(global_hr_values.loc['HR100', 'waarde'] / 12, 2),
        'Verzekering BA': round(global_hr_values.loc['HR110', 'waarde'] * monthly_revenue, 2),
        'Verzekering AO': round(global_hr_values.loc['HR111', 'waarde'] / 12, 2),
        'Mobiliteitskost': round(contract_frame.loc[contract_id, 'monthly_mobility'], 2),
        'Opleiding': round(global_hr_values.loc['HR120', 'waarde'] / 12, 2),
        'Attenties en activiteiten': round((global_hr_values.loc['HR140', 'waarde']
                                            + global_hr_values.loc['HR141', 'waarde']) / 12, 2),
        'Preventie': round((global_hr_values.loc['HR130', 'waarde'] + global_hr_values.loc['HR101', 'waarde']) / 12, 2),
        'ICT': round((global_hr_values.loc['HR150', 'waarde'] + global_hr_values.loc['HR151', 'waarde'] +
                     global_hr_values.loc['HR152', 'waarde'] + global_hr_values.loc['HR153', 'waarde']) / 12, 2),
    }
    return cost_overview


def monthly_revenue(employee_id: int, ref_date: datetime) -> (float, float):
    """Calculate expected monthly employee revenue before and after substracting MSP fee, using calendar"""
    project_id, project_start, project_end = calculate_project.get_consultant_project(employee_id, ref_date)
    dayrate, msp_fee = calculate_project.get_project_dayrate(project_id)
    if project_id == 99999:
        gh.logger(f"No project found for employee {employee_id} in month {ref_date.month}, setting dayrate to 0.00.")
        return 0.00, 0.00
    # define actual date range for reference period, from the first until the last of the month
    period_start = ref_date.replace(day=1)
    period_end = ref_date.replace(day=calendar.monthrange(ref_date.year, ref_date.month)[1])
    # calculate start and end for billable period, if project starts during the month this is correctly taken in account
    start_date = max(period_start, project_start)
    # make sure end date is not before start date
    end_date = max(min(period_end, project_end), start_date)
    workhours = calculate_calendar.get_workhours(employee_id, start_date, end_date, True)
    revenue = workhours * (dayrate/8)
    return revenue, revenue * (1 - msp_fee)


def get_monthly_summary_data(ref_date: datetime) -> (pd.DataFrame, pd.DataFrame):
    """Create two dataframes showing all different costs and incomes for all employees in a month
    These dataframe only include individual costs (salary package, ICT of individual employee, training,
    etc.) and income but do NOT include general company costs, management and administration cost
    """
    worker_list = db_supply.worker_list_get('intern')
    cost_list = []
    revenue_list = []
    # get all employee contracts valid on ref_date
    empl_contracts = db_supply.employee_contracts_get(ref_date)
    # loop over all employee contracts
    for index, row in empl_contracts.iterrows():
        contract_id = index
        employee_id = row['employee_id']
        revenue, revenue_msp = monthly_revenue(employee_id, ref_date)
        cost_empl = monthly_cost(contract_id, ref_date, empl_contracts, worker_list, revenue)
        cost_list.append(cost_empl)
        revenue_empl = {'Medewerker': cost_empl['Medewerker'], 'Inkomsten na MSP': revenue_msp}
        revenue_list.append(revenue_empl)
    return (pd.DataFrame.from_records(cost_list).set_index(['Medewerker']),
            pd.DataFrame.from_records(revenue_list).set_index(['Medewerker']))


def monthly_summary(cost_overview: pd.DataFrame, revenue_overview: pd.DataFrame) -> pd.DataFrame:
    """Create summary dataframe showing employee cost, income and margin for month or year"""
    ignore_list = json.loads(config.g_config.get('PARAMETERS', 'ignore_list'))
    overview = []
    # list of columns from the cost_overview dataframe that we want to include in the summary
    costs_to_include = ['Bezoldiging', 'Provisie vakantiegeld', 'Provisie eindejaarspremie', 'RSZ werkgever',
                        'Premie-PC200', 'Bonus', 'Nettovergoeding', 'Maaltijdcheques', 'ECO-cheques',
                        'Hospitalisatieverz.', 'Groepsverz.', 'Administratie Securex', 'Verzekering BA',
                        'Verzekering AO', 'Mobiliteitskost', 'Opleiding', 'Attenties en activiteiten', 'Preventie',
                        'ICT']
    for i in cost_overview.index.tolist():
        cost = cost_overview.loc[i, costs_to_include].sum(axis=0)
        income = revenue_overview.loc[i].sum(axis=0)
        margin = income - cost
        # if summary dataframe is not for full year, then do not include margin percentage
        overview_one_empl = {'Medewerker': i, 'Kostprijs': round(cost, 2), 'Omzet': round(income, 2),
                             'Bruto marge': round(margin, 2)}
        overview.append(overview_one_empl)
    overview_frame = pd.DataFrame.from_records(overview).set_index(['Medewerker'])
    # drop employees in ignore list
    try:
        overview_frame.drop(ignore_list, inplace=True)
    except KeyError:
        gh.logger("Some employees in Ignorelist were not found in employee cost overview, please correct"
                  "this.", 'ERROR')
    # sort dataframe by index
    overview_frame.sort_index(inplace=True)
    return overview_frame


def get_year_of_monthly_summaries():
    """Get all monthly employee summaries, starting with current month of ref_date, for the whole year"""
    ref_date = config.g_ref_date
    # create dictionary to store the monthly employee summaries
    monthly_employee_summaries = {}
    # loop over all months of the year, starting from the current month
    for month in range(ref_date.month, 13):
        month_date = datetime(ref_date.year, month, 1)
        monthly_cost, monthly_income = get_monthly_summary_data(month_date)
        # get summarized employee data for the month, and append to dictionary
        monthly_employee_summaries[month] = monthly_summary(monthly_cost, monthly_income)
    return monthly_employee_summaries


def evaluate_contract_start_end(contract_id: int, contract_frame: pd.DataFrame, ref_date: datetime, period: str)\
        -> bool:
    """Evaluate if contracts are starting or ending in the current month / year"""
    start_date = contract_frame.loc[contract_id, 'start_date']
    end_date = contract_frame.loc[contract_id, 'end_date']
    if period == 'm':
        start_window = (ref_date.replace(day=2)).date()
        end_window = (ref_date.replace(day=(calendar.monthrange(ref_date.year, ref_date.month)[1] - 1))).date()
    elif period == 'y':
        start_window = (ref_date.replace(month=1, day=2)).date()
        end_window = (ref_date.replace(month=12, day=(calendar.monthrange(ref_date.year, 12)[1] - 1))).date()
    else:
        raise ValueError("In function evaluate_contract_start_end argument 'period' must be 'm' or 'y'")
    # return True if contract starts or ends in the current month
    return start_window <= start_date <= end_window or start_window <= end_date <= end_window


def yearly_cost_income(employee_id: int, real_calendar: bool = False) -> (pd.DataFrame, float, pd.DataFrame):
    """Simulates yearly cost, income and margin for a single employee. This function looks at the project and
    employment situation on ref_date and assumes this situation is constant for the whole year. The calculations are the
    same as those done by the loonberekening Excel file
    The real_calendar parameter is used to determine if the actual workdays and billable days should be used, or if the
    configured "average" billable days are used
    Function returns the calculation results as well as the parameters for display by a html parsing function.
    """
    ref_date = config.g_ref_date
    # get global hr values
    global_hr_values = db_supply.global_hr_values
    # get contract data
    contract_frame = db_supply.employee_contracts_get(ref_date)
    contract_id = contract_frame[contract_frame['employee_id'] == employee_id].index[0]

    # evaluate if contract is starting or ending in the current year
    contract_change = evaluate_contract_start_end(contract_id, contract_frame, ref_date, 'y')
    if contract_change:
        gh.logger(f"Contract for {employee_id} is starting or ending in year {ref_date.year}.")

    # todo: review all FTE logic whether it still makes sense!!!
    # calculate correction factor FTE, to take into the actual fte time that are paid hours
    company_paid_ratio, vacation_time_ratio = calculate_calendar.get_fte_ratios(
        employee_id,
        ref_date.replace(month=1, day=1),
        ref_date.replace(month=12, day=31),
        False)
    # calculate workdays and billable days
    if real_calendar:
        yearly_workdays = calculate_calendar.get_workhours(employee_id, ref_date.replace(month=1, day=1),
                                                           ref_date.replace(month=12, day=31), False) / 8
        yearly_billable_days = calculate_calendar.get_workhours(employee_id, ref_date.replace(month=1, day=1),
                                                                ref_date.replace(month=12, day=31), True) / 8
    else:
        yearly_billable_days = (int(config.g_config.get('PARAMETERS', 'yearly_workdays')) *
                                contract_frame.loc[contract_id, 'fte'] * company_paid_ratio)
        # to stay aligned with tool in Excel we simplify by assuming workdays equals billable days
        yearly_workdays = yearly_billable_days

    # get FTE correction factors
    actual_fte = contract_frame.loc[contract_id, 'fte'] * company_paid_ratio

    # calculate yearly revenue
    project_id, project_start, project_end = calculate_project.get_consultant_project(employee_id, ref_date)
    dayrate, msp_fee = calculate_project.get_project_dayrate(project_id)
    yearly_revenue = yearly_billable_days * dayrate * (1 - msp_fee)

    # calculate gross salary
    bezoldiging = (contract_frame.loc[contract_id, 'monthly_salary'] * company_paid_ratio
                   * config.g_config.getfloat('PARAMETERS', 'inflator'))

    # calculate full cost matrix
    cost_overview = {
        'Employee': employee_id,
        'Bezoldiging': round(bezoldiging * 12, 2),
        'Maaltijdcheques': round((global_hr_values.loc['HR010', 'waarde'] * global_hr_values.loc['HR012', 'waarde'] *
                                  yearly_workdays), 2),
        'RSZ werkgever': round(bezoldiging * 12 * global_hr_values.loc['HR401', 'waarde'], 2),
        'Eindejaarspremie': round(bezoldiging * (1 + global_hr_values.loc['HR401', 'waarde']), 2),
        'Premie-PC200': round(get_pc200_premium(employee_id, global_hr_values), 2),
        'Bonus': round(get_bonus(contract_id, contract_frame, global_hr_values), 2),
        'Dubbel vakantiegeld': round(get_vakantiegeld(bezoldiging, 1), 2),
        'Nettovergoeding': round(get_net_allowance(contract_id, contract_frame, global_hr_values) * 12, 2),
        'ECO-cheques': round(get_eco_cheques(employee_id, global_hr_values), 2),
        'Hospitalisatieverz.': round(global_hr_values.loc['HR041', 'waarde'] * 1.25, 2),
        'Groepsverz.': round(global_hr_values.loc['HR113', 'waarde'] * contract_frame.loc[contract_id, 'fte'] *
                             company_paid_ratio, 2),
        'Administratie Securex': round(global_hr_values.loc['HR100', 'waarde'], 2),
        'Verzekering BA': round(global_hr_values.loc['HR110', 'waarde'] * yearly_revenue, 2),
        'Verzekering AO': round(global_hr_values.loc['HR111', 'waarde'], 2),
        'Mobiliteitskost': round(contract_frame.loc[contract_id, 'monthly_mobility'] * 12, 2),
        'Opleiding, attenties en activiteiten': round(global_hr_values.loc['HR120', 'waarde'] +
                                                      global_hr_values.loc['HR140', 'waarde'] +
                                                      global_hr_values.loc['HR141', 'waarde'], 2),
        'Preventie': round((global_hr_values.loc['HR130', 'waarde'] + global_hr_values.loc['HR101', 'waarde']), 2),
        'ICT': round((global_hr_values.loc['HR150', 'waarde'] + global_hr_values.loc['HR151', 'waarde'] +
                     global_hr_values.loc['HR152', 'waarde'] + global_hr_values.loc['HR153', 'waarde']), 2),
        'Management tijd': round(global_hr_values.loc['HR080', 'waarde'], 2),
        'Administratie': round(global_hr_values.loc['HR081', 'waarde'], 2),
        'Algemene kosten': round(global_hr_values.loc['HR200', 'waarde'], 2),
    }

    # parameters
    parameters = {
        'Employee': employee_id,
        'Level': contract_frame.loc[contract_id, 'function_category'],
        'Mobility': contract_frame.loc[contract_id, 'mobility_type'],
        'Maandloon': contract_frame.loc[contract_id, 'monthly_salary']
                     * config.g_config.getfloat('PARAMETERS', 'inflator'),
        'FTE': actual_fte,
        'Billable dagen': yearly_billable_days,
        'Dayrate': dayrate,
        'MSP fee': msp_fee,
    }

    table_cost_overview = pd.DataFrame.from_records([cost_overview], index='Employee')
    table_parameters = pd.DataFrame.from_records([parameters], index='Employee')

    # return results
    return table_cost_overview, yearly_revenue, table_parameters
