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
# This function file contains functions which perform calendar specific calculations.
#
import pandas as pd
from datetime import datetime
from src.utils import db_supply


def get_workhours(employee_id: int, start_date: datetime, end_date: datetime, billable: bool) -> float:
    """Get the number of workhours forecasted for a specific employee over a specified period.
    If argument billable is set then training_time is excluded from the calculation.
    Time that is returned is expressed in hours!"""
    if end_date.year > start_date.year:
        raise ValueError("Cannot forecast workhours with function get_workhours over multiple years")
    # get global dataframe with calendar
    global_calendar = db_supply.global_calendar
    if global_calendar is None:
        raise ValueError("global_calendar cannot be accessed in function get_workhours")

    # strip down calendar to applicable employee and period
    filtered_calendar = global_calendar.loc[employee_id]
    filtered_calendar = filtered_calendar[(filtered_calendar.index.get_level_values('date') >= start_date) &
                                          (filtered_calendar.index.get_level_values('date') <= end_date)]

    # get number of minutes in the period
    scheduled_time = filtered_calendar['scheduled_time'].sum()
    if billable:
        leave_time = (filtered_calendar[['paid_leave_time_total', 'unpaid_leave_time_total', 'sick_time_total',
                                            'training_time']].sum().sum())
    else:
        leave_time = (filtered_calendar[['paid_leave_time_total', 'unpaid_leave_time_total', 'sick_time_total']]
                      .sum().sum())

    # correct vacation_time for future months, based on saldi
    absence_forecast = 0
    if end_date > datetime.now():
        # get global dataframe with saldi
        global_saldi = db_supply.global_saldi
        if global_saldi is None:
            raise ValueError("global_saldi cannot be accessed in function get_workhours")
        if billable:
            absence_minutes_left = global_saldi.loc[employee_id, ['training', 'vacation', 'holiday', 'adv',
                                                              'extralegal_vacation', 'sickness']].sum().sum()
        else:
            absence_minutes_left = global_saldi.loc[employee_id, ['vacation', 'holiday', 'adv', 'extralegal_vacation',
                                                                  'sickness']].sum().sum()

        # if period ends in current month (which is not december), then no absence minutes are forecasted
        if end_date.month == datetime.now().month and end_date.month != 12:
            absence_forecast = 0
        # else calculate forecasted absence for the period
        else:
            # calculate number of months left in the year and in the period for which we are calculating
            months_left_in_year = 12 - datetime.now().month
            months_left_in_period = end_date.month - max(datetime.now().month, start_date.month) + 1
            # handle special cases to calculate months left
            if start_date.year > datetime.now().year:
                months_left_in_year = 12
                months_left_in_period = end_date.month - start_date.month + 1
            # in case we are in the last month of the year, we must consider all remaining days will be taken that month
            if months_left_in_year == 0:
                months_left_in_year = 1
            # calculate expected absence per month
            monthly_absence_forecast = round(absence_minutes_left / months_left_in_year, 0)
            # calculate forecasted absence for the period
            absence_forecast = months_left_in_period * monthly_absence_forecast

    # calculate and return work hours in calendar
    return round((scheduled_time - leave_time - absence_forecast) / 60, 2)


def get_fte_ratios(employee_id: int, start_date: datetime, end_date: datetime, use_company_workdays: bool)\
        -> (float, float):
    """Get correction factors on fte, return these as two floats
    1) company_paid_ratio being the days paid by the employer to the employee versus the scheduled time for
    that employee in the current month. As such we correct for unpaid leave and unpaid sick time, leave not paid by the
    employer such as jeugdvakantie and ouderschapsverlof, contracts starting or ending in the current month
    2) vacation_time_ratio being the legal vacation days versus the total number of days paid by the employer (i.e.
    scheduled time minus unpaid leave time). The legal vacation days number of future months includes a correction
    factor for vacation saldi.
    Note that for an employee with a part-time contract, the contractual FTE is already reflected in the scheduled time.
    So for an employee on an 80% contract the first calculated factor can be 1.0, if there is no other unpaid leave.
    """
    # get global dataframe with multiyear calendar
    global_multiyear_calendar = db_supply.global_multiyear_calendar
    if global_multiyear_calendar is None:
        raise ValueError("global_multiyear_calendar cannot be accessed in function get_fte_ratios")

    # strip down calendar to applicable period and employee
    filtered_calendar = global_multiyear_calendar.loc[employee_id]
    filtered_calendar = filtered_calendar[(filtered_calendar.index.get_level_values('date') >= start_date) &
                                              (filtered_calendar.index.get_level_values('date') <= end_date)]

    # get number of minutes in the period
    scheduled_time = filtered_calendar['scheduled_time'].sum()
    unpaid_leave = filtered_calendar[['unpaid_leave_time_total', 'unpaid_sick_time']].sum().sum()
    vacation_time = filtered_calendar['vacation_time'].sum()
    absence_forecast = 0

    if end_date > datetime.now():
        # get global dataframe with saldi
        global_saldi = db_supply.global_saldi
        if global_saldi is None:
            raise ValueError("global_saldi cannot be accessed in function get_fte_ratios")
        absence_minutes_left = global_saldi.loc[employee_id, ['vacation']].sum()

        # if period ends in current month (which is not december), then no absence minutes are forecasted
        if end_date.month == datetime.now().month and end_date.month != 12:
            absence_forecast = 0
        # else calculate forecasted absence for the period
        else:
            # calculate number of months left in the year and in the period for which we are calculating
            months_left_in_year = 12 - datetime.now().month
            months_left_in_period = end_date.month - max(datetime.now().month, start_date.month) + 1
            # handle special cases to calculate months left
            if start_date.year > datetime.now().year:
                months_left_in_year = 12
                months_left_in_period = end_date.month - start_date.month + 1
            if months_left_in_year == 0:
                months_left_in_year = 1
            # calculate expected absence per month
            monthly_absence_forecast = round(absence_minutes_left / months_left_in_year, 0)
            # calculate forecasted absence for the period
            absence_forecast = months_left_in_period * monthly_absence_forecast

    vacation_time = round(vacation_time + absence_forecast, 0)

    # if contract is starting or ending in current month or year OR if we need to compare scheduled time with actual
    # workdays in the company (for bonus calculation or ecocheques), we need to adjust for the actual workdays
    if use_company_workdays:
        calendar_time = get_workday_worktime(start_date, end_date)
        # note there is a minor deviation in the calculation, as calendar_time does not reflect part-time contracts
        if calendar_time == 0:
            company_paid_ratio = 0
        else:
            company_paid_ratio = round(((scheduled_time - unpaid_leave) / calendar_time), 2)
        if scheduled_time == unpaid_leave:
            vacation_time_ratio = 0
        else:
            vacation_time_ratio = round((vacation_time / (scheduled_time - unpaid_leave)), 2)
    # in all other cases, employee works full month, scheduled time is a correct measure
    else:
        company_paid_ratio = round(((scheduled_time - unpaid_leave) / scheduled_time), 2)
        vacation_time_ratio = round((vacation_time / (scheduled_time - unpaid_leave)), 2)

    return float(company_paid_ratio), float(vacation_time_ratio)


def get_first_day(employee_id: int, year: int) -> datetime:
    """Return the first workday, the day on which there is scheduled time, for an employee in the given year"""
    calendar = db_supply.employee_calendar_get(employee_id, year)
    filtered_df = calendar[calendar['scheduled_time'] != 0]
    return pd.to_datetime(filtered_df.index[0][1])


def calculate_work_time(date: datetime) -> float:
    """Calculate the number of work minutes in a day"""
    # legacy code, to remove
    # Define Belgian holidays
    #be_holidays = holidays.BE(years=date.year)
    #if date.weekday() >= 5 or date in be_holidays:
    #    return 0
    if date.weekday() >= 5:
        return 0
    else:
        return 480


def build_workday_calendar(year: int):
    """Build a workday calendar defining all official workdays INCLUDING the legal holidays in belgium in a given year
    and the previous year"""
    global global_workdays
    # Generate date range for the entire year
    start_date = datetime(year - 1, 1, 1)
    end_date = datetime(year, 12, 31)
    date_range = pd.date_range(start_date, end_date)

    # Create dataframe
    global_workdays = pd.DataFrame(date_range, columns=['date'])
    global_workdays['work_time'] = global_workdays['date'].apply(calculate_work_time)


def get_workday_worktime(start_date: datetime, end_date: datetime) -> float:
    """Get the number of work minutes in a specific period"""
    global global_workdays
    if global_workdays is None:
        raise ValueError("global_workdays cannot be accessed in function get_workday_workhours")
    return global_workdays[(global_workdays['date'] >= start_date) & (global_workdays['date']
                                                                      <= end_date)]['work_time'].sum()
