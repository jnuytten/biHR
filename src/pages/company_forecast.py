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
# This file contains structure and functions to display the company forecast page.
#

from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
from app import app, global_dataframes

cost_frame = global_dataframes['cost_frame']

layout = html.Div([
    html.H1("Page 1 - Cost Frame"),
    dash_table.DataTable(
        id='table-cost_frame',
        columns=[{'name': col, 'id': col, 'editable': True} for col in cost_frame.columns],
        data=cost_frame.to_dict('records'),
        editable=True
    ),
    dcc.Graph(id='graph-cost_frame')
])

@app.callback(
    Output('graph-cost_frame', 'figure'),
    Input('table-cost_frame', 'data')
)
def update_graph_cost_frame(data):
    df = pd.DataFrame(data)
    fig = px.line(df, x='A', y='B', title='Cost frame Visualization')
    return fig