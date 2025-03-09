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
# This function file contains all functions used to retrieve data from Officient API and input files, and to
# put this data into the SQL database.
#
import configparser
import pandas as pd
from typing import Dict
from datetime import datetime
from src.utils import calculate_calendar, officient_api_queries, db_supply, config, gen_helpers as gh


def employee_list_get() -> pd.DataFrame:
    """Get JSON object from Officient API with all active employees"""
    employee_data = officient_api_queries.get_json("https://api.officient.io/1.0/people/list?include_archived=0")
    # extract relevant data
    relevant_data = []
    for item in employee_data['data']:
        # for each employee execute one additional api query to get the team name
        item_detail = officient_api_queries.get_json(f"https://api.officient.io/1.0/people/{item['id']}/detail")
        # append employee data to the list
        relevant_data.append({
            'Id': item['id'],
            'Name': item['name'],
            'Role': item['role_name'],
            'Team': item_detail['data']['team']['name']})
    return pd.DataFrame(relevant_data)


def freelance_list_get(freelancefile: str) -> pd.DataFrame:
    """Get dictionary?? from Excel file with freelancers"""
    # define freelance dataframe from csv file
    dtype = {'Freelancer': str, 'Name': str, 'Id': int}
    freelance_list = pd.read_csv(freelancefile, dtype=dtype, sep=';')
    # add new column to contract_frame for storing initials
    freelance_list.insert(2, "Role", 'Freelance', True)
    # put columns in right order
    freelance_list = freelance_list[['Id', 'Name', 'Role']]
    # add team column for all freelancers with value "Projects & Business Development"
    freelance_list['Team'] = "Projects & Business Development"
    return freelance_list


def worker_list_db_exec(workers: pd.DataFrame):
    """Helper function inserting a dataframe with workers in the database
    ON DUPLICATE KEY UPDATE ensures that when id already exists the value
    is updated instead of added to the database"""
    query = """
    INSERT INTO people_workers (id, name, role_name, team)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    role_name = VALUES(role_name)
    """
    records = workers.values.tolist()
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, records)
            conn.commit()


def workers_list_compose(freelancefile: str):
    """Compose a unified list of all employees and freelancers and insert into SQL"""
    freelance_list = freelance_list_get(freelancefile)
    employee_list = employee_list_get()
    # check required columns exist
    gh.check_col_exists(freelance_list, ['Id', 'Name', 'Role', 'Team'])
    gh.check_col_exists(employee_list, ['Id', 'Name', 'Role', 'Team'])
    # check for missing values
    missing_values = freelance_list.isnull().sum() + employee_list.isnull().sum()
    if missing_values.any():
        raise ValueError('Input dataframe is missing required values: freelance_list')
    # empty table
    gh.truncate_table("people_workers")
    # insert into SQL
    worker_list_db_exec(freelance_list)
    worker_list_db_exec(employee_list)


def employee_calendar_get(employee_id: int, year: int) -> Dict[str, any]:
    """Get JSON object from Officient API with one year calendar of employee"""
    return officient_api_queries.get_json(f"https://api.officient.io/1.0/calendar/{employee_id}/{year}")


def employee_calendar_db_exec(employee_id: int, date: str, scheduled_time: int, absence_durations: Dict[str, int]):
    """Helper function inserting one record in the database
    ON DUPLICATE KEY UPDATE ensures that when combination employee_id with date already exists the value
    is updated instead of added to the database
    """
    query = """
    INSERT INTO calendar_workday (employee_id, date, scheduled_time, training_time, vacation_time, holiday_time,
    adv_time, extralegal_vacation_time, paid_leave_time_total, unpaid_leave_time_total, paid_sick_time,
    unpaid_sick_time, sick_time_total)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    scheduled_time = VALUES(scheduled_time),
    training_time = VALUES(training_time),
    vacation_time = VALUES(vacation_time),
    holiday_time = VALUES(holiday_time),
    adv_time = VALUES(adv_time),
    extralegal_vacation_time = VALUES(extralegal_vacation_time),
    paid_leave_time_total = VALUES(paid_leave_time_total),
    unpaid_leave_time_total = VALUES(unpaid_leave_time_total),
    paid_sick_time = VALUES(paid_sick_time),
    unpaid_sick_time = VALUES(unpaid_sick_time),
    sick_time_total = VALUES(sick_time_total)
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (
                employee_id, date, scheduled_time,
                absence_durations.get('training_time', 0),
                absence_durations.get('vacation_time', 0),
                absence_durations.get('holiday_time', 0),
                absence_durations.get('adv_time', 0),
                absence_durations.get('extralegal_vacation_time', 0),
                absence_durations.get('paid_leave_time_total', 0),
                absence_durations.get('unpaid_leave_time_total', 0),
                absence_durations.get('paid_sick_time', 0),
                absence_durations.get('unpaid_sick_time', 0),
                absence_durations.get('sick_time_total', 0)
            ))
            conn.commit()


def employee_calendar_insert(calendar_data: Dict[str, any], employee_id: int):
    """Append JSON data to SQL database"""
    # retrieve company holidays
    company_days_off = {day['date']: day['name'] for day in calendar_data['data']['company_days_off']}
    # Insert time off data
    for day in calendar_data['data']['time_off']:
        date = day['date']
        scheduled_time = day['scheduled_minutes']
        absence_durations = {
            "training_time": 0,
            "vacation_time": 0,
            "holiday_time": 0,
            "adv_time": 0,
            "extralegal_vacation_time": 0,
            "paid_leave_time_total": 0,
            "unpaid_leave_time_total": 0,
            "paid_sick_time": 0,
            "unpaid_sick_time": 0,
            "sick_time_total": 0
        }
        for event in day['events']:
            if event['name'] == "Training Day":
                absence_durations["training_time"] += event['duration_minutes']
            elif event['name'] in ("Vakantie", "Inhaalrust", "Vervangingsfeestdag", "Conventionele vakantiedagen",
                                   "klein verlet"):
                absence_durations["paid_leave_time_total"] += event['duration_minutes']
                # for those absence types which have a saldi, add them to separate counters
                if event['name'] == "Vakantie":
                    absence_durations["vacation_time"] += event['duration_minutes']
                if event['name'] == "Inhaalrust":
                    absence_durations["adv_time"] += event['duration_minutes']
                if event['name'] == "Vervangingsfeestdag":
                    absence_durations["holiday_time"] += event['duration_minutes']
                if event['name'] == "Conventionele vakantiedagen":
                    absence_durations["extralegal_vacation_time"] += event['duration_minutes']
            elif event['name'] in ("Verlof zonder wedde", "Jeugdvakantie", "Ouderschapsverlof", "Ouderschapsverlof-5",
                                   "Dringende familiale reden", "Dwingende familiale reden", "Geboorteverlof",
                                   "Aanvullende Vakantie (Eu) - Bedienden - Betaald"):
                absence_durations["unpaid_leave_time_total"] += event['duration_minutes']
            elif event['name'] == "Sick day":
                absence_durations["paid_sick_time"] += event['duration_minutes']
                absence_durations["sick_time_total"] += event['duration_minutes']
            elif event['name'] in ("Thuiswerk", "Vrijwillige overuren zonder recup", "Recuperatie overuren",
                                   "Overuren zonder recuperatie", "Netto Relance-overuren zonder recuperatie"):
                pass
            else:
                raise ValueError(f"Unknown event name: {event['name']}")
        # Add company days off to paid_leave_time if there are scheduled minutes
        if day['date'] in company_days_off and day['scheduled_minutes'] > 0:
            absence_durations['paid_leave_time_total'] += day['scheduled_minutes']
        # Use helper function to insert into database
        employee_calendar_db_exec(employee_id, date, scheduled_time, absence_durations)


def employee_calendar_delete(employee_id: int, year: int):
    """Remove all records in the table of given employee in a given year"""
    query = """
    DELETE FROM calendar_workday
    WHERE employee_id = %s AND YEAR(date) = %s
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (employee_id, year))
            conn.commit()


def employee_calendar_compose(year: int):
    """Compose the full calendar of all listed non-freelance employees for the current year in SQL"""
    worker_list = db_supply.worker_list_get('intern')
    for i in worker_list.index.tolist():
        calendar = employee_calendar_get(i, year)
        employee_calendar_insert(calendar, i)


def employee_saldi_get(employee_id: int, year: int) -> Dict:
    """Get JSON object from Officient API with all saldi and get year saldi, then correct by saldi already taken from
    SQL database. All times are expressed in minutes!"""
    # retrieve year limits of employee for year from Officient API
    year_limit_data = officient_api_queries.get_json(f"https://api.officient.io/1.0/calendar/{employee_id}"
                                                     f"/events/types/{year}/limits")
    # retrieve data from JSON object and put into dictionary per absence type
    absence_types = ["Vakantie", "Inhaalrust", "Vervangingsfeestdag", "Conventionele vakantiedagen"]
    year_limits = {}
    for item in year_limit_data['data']:
        if item['name'] in absence_types:
            if item['limitation'] == 'limit_in_minutes':
                year_limits[item['name']] = item['max_yearly_amount_minutes']
            elif item['limitation'] == 'limit_in_days':
                year_limits[item['name']] = item['max_yearly_amount_days'] * 8 * 60
    # for sickness and training days, retrieve from config the historical average values
    year_limits['Ziekte'] = config.g_config.getint('PARAMETERS', 'yearly_sick_days') * 8 * 60
    year_limits['Training'] = config.g_config.getint('PARAMETERS', 'yearly_training_days') * 8 * 60
    # get employee calendar for this year from SQL
    calendar = db_supply.employee_calendar_get(employee_id, year)
    # calculate remaining saldi of the year by substracting from year limits the days already used (as in calendar)
    saldi = {}
    saldi['employee_id'] = employee_id
    saldi['training'] = int(max(0, year_limits['Training'] - calendar['training_time'].sum()))
    saldi['vacation'] = int(year_limits['Vakantie'] - calendar['vacation_time'].sum())
    saldi['holiday'] = int(year_limits['Vervangingsfeestdag'] - calendar['holiday_time'].sum())
    saldi['adv'] = int(year_limits['Inhaalrust'] - calendar['adv_time'].sum())
    saldi['extralegal_vacation'] = int(year_limits['Conventionele vakantiedagen'] -
                                       calendar['extralegal_vacation_time'].sum())
    saldi['sickness'] = int(max(0, year_limits['Ziekte'] - calendar['sick_time_total'].sum()))
    for absence_saldi in saldi:
        if saldi[absence_saldi] < 0:
            saldi[absence_saldi] = 0
            print(f'Calculated remaining saldi for employee {employee_id} of type {absence_saldi} is below'
                             f'zero. Setting to zero.')
    return saldi


def employee_saldi_db_exec(saldi_dict: Dict):
    """Helper function inserting a dataframe with absence saldi in the database
    ON DUPLICATE KEY UPDATE ensures that when id already exists the value
    is updated instead of added to the database"""
    record_tuple = (saldi_dict['employee_id'], saldi_dict['training'], saldi_dict['vacation'], saldi_dict['holiday'],
                    saldi_dict['adv'], saldi_dict['extralegal_vacation'], saldi_dict['sickness'])
    query = """
    INSERT INTO calendar_saldi (employee_id, training, vacation, holiday, adv, extralegal_vacation, sickness)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    training = VALUES(training),
    vacation = VALUES(vacation),
    holiday = VALUES(holiday),
    adv = VALUES(adv),
    extralegal_vacation = VALUES(extralegal_vacation),
    sickness = VALUES(sickness)
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, record_tuple)
            conn.commit()


def employee_saldi_compose(year: int):
    """Compose a unified list of all employee absence saldi"""
    # loop over employees
    worker_list = db_supply.worker_list_get('intern')
    for i in worker_list.index.tolist():
        saldi_line = employee_saldi_get(i, year)
        # insert into SQL
        employee_saldi_db_exec(saldi_line)


def employee_contract_get(employee_id: int) -> Dict[str, any]:
    """Get JSON object from Officient API with all contracts of an employee"""
    return officient_api_queries.get_json(f"https://api.officient.io/1.0/wages/{employee_id}/history")


def employee_budget_get(employee_id: int, year: int) -> Dict[str, any]:
    """Get JSON object from Officient API with all budgets of an employee"""
    return officient_api_queries.get_json(f"https://api.officient.io/1.0/budgets/people/{employee_id}/{year}/list")


def employee_mobility_cost(employee_id: int, start_date: datetime, contract: list)\
        -> tuple:
    """Calculate the actual monthly mobility cost"""
    # if contract stipulates a car, just return the monthly car cost as in the contract
    if contract['estimated_monthly_cost']['base_components']['car'] != 0:
        return "car", contract['estimated_monthly_cost']['base_components']['car']
    else:
        # DEBUG: this code is currently not working due to a bug in Officient not showing mobility budgets
        # if no car, then see if there is a LEGAL budget (= mobiliteitsbudget)
        #budget_data = employee_budget_get(employee_id, start_date.year)
        #for budget in budget_data['data']:
        #    if budget['budget_type'] == 'LEGAL':
                # take into account real fte to factor in part-time work, start_date is date the contract starts (to
                # avoid doing the calculations over periods before the contract starts) and end_date is the 31st of
                # december in the same year as start_date
        #        end_date = datetime(start_date.year, 12, 31)
        #        company_paid_ratio, vacation_time_ratio = calculate_calendar.get_fte_ratios(employee_id, start_date,
        #                                                                                    end_date,
        #                                                                                    True)
        # if there is a budget, then calculate monthly cost based on 20% year salary and contract fte
        #DEBUG: temporary workardound
        if gh.get_consultant_function(employee_id) != "Management Assistant":
            end_date = datetime(start_date.year, 12, 31)
            company_paid_ratio, vacation_time_ratio = calculate_calendar.get_fte_ratios(employee_id, start_date,
                                                                                                end_date,
                                                                                                True)
            return "budget", 13 * contract['rate'] * 0.2 * company_paid_ratio / 12
        # if no car and no budget, return fixed allowance
        return "allowance", 80


def employee_contract_db_exec(contract_id: int, employee_id: int, function_category: str, start_date: str,
                              end_date: str, monthly_salary: float, mobility_type: str, monthly_mobility: float,
                              fte: float):
    """Helper function inserting one record (one contract) in the database
    ON DUPLICATE KEY UPDATE ensures that when contract_id exists the value
    is updated instead of added to the database
    """
    # SQL query to insert contracts
    query = """
    INSERT INTO people_employee_contracts (id, employee_id, function_category, start_date, end_date, monthly_salary,
    mobility_type, monthly_mobility, fte)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    id = VALUES(id),
    employee_id = VALUES(employee_id),
    function_category = VALUES(function_category),
    start_date = VALUES(start_date),
    end_date = VALUES(end_date),
    monthly_salary = VALUES(monthly_salary),
    mobility_type = VALUES(mobility_type),
    monthly_mobility = VALUES(monthly_mobility),
    fte = VALUES(fte)
    """
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            # enter records
            cursor.execute(query, (
                contract_id, employee_id, function_category, start_date, end_date, monthly_salary, mobility_type,
                monthly_mobility, fte
            ))
            conn.commit()


def employee_contract_insert(contract_data: Dict[str, any], employee_id: int):
    """"This function inserts the contract list of an employee into SQL
    All costs of the contract are expressed on a monthly basis, based on the contractual fte (i.e. not taking
    into account parental leave or parental part-time work)
    """
    # loop over contracts and insert them into the database
    for contract in contract_data['data']:
        end_date = contract['end_date']
        # if end date is empty, set it to a very high value
        if end_date == '':
            end_date = "2100-12-31"
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        # skip contracts which ended before today
        if end_datetime < datetime.now():
            continue
        # get rest of the data
        start_date = contract['start_date']
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        fte = contract['custom_payroll_data']['avg_working_hours_per_week'] / 40
        # get mobility type and monthly amount
        mobility = employee_mobility_cost(employee_id, start_datetime, contract)
        # do some sanity checks before proceeding
        if mobility[1] < 1:
            raise ValueError(f"Mobility cost missing for {employee_id}")
        if mobility[1] > 2000:
            print(f"Mobility cost suspiciously of {mobility[1]} high for {employee_id}")
        if contract['rate'] < 1:
            raise ValueError(f"Monthly salary missing for {employee_id}")
        if contract['rate'] > 10000:
            raise ValueError(f"Monthly salary of {contract['rate']} impossibly high for employee {employee_id}")
        if not 0 <= fte <= 1:
            raise ValueError(f"Impossible FTE value of {fte} for {employee_id}")
        if not 1 <= contract['id'] <= 9999999999:
            raise ValueError(f"Impossible contract id value of {contract['id']} for {employee_id}")

        # Use helper function to insert into database
        employee_contract_db_exec(
            contract['id'], employee_id, contract['custom_payroll_data']['professional_details']['function'],
            start_date, end_date, contract['rate'], mobility[0], mobility[1], fte)


def employee_contract_compose():
    """Compose a unified list of all employee contracts and insert into SQL"""
    # first empty table
    gh.truncate_table("people_employee_contracts")
    # then create and loop over worker list
    worker_list = db_supply.worker_list_get('intern')
    print(worker_list.index.tolist())
    for employee_id in worker_list.index.tolist():
        contract_data = employee_contract_get(employee_id)
        employee_contract_insert(contract_data, employee_id)


def project_get(csvfile: str) -> pd.DataFrame:
    """Get a list of projects from csv file into a dataframe"""
    dtype = {'Consultant': str, 'Consultant id': int, 'Categorie': str, 'Klant': str, 'MSP Fee': float,
             'Startdatum': str, 'Einddatum': str, 'Percentage': float, 'Uurtarief': float, 'Dagtarief': float,
             'Freelance uurtarief': float, 'Freelance dagtarief': float}
    project_frame = pd.read_csv(csvfile, dtype=dtype, decimal=',', sep=';')
    project_frame.fillna({
        'Einddatum': '2100/12/31',
        'Freelance uurtarief': 0,
        'Freelance dagtarief': 0
    }, inplace=True)
    project_frame['Uurtarief'] = project_frame['Uurtarief'].apply(lambda x: round(x, 2))
    project_frame['Freelance uurtarief'] = project_frame['Freelance uurtarief'].apply(lambda x: round(x, 2))
    # check all columns exist in contract_frame
    col_list = list(dtype.keys())
    gh.check_col_exists(project_frame, col_list)
    return project_frame


def project_db_exec(projects: pd.DataFrame):
    """Helper function inserting a dataframe with projects in the database
    ON DUPLICATE KEY UPDATE ensures that when id already exists the value
    is updated instead of added to the database"""

    # SQL query to insert new records into the table
    query = """
    INSERT INTO projects (client, msp_percentage, start_date, end_date, percentage, hourly_rate, employee_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    client = VALUES(client),
    msp_percentage = VALUES(msp_percentage),
    start_date = VALUES(start_date),
    end_date = VALUES(end_date),
    percentage = VALUES(percentage),
    hourly_rate = VALUES(hourly_rate),
    employee_id = VALUES(employee_id)
    """
    records = projects.values.tolist()
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            # enter records
            cursor.executemany(query, records)
            conn.commit()


def project_insert(projects_freelancers: pd.DataFrame):
    # compose dataframe with correct columns and order
    projects = projects_freelancers[['Klant', 'MSP Fee', 'Startdatum', 'Einddatum', 'Percentage', 'Uurtarief',
                                     'Consultant id']]
    # rename columns
    projects_renamed = projects.rename(columns={
        'Klant': 'client',
        'MSP Fee': 'msp_percentage',
        'Startdatum': 'start_date',
        'Einddatum': 'end_date',
        'Percentage': 'percentage',
        'Uurtarief': 'hourly_rate',
        'Consultant id': 'employee_id'
    })
    # check required columns exist
    gh.check_col_exists(projects_renamed, ['client', 'msp_percentage', 'start_date', 'end_date', 'percentage',
                                           'hourly_rate', 'employee_id'])
    # insert into SQL
    project_db_exec(projects_renamed)


def freelance_contract_db_exec(freelancers: pd.DataFrame):
    """Helper function inserting a dataframe with freelancers in the database
    ON DUPLICATE KEY UPDATE ensures that when id already exists the value
    is updated instead of added to the database"""
    query = """
    INSERT INTO people_freelance_contracts (employee_id, hourly_rate)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
    employee_id = VALUES(employee_id),
    hourly_rate = VALUES(hourly_rate)
    """
    records = freelancers.values.tolist()
    with gh.get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, records)
            conn.commit()


def freelance_contract_insert(projects_freelancers: pd.DataFrame):
    """"This function inserts the list of freelance contracts into SQL"""
    # compose dataframe with correct columns and order
    freelancers_filtered = projects_freelancers[projects_freelancers["Categorie"].str.contains("Freelance")]
    freelancers = freelancers_filtered[['Consultant id', 'Freelance uurtarief']]

    # rename columns
    freelancers_renamed = freelancers.rename(columns={
        'Consultant id': 'employee_id',
        'Freelance uurtarief': 'hourly_rate'
    })
    # check required columns exist
    gh.check_col_exists(freelancers_renamed, ['employee_id', 'hourly_rate'])
    # insert into SQL
    freelance_contract_db_exec(freelancers_renamed)


def project_list_compose(projects_csv: str):
    """Compose a list of freelance contracts and a list of projects into SQL."""
    # first empty projects and freelance contracts table
    gh.truncate_table("projects")
    gh.truncate_table("people_freelance_contracts")
    # then get the data and insert into SQL
    projects_freelancers = project_get(projects_csv)
    project_insert(projects_freelancers)
    freelance_contract_insert(projects_freelancers)
