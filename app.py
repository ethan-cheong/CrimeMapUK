import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import pgeocode
import json
import math

#Plan:

# Prepare grouped datasets for crime type, population number, year, month, LSOA code, MSOA, code

# Compute aggregations upfront in a data processing callback,
# Then feed it to our aggregate mode.


# Heatmap will group by some district - find a way to do this. maybe upload a
# Grouped dataset that changes depending on the option?
# Colour of each district should be: Crime rate per ___ per year.
# Format it like https://dash-gallery.plotly.host/dash-opioid-epidemic/

# On the right, have a select method option: Whole of UK, or selected counties.
# below that, have a select chart option, that provides and plots multiple
# metrics.

# Once you've done that, tidy up everything with refactoring
#. sort out transparency, colours.
# Finally, OPTIMIZE! make fast.

df_street = pd.read_csv("street_data_test.csv")
df_street_agg = pd.read_csv("street_data_agg.csv")

with open('lsoa_boundaries.geojson') as f:
    lsoa = json.load(f)

token = "pk.eyJ1IjoiZXRoYW5jaGVvbmciLCJhIjoiY2tqbWRtdmNnMDN2dTJ3cGVyOHdpaDJuOSJ9.v7rcDmVITTKevrcT5HCXKA"
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

chart_options = ['chart a', 'chart b']

def getPostalCoords(postal_code):
    # Function that takes a UK postal code as a string and returns coords as a df
    return pgeocode.Nominatim('gb').query_postal_code(postal_code)[['latitude','longitude']]

def toList(item):
    if isinstance(item, list):
        return item
    else:
        return [item]

crime_color_map = {
    "Anti-social behaviour": "#DC050C",
    "Bicycle theft": "#E8601C",
    "Burglary": "#F1932D",
    "Criminal damage and arson": "#F6C141",
    "Drugs": "#F7F056",
    "Other crime": "#CAE0AB",
    "Other theft": "#90C987",
    "Possession of weapons": "#4EB265",
    "Public order": "#7BAFDE",
    "Robbery": "#5289C7",
    "Shoplifting": "#1965B0",
    "Theft from the person": "#882E72",
    "Vehicle crime": "#AE76A3",
    "Violence and sexual offences": "#D1BBD7",
}

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([
        html.H1("Monthly UK Crimes"),
        html.P('Information taken from UK Police Force.',
               id='description')
    ], id='header'
    ),

    html.Div([

        html.Div([

            html.Div([
                html.P('Visualisation type:',
                       id='visualisation-type-text'),
                dcc.RadioItems( # Change this into a cool button that changes color!
                    id='visualisation-type-radio-items',
                    options=[
                        {'label': 'Individual Crimes', 'value': 'ind'},
                        {'label': 'Aggregate Crimes', 'value': 'agg'}
                    ],
                    value='ind',
                )
            ],
            style={'display':'inline-block','width': '48%'},
            id='visualisation-type-container'
            ),

            html.Div([
                html.P('Enter a UK postal code (optional):',
                       id='postal-text'),
                dcc.Input(
                    id='postal-input',
                    type='text',
                    placeholder='Postal Code'
                ),
                html.Button(
                    'Enter',
                    id='postal-enter-button',
                    n_clicks=0
                )
            ],
            style={'display':'inline-block', 'float': 'right','width': '48%'},
            id='postal-container'
            ),

            html.Div([
                html.P(
                    'Select the date:',
                    id='date-slider-text'),
                dcc.Slider(
                    id='year-slider',
                    min=df_street['Year'].min(),
                    max=df_street['Year'].max(),
                    value=df_street['Year'].min(),
                    marks={str(year): str(year) for year in df_street['Year'].unique()},
                    step=None
                ),
                html.Div([
                    dcc.Slider(
                        id='month-slider',
                        min=df_street['Month'].min(),
                        max=df_street['Month'].max(),
                        value=df_street['Month'].min(),
                        marks={str(month): str(month) for month in df_street['Month'].unique()},
                        step=None,
                        )]
                        , style = {},
                        id = 'month-slider-div'
                )
            ],
            id='date-container'
            ),

            html.Div([
                html.P(
                    'Filter by crime type:',
                    id='crime-dropdown-text'
                ),
                dcc.Checklist(
                    id='select-all',
                    options=[{'label': 'Select All', 'value': 'On'}],
                    value=[]
                ),
                dcc.Dropdown(
                    id='crime-dropdown',
                    options=[
                        {'label': c, 'value': c} for c in df_street['Crime type'].unique()
                    ],
                    value=['Theft from the person'],
                    multi=True
                ),
                dcc.Checklist(
                    id='highlight',
                    options=[{'label': 'Brighten Individual Crimes', 'value': 'On'}],
                    value=[],
                    style=dict()
                ),
                dcc.RadioItems(
                    id='boundaries',
                    options=[
                        {'label': 'Lower-layer Super Output Area', 'value': 'LSOA'},
                        {'label': 'Middle-layer Super Output Area', 'value': 'MSOA'},
                    ],
                    value='MSOA',
                    style=dict()
                    )
                ],
            style={},
            id='other-options-container'
            ),
        ],
        id='input-container'
        ),

        html.Div([
            html.P('Select chart: ',
                   id='select-chart-text'
            ),
            dcc.Dropdown(
                id='chart-dropdown',
                options=[
                    {'label': chart, 'value': chart} for chart in chart_options
                ],
                value=chart_options[0]
            ),
            dcc.RadioItems(
                id='chart-type-radio-items',
                options=[
                    {'label': 'Whole of UK', 'value': 'whole'},
                    {'label': 'Select from map', 'value': 'select'}
                ],
                value='whole',
                labelStyle={'display':'inline'}
            ),
            dcc.Graph(
                id='selected-chart'
            )

        ],
        id='graph-container'
        ),

    ],
    id='left-column',
    style={'width': '48%', 'display': 'inline-block','background-color': 'powderblue'}
    ),

    html.Div([
        dcc.Graph(
            id='map',
            style={'height': '800px'}
            )
    ],
    style={'width': '48%', 'display': 'inline-block', 'float': 'right',
           'height': '100%'},
    id='right-column'
    )

])

@app.callback(
    Output('month-slider-div', 'style'),
    Output('highlight', 'style'),
    Output('boundaries', 'style'),
    Input('visualisation-type-radio-items', 'value')
)
def changeVisualizationType(current_type):
    if current_type=="ind":
        return [
            dict(),
            dict(),
            dict(display='none')
            ]
    elif current_type=="agg":
        return [
            dict(display='none'),
            dict(display='none'),
            dict()
            ]

@app.callback(
    Output('crime-dropdown', 'value'),
    Input('select-all', 'value'),
    State('crime-dropdown', 'value')
)
def checkSelected(selected, current_values):
    if selected:
        return [c for c in df_street['Crime type'].unique()]
    else:
        return current_values

@app.callback(
    Output('map', 'figure'),
    Input('visualisation-type-radio-items', 'value'),
    Input('postal-enter-button', 'n_clicks'),
    Input('year-slider', 'value'),
    Input('month-slider', 'value'),
    Input('crime-dropdown', 'value'),
    Input('highlight', 'value'),
    State('postal-input','value')
)
def updateMap(current_type, n_clicks, year, month, crime_types, highlight, postal):
    year = int(year)
    month = int(month)
    if current_type == "ind":
        dff = df_street[(df_street['Year']==year) & (df_street['Month']==month) & (df_street['Crime type'].isin(crime_types))]
        if highlight:
            alpha = 1
        else:
            alpha = 0.3

        if postal:
            coords = getPostalCoords(postal)
            center = dict(lat = coords['latitude'].item(), lon = coords['longitude'].item())
            fig = px.scatter_mapbox(dff,
                                    lat="Latitude",
                                    lon="Longitude",
                                    opacity=alpha,
                                    center=center,
                                    color="Crime type",
                                    zoom=14,
                                    color_discrete_map=crime_color_map
                                    )
            fig.update_layout(mapbox_style='dark',
                              mapbox_accesstoken=token,
                              autosize=True,
                              margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
                              legend={'x':0, 'xanchor': 'left',
                                      'bgcolor': 'rgb(25, 26, 26)',
                                      'font_color': 'white',
                                      'title_font_color': 'white'
                                      })
            fig.update_traces(hoverinfo='skip', hovertemplate=None, marker_size=10)
            return fig

        else:
            center = {"lat": 51.5123, "lon": -0.1}
            fig = px.scatter_mapbox(dff,
                                    lat="Latitude",
                                    lon="Longitude",
                                    center=center,
                                    opacity=alpha,
                                    color="Crime type",
                                    zoom=11,
                                    color_discrete_map=crime_color_map
                                    )
            fig.update_layout(mapbox_style='dark',
                              mapbox_accesstoken=token,
                              autosize=True,
                              margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
                              legend={'x':0, 'xanchor': 'left',
                                      'bgcolor': 'rgb(25, 26, 26)',
                                      'font_color': 'white',
                                      'title_font_color': 'white'
                                      })
            fig.update_traces(hoverinfo='skip', hovertemplate=None, marker_size=10)
            return fig

    elif current_type == "agg":
        # Crude fix for an annoying problem that arises if isin() isn't passed
        # a list
        crime_list = toList(crime_types)

        dff = df_street_agg[(df_street_agg['Year']==year) & df_street_agg['Crime'].isin(crime_list)]
        dff = dff.groupby('LSOA').agg({'n': 'sum'})
        dff['LSOA']=dff.index
        dff['logn']=dff['n'].apply(lambda x:math.log(x))

        if postal:
            coords = getPostalCoords(postal)
            center = dict(lat = coords['latitude'].item(), lon = coords['longitude'].item())
            fig = px.choropleth_mapbox(dff,
                                       geojson=lsoa,
                                       locations='LSOA',
                                       featureidkey='properties.LSOA11CD',
                                       opacity=0.5,
                                       center=center,
                                       color="logn",
                                       zoom=11,
                                       color_continuous_scale="magma",
                                       labels={'logn':'Crime Count (log)'}
                                       )
            fig.update_layout(mapbox_style='dark',
                              mapbox_accesstoken=token,
                              autosize=True,
                              margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
                              )
            fig.update_traces(

            )
            return fig
        else:
            center = {"lat": 53.26, "lon": -1.1}
            fig = px.choropleth_mapbox(dff,
                                       geojson=lsoa,
                                       featureidkey='properties.LSOA11CD',
                                       locations='LSOA',
                                       opacity=0.5,
                                       center=center,
                                       color="logn",
                                       zoom=6,
                                       color_continuous_scale="magma",
                                       labels={'logn':'Crime Count (log)'}
                                       )
            fig.update_layout(mapbox_style='dark',
                              mapbox_accesstoken=token,
                              autosize=True,
                              margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
                              )
            fig.update_traces(

            )
            return fig


if __name__ == '__main__':
    app.run_server(debug=True)
