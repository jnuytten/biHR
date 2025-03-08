# biHR
biHR is a program written in Python that does data analysis of cost, income and margin
of a consultancy company, or other company working with daily or hourly rates.
The data is retrieved from the Officient API and CSV files, and stored in a MySQL
database.

Note from the developer: this project as well as this README file are work in progress.

## Installation
1. Clone the repository
2. Install the required packages with `pip install <package>`,
the following packages are required: `pandas`, `mysql-connector-python`, `datetime`, `holidays`, `Configparser`, `Dash`, `Python.dotenv`  
3. Create a MySQL database and import the `setup/create_tables.sql` file
4. Create a `.env` file in the root directory and add the following variables:
```
db_host = <your sql host>
db_user = <your sql user>
db_password = <your sql password>
db_name = <your sql database name>
officient_key = <your officient api key>
```
5. Set configuration in the `config.ini` file
6. Run the `refresh_data.py`script to get data from Officient and CSV files to the SQL database 
7. Run the `app.py` file

## Usage
The program is run from the `app.py` file.
Data can be visualized using Dash in a browser.

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see
<https://www.gnu.org/licenses/>.

Copyright (C) 2024 Joachim Nuyttens
