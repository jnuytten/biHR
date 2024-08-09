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
# This function file contains general helper functions.
#
import pandas as pd
import mysql.connector
import subprocess
import configparser
import os
from dotenv import load_dotenv
from datetime import datetime


def check_col_exists(data_frame: pd.DataFrame, col_list: list):
    """Throw error if listed column is not in dataframe"""
    for column in col_list:
        if column not in data_frame.columns:
            raise ValueError('Input dataframe does not match: column \"' + column + '\" does not exist')
    return 1


def get_db_connection():
    # load configuration parameters
    load_dotenv()
    try:
        # return connection to database
        connection = mysql.connector.connect(
            host=os.getenv('db_host'),
            user=os.getenv('db_user'),
            password=os.getenv('db_password'),
            database=os.getenv('db_name')
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL database: {str(e)}")
        return None


def truncate_table(table_name: str):
    """Helper function emptying given table"""
    # SQL query to empty the table
    delete_query = f"TRUNCATE TABLE {table_name}"
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # empty table
            cursor.execute(delete_query)
            conn.commit()


def get_month_name(month: int) -> str:
    """Return the name of the month as a string"""
    month_names = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september',
                   'oktober', 'november', 'december']
    return month_names[month - 1]


def get_consultant_name(consultant_id: int) -> str:
    """Return the name of the consultant as a string"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT name FROM people_workers WHERE id = {consultant_id}")
            name = cursor.fetchone()[0]
    return name


def create_sql_dump():
    # Get the current date to append to the filename
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    # load configuration parameters from .env file
    load_dotenv()
    user = os.getenv('db_user')
    password = os.getenv('db_password')
    database = os.getenv('db_name')
    # load other configuration parameters
    config = configparser.ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
    config.read('config.ini')
    dump_file_path = config.get('FILES', 'database_dumps')
    dump_file = f"{dump_file_path}/dump_{database}_{date}.sql"

    try:
        # Call the mysqldump command to create an SQL dump
        with open(dump_file, 'w') as f:
            subprocess.run(['mysqldump', '-u', user, '-p'+password, database], stdout=f, check=True)
        print(f"SQL dump created: {dump_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating SQL dump: {str(e)}")


def logger(log_message: str, log_level: str = 'INFO'):
    """Log the message to output, filtering certain messages based on keywords"""
    # read keywords from the external file
    with open('log_keywords.txt', 'r') as file:
        keywords = [line.strip() for line in file.readlines()]

    # Check if the log message contains any of the keywords
    if any(keyword in log_message for keyword in keywords):
        return  # Filter out the log message

    # Log the message (for example, print it)
    print(log_message)
