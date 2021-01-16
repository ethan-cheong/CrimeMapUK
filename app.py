import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np
import pgeocode
import json
import math

# Load datasets

df_street = pd.read_csv("street_data_test.csv") # Use street_data_final in production version
df_street_agg = pd.read_csv("street_data_agg.csv")

# Load json boundaries
with open('lsoa_boundaries.geojson') as f:
    lsoa = json.load(f)

with open('lad_boundaries.geojson') as f:
    lad = json.load(f)

# Token for mapbox dark mode
token = "pk.eyJ1IjoiZXRoYW5jaGVvbmciLCJhIjoiY2tqbWRtdmNnMDN2dTJ3cGVyOHdpaDJuOSJ9.v7rcDmVITTKevrcT5HCXKA"

chart_options = ['Crime rate by region (Single Year)', 'Log crime rate by region (Single Year)',] #'Trends in crime rate (monthly)'


def get_postal_coords(postal_code):
    # Function that takes a UK postal code as a string and returns coords as a df
    return pgeocode.Nominatim('gb').query_postal_code(postal_code)[['latitude','longitude']]


def convert_to_list(item):
    # Function that converts an item to a list if it's not a list
    if isinstance(item, list):
        return item
    else:
        return [item]


# Color map for each crime type
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

# Initialize app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1("Crime Map UK"),
        html.P('An interactive visualization that shows yearly crime rate in the UK by region as well as maps individual crimes by month. More information available here: ethan-cheong.github.io/crime-map-uk/.',
               id='description'),
        html.P('Individual crime data taken from the UK Police Force API; built with Dash in Python and hosted on AWS EC2.',
               id='description2'),
    ], id='header' # Header bar that spans screen
    ),
    html.Div([
        html.Div([
            html.Div([
                html.P('Visualization type:', id='visualization-type-text'),
                dcc.RadioItems(
                    id='visualization-type-radio-items',
                    options=[
                        {'label': 'Aggregate Crimes', 'value': 'agg'},
                        {'label': 'Individual Crimes', 'value': 'ind'},
                    ],
                    value='agg',
                ) # Radio items to choose visualization type
            ],
            style={'display':'inline-block'},
            id='visualization-type-container'
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
                ) # Optionally input a postal code
            ],
            style={'display':'inline-block', 'float': 'right'},
            id='postal-container'
            ),

            html.Div([
                html.P(
                    'Drag the slider to select the date:',
                    id='date-slider-text'),
                dcc.Slider(
                    id='year-slider',
                    min=df_street['Year'].min(),
                    max=df_street['Year'].max(),
                    value=df_street['Year'].min(),
                    marks={str(year): str(year) for year in df_street['Year'].unique()},
                    # Marks should show each year present in our dataset
                    step=None
                ),
                html.Div([
                    dcc.Slider(
                        id='month-slider',
                        min=df_street['Month'].min(),
                        max=df_street['Month'].max(),
                        value=df_street['Month'].min(),
                        marks={str(month): str(month) for month in df_street['Month'].unique()},
                        # Marks should show each month in the dataset
                        step=None,
                        )]
                        , style = {},
                        id = 'month-slider-div'
                ) # This is contained in a Div so it can be hidden in agg mode
            ], # Choose the date with sliders
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
                        {'label': c, 'value': c} for c in df_street['Crime'].unique()
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
                        {'label': 'Local Authority District', 'value': 'LAD'},
                        {'label': 'Lower-layer Super Output Area', 'value': 'LSOA'},
                    ],
                    value='LAD',
                    style=dict()
                    )
                ],
            style={},
            id='other-options-container'
            ), # Other options
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
            dcc.Graph(
                id='selected-chart',
                figure=dict(
                    data=[dict(x=0, y=0)],
                    layout=dict(
                        paper_bgcolor='#191a1a',
                        plot_bgcolor='#191a1a',
                        autofill=True,
                        margin=dict(t=75, r=50, b=50, l=50),
                    )
                )
            ),
        ],
        id='graph-container'
        ),

    ],
    id='left-column',
    style={'display': 'inline-block', 'width': '45%'}
    ),

    html.Div([
        dcc.Graph(
            id='map'
            )
    ],
    style={'display': 'inline-block', 'float': 'right', 'width': '45%'},
    id='right-column'
    )

])

# This callback plots the crime rate by region graph, depending on the inputs its been given
@app.callback(
    Output('selected-chart', 'figure'),
    Input('chart-dropdown', 'value'),
    Input('year-slider', 'value'),
    Input('visualization-type-radio-items', 'value'),
    Input('map', 'selectedData')
)
def plotChart(chart_type, year, visualization_type, selected_data):
    if selected_data is None or visualization_type == 'ind':
        return dict(
            data=[dict(x=0, y=0)],
            layout=dict(
                title="Use the select tool on the aggregate crimes map to select regions",
                paper_bgcolor="#191a1a",
                plot_bgcolor="#191a1a",
                font=dict(color="White"),
                margin=dict(t=75, r=50, b=50, l=75),
            ),
        ) # Return a blank graph if not in agg mode or nothing is selected.

    dff = pd.DataFrame([selected_data["points"][i]['customdata'] for i in range(len(selected_data["points"]))],
                        columns = ['Region', 'Log crime rate', 'Crime rate'])
    # Make a dataframe from the selected data on the map after its been lassoed

    if chart_type == 'Crime rate by region (Single Year)':
        fig = px.bar(dff, x='Region', y='Crime rate', title='Crime rate by region (Single Year)')
        fig.update_layout(paper_bgcolor='#191a1a',
                    plot_bgcolor='#191a1a',
                    margin=dict(t=75, r=50, b=50, l=50),
                    font=dict(color="White"))
        fig.update_xaxes(categoryorder="total ascending")
        fig.update_traces(marker_color='orange')

    elif chart_type == 'Log crime rate by region (Single Year)':
        fig = px.bar(dff, x='Region', y='Log crime rate', title='Log crime rate by region (Single Year)')
        fig.update_layout(paper_bgcolor='#191a1a',
                    plot_bgcolor='#191a1a',
                    margin=dict(t=75, r=50, b=50, l=50),
                    font=dict(color="White"))
        fig.update_xaxes(categoryorder="total ascending")
        fig.update_traces(marker_color='orange')

    return fig

# This next callback changes the format of the app based on which mode it's in
@app.callback(
    Output('month-slider-div', 'style'),
    Output('highlight', 'style'),
    Output('boundaries', 'style'),
    Output('map', 'style'),
    Input('visualization-type-radio-items', 'value')
)
def changeVisualizationType(current_type):
    if current_type=="ind":
        # Show month slider and highlight checkbox. Hide boundaries radioitems. Change height of map
        return [
            dict(),
            dict(),
            dict(display='none'),
            dict(height='817px')
            ]
    elif current_type=="agg":
        # Hide month slider and highlight checkbox. Show boundaries radioitems. Change height of map
        return [
            dict(display='none'),
            dict(display='none'),
            dict(),
            dict(height='778px')
            ]

# This callback gives functionality to the select all button above the crime type dropdown
@app.callback(
    Output('crime-dropdown', 'value'),
    Input('select-all', 'value'),
    State('crime-dropdown', 'value')
)
def checkSelected(selected, current_values):
    if selected:
        return [c for c in df_street['Crime'].unique()]
    else:
        return current_values

# This callback plots the map
@app.callback(
    Output('map', 'figure'),
    Input('visualization-type-radio-items', 'value'),
    Input('postal-enter-button', 'n_clicks'),
    Input('year-slider', 'value'),
    Input('month-slider', 'value'),
    Input('crime-dropdown', 'value'),
    Input('highlight', 'value'),
    Input('boundaries', 'value'),
    State('postal-input','value')
)
def updateMap(current_type, n_clicks, year, month, crime_types, highlight,
              boundaries, postal):
    year = int(year)
    month = int(month)
    if current_type == "ind":
        dff = df_street[(df_street['Year']==year) & (df_street['Month']==month) & (df_street['Crime'].isin(crime_types))]
        if highlight:
            alpha = 1
        else:
            alpha = 0.3

        if postal:
            coords = get_postal_coords(postal)
            center = dict(lat = coords['latitude'].item(), lon = coords['longitude'].item())
            fig = px.scatter_mapbox(dff,
                                    lat="Latitude",
                                    lon="Longitude",
                                    opacity=alpha,
                                    center=center,
                                    color="Crime",
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
                                    color="Crime",
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

        # Crude fix for an annoying problem that arises if isin() isn't passed a list
        crime_list = convert_to_list(crime_types)
        dff = df_street_agg[(df_street_agg['Year']==year) & df_street_agg['Crime'].isin(crime_list)]

        if boundaries == 'LSOA':

            dff = dff.groupby(['LSOA', 'LSOAName']).agg({'n': 'sum'})
            dff.reset_index(level=['LSOA', 'LSOAName'], inplace=True)
            dff['Number of crimes (log)']=dff['n'].apply(lambda x:round(math.log(x),2))
            dff['Number of crimes (actual)'] = dff['n']

            if postal:
                coords = get_postal_coords(postal)
                center = dict(lat = coords['latitude'].item(), lon = coords['longitude'].item())
                fig = px.choropleth_mapbox(dff,
                                           geojson=lsoa,
                                           locations='LSOA',
                                           featureidkey='properties.LSOA11CD',
                                           opacity=0.5,
                                           center=center,
                                           color='Number of crimes (log)',
                                           zoom=11,
                                           color_continuous_scale='magma',
                                           hover_data=['LSOAName','Number of crimes (log)','Number of crimes (actual)',]
                                           )
                fig.update_layout(mapbox_style='dark',
                                  mapbox_accesstoken=token,
                                  autosize=True,
                                  margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
                                  )
                fig.update_coloraxes(
                    colorbar=dict(
                        len=0.3,
                        xanchor='left',
                        yanchor='top',
                        x=0,
                        y=1,
                    ),
                    colorbar_tickfont=dict(
                        color='White'
                    ),
                    colorbar_title=dict(
                        font_color='White'
                    )
                )

                return fig

            else:
                center = {'lat': 53.26, 'lon': -1.1}
                fig = px.choropleth_mapbox(dff,
                                           geojson=lsoa,
                                           featureidkey='properties.LSOA11CD',
                                           locations='LSOA',
                                           opacity=0.5,
                                           center=center,
                                           color='Number of crimes (log)',
                                           zoom=6,
                                           color_continuous_scale='magma',
                                           hover_data=['LSOAName','Number of crimes (log)','Number of crimes (actual)',]
                                           )
                fig.update_layout(mapbox_style='dark',
                                  mapbox_accesstoken=token,
                                  autosize=True,
                                  margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
                                  )
                fig.update_coloraxes(
                    colorbar=dict(
                        len=0.3,
                        xanchor='left',
                        yanchor='top',
                        x=0,
                        y=1,
                    ),
                    colorbar_tickfont=dict(
                        color='White'
                    ),
                    colorbar_title=dict(
                        font_color='White'
                    )
                )

                return fig

        elif boundaries == 'LAD':

            dff['Crimes per 1000 people'] = dff['n']/dff['Population']*1000
            dff = dff.groupby(['LAD', 'LADName']).agg({'Crimes per 1000 people': 'sum'})
            dff.reset_index(level=['LAD', 'LADName'], inplace=True)
            # The line below is a quick fix to prevent a math error when we take log(0)
            dff['Crimes per 1000 people'] = dff['Crimes per 1000 people'].apply(lambda x: 1 if round(x,2)==0 else round(x,2))
            dff['Log crime rate'] = dff['Crimes per 1000 people'].apply(lambda x: round(math.log(x), 2))

            if postal:
                coords = get_postal_coords(postal)
                center = dict(lat = coords['latitude'].item(), lon = coords['longitude'].item())
                fig = px.choropleth_mapbox(dff,
                                           geojson=lad,
                                           locations='LAD',
                                           featureidkey='properties.LAD20CD',
                                           opacity=0.5,
                                           center=center,
                                           color='Log crime rate',
                                           zoom=11,
                                           color_continuous_scale='magma',
                                           hover_data=['LADName',
                                                       'Log crime rate',
                                                       'Crimes per 1000 people',
                                                       ]
                                           )
                fig.update_layout(mapbox_style='dark',
                                  mapbox_accesstoken=token,
                                  autosize=True,
                                  margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
                                  )
                fig.update_coloraxes(
                    colorbar=dict(
                        len=0.3,
                        xanchor='left',
                        yanchor='top',
                        x=0,
                        y=1,
                    ),
                    colorbar_tickfont=dict(
                        color='White'
                    ),
                    colorbar_title=dict(
                        font_color='White'
                    )
                )

                return fig

            else:

                center = {'lat': 53.26, 'lon': -1.1}
                fig = px.choropleth_mapbox(dff,
                                           geojson=lad,
                                           featureidkey='properties.LAD20CD',
                                           locations='LAD',
                                           opacity=0.5,
                                           center=center,
                                           color='Log crime rate',
                                           zoom=6,
                                           color_continuous_scale="magma",
                                           hover_data=['LADName',
                                                       'Log crime rate',
                                                       'Crimes per 1000 people',
                                                       ]
                                           )
                fig.update_layout(mapbox_style='dark',
                                  mapbox_accesstoken=token,
                                  autosize=True,
                                  margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
                                  )
                fig.update_coloraxes(
                    colorbar=dict(
                        len=0.3,
                        xanchor='left',
                        yanchor='top',
                        x=0,
                        y=1,
                    ),
                    colorbar_tickfont=dict(
                        color='White'
                    ),
                    colorbar_title=dict(
                        font_color='White'
                    )
                )

                return fig

if __name__ == '__main__':
    app.run_server(debug=False,dev_tools_ui=False,dev_tools_props_check=False)
