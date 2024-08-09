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
# This function file contains all functions used to query the Officient API for data.
#

import requests
import configparser
import os
from dotenv import load_dotenv
from typing import Dict


def get_json(url: str) -> Dict[str, any]:
    """Retrieve JSON object as Dictionary from Officient"""
    # load configuration parameters from .env file
    load_dotenv()
    token = os.getenv('officient_key')
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # raise exception for HTTP errors
    return response.json()
