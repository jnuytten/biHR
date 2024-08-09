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
# This function file contains all functions used generate html reports from loaded data.
#
from datetime import datetime
import pandas as pd
from src.utils import gen_helpers as gh


def month_details_table(monthly_data: pd.DataFrame) -> (float, float, str):
    """Generate table in html format with totals for a specific month, one employee or freelancers"""
    content = ""
    content += monthly_data.to_html()
    # calculate totals
    cost = monthly_data['Kostprijs'].sum()
    revenue = monthly_data['Omzet'].sum()
    margin = monthly_data['Bruto marge'].sum()
    # print totals to html
    content += '<div style="clear: both;"></div>\n'
    content += '<ul>\n'
    content += '<li>Totale omzet: ' + str(round(revenue, 2)) + '</li>\n'
    content += '<li>Totale kost: ' + str(round(cost, 2)) + '</li>\n'
    content += '<li>Totale marge: ' + str(round(margin, 2)) + '</li>\n'
    content += '</ul>\n'
    return cost, revenue, content


def forecast_company_month(month: int, monthly_employee_data: pd.DataFrame, monthly_freelance_data: pd.DataFrame,
                           management_cost: float, administration_cost: float, general_cost: float) -> str:
    """Generate summarized table which is a forecast for the full company (all employees and freelancers) revenues
    and expenses for one specific month"""
    content = f'<h4>Detailoverzicht maand {gh.get_month_name(month)}</h4>\n'
    content += ('<p>Detail van de volledige maand, kosten en inkomsten uitgesplitst per medewerker. Kosten van '
                'medewerkers bevatten NIET de management, administratieve en algemene bedrijfskosten!</p>\n')
    # employee data
    content += '<p><strong>Interne medewerkers</strong></p>\n'
    employee_cost, employee_revenue, employee_table = month_details_table(monthly_employee_data)
    content += employee_table
    # freelance data
    content += '<p><strong>Freelance medewerkers</strong></p>\n'
    freelance_cost, freelance_revenue, freelance_table = month_details_table(monthly_freelance_data)
    content += freelance_table
    # general data
    content += '<p><strong>Algemene kosten</strong></p>\n'
    content += '<ul>\n'
    content += '<li>Management tijd: ' + str(round(management_cost, 2)) + '</li>\n'
    content += '<li>Administratie tijd: ' + str(round(administration_cost, 2)) + '</li>\n'
    content += '<li>Algemene kosten: ' + str(round(general_cost, 2)) + '</li>\n'
    content += '</ul>\n'
    # overall totals
    total_cost = employee_cost + freelance_cost + management_cost + administration_cost + general_cost
    total_revenue = employee_revenue + freelance_revenue
    content += '<p><strong>Maandelijks totaal</strong></p>\n'
    content += '<ul>\n'
    content += '<li>Totale kost: ' + str(round(total_cost, 2)) + '</li>\n'
    content += '<li>Totale omzet: ' + str(round(total_revenue, 2)) + '</li>\n'
    content += '<li>Totale bruto marge: ' + str(round(total_revenue - total_cost, 2)) + '</li>\n'
    content += '</ul>\n'
    # print link to detailed numbers of internal employees
    content += ('<a href="' + f'report-company_{datetime.now().year}_{month}_empl_details.html'
                + '">Detailoverzicht interne medewerkers</a>\n')
    return content


def forecast_employee_year(employee_id: int, employee_name: str, ref_date: datetime, cost_overview: pd.DataFrame,
                           yearly_revenue: float, parameters: pd.DataFrame) -> str:
    """Generate a html report with a simulation of the yearly costs and revenues for a single employee"""
    content = f'<h4>Simulatie jaarlijks voor {employee_name} (id {str(employee_id)})</h4>\n'
    content += (f'<p>Simulatie van jaarlijkse kosten, inkomsten en marge op individuele werknemer. Deze extrapoleert'
                f'de situatie (verloning, project) op datum {ref_date.strftime("%d-%m-%y")} naar het volledige jaar.'
                f'Deze houdt rekening met de echte kalender, en kan dus niet 1-op-1 vergeleken worden met de Excel'
                f'simulatie. Tenzij in functie main_functions.employee_year_simulation vlag real_calendar wordt'
                f'afgezet.</p>\n')
    # parameters
    content += '<p><strong>Parameters van de berekening</strong></p>\n'
    content += (parameters.transpose()).to_html()
    content += "<br><br>"
    # cost details
    content += '<p><strong>Detail kosten</strong></p>\n'
    content += (cost_overview.transpose()).to_html()
    content += "<br><br>"
    # income and margin
    total_cost = cost_overview.iloc[0, :].sum()
    gross_margin = yearly_revenue - total_cost
    relative_margin = (gross_margin / yearly_revenue) * 100
    content += '<p><strong>Inkomsten en marge</strong></p>\n'
    content += '<ul>\n'
    content += '<li>Inkomsten: ' + str(round(yearly_revenue, 2)) + '</li>\n'
    content += '<li>Totaal kosten: ' + str(round(total_cost, 2)) + '</li>\n'
    content += '<li>Bruto marge: ' + str(round(gross_margin, 2)) + '</li>\n'
    content += '<li>Relatieve marge: ' + str(round(relative_margin, 2)) + '%</li>\n'
    content += '</ul>\n'
    return content


def generate_html(filename: str, title: str, content: str):
    """Print html file based on content in html markup"""
    html = f'''
        <html>                                               
            <head>
                <title>{title}</title>
                <link rel="stylesheet" href="styles.css">  
            </head>
            <body>
                <h1>{title}</h1>                
                <div class="content">
                    {content}
                </div>
            </body>
        </html>
        '''
    with open(filename, 'w') as f:
        f.write(html)
    pass
