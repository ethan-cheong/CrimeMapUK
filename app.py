import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import pgeocode
from ukpostcodeutils import validation

#Plan:

# Put our big big map on the right hand side.
# Slowly add in functionality for all buttons.

# Two visualization types, heatmap and scatter.
# Put these in the header: Select vizualisation type.
# Will affect menus that pop up,

# For heatmap, options will be by year. Year should be a range.
# multiple choice dropdown menu to choose crimes. Also have checkbox to pick all.
# Optional Postal code entry that will show where you want. Otherwise,
# Big map of the UK.
# Heatmap will group by some district - find a way to do this. maybe upload a
# Grouped dataset that changes depending on the option?
# Colour of each district should be: Crime rate per ___ per year.

# For scatter, options will be year and month - slider instead of range.
# Radio items to suggest which crime
# Optional postal code entry that zooms in on where you want

# Format it like https://dash-gallery.plotly.host/dash-opioid-epidemic/

# On the right, have a select method option: Whole of UK, or selected counties.
# below that, have a select chart option, that provides and plots multiple
# metrics.

# Once you've done that, tidy up everything. sort out transparency, colours.
# Finally, OPTIMIZE! make fast.

df_street = pd.read_csv("street_data.csv")
# Change the writing format for concatDatasets so it writes a usable date!

token = "pk.eyJ1IjoiZXRoYW5jaGVvbmciLCJhIjoiY2tqbWRtdmNnMDN2dTJ3cGVyOHdpaDJuOSJ9.v7rcDmVITTKevrcT5HCXKA"
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

chart_options = ['chart a', 'chart b']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def getPostalCoords(postal_code):
    # Function that takes a UK postal code as a string and returns coords as a df
    return pgeocode.Nominatim('gb').query_postal_code(postal_code)[['latitude','longitude']]


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
                dcc.RadioItems(
                    id='visualisation-type-radio-items',
                    options=[
                        {'label': 'Aggregate', 'value': 'agg'},
                        {'label': 'Individual', 'value': 'ind'}
                    ],
                    value='agg',
                )
            ],
            style={'display':'inline-block','width': '48%'},
            id='visualisation-type-container'
            ),

            html.Div([
                html.P('Enter a UK postal code (optional, speeds up loading):',
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
                dcc.Slider(
                    id='month-slider',
                    min=df_street['Month'].min(),
                    max=df_street['Month'].max(),
                    value=df_street['Month'].min(),
                    marks={str(month): str(month) for month in df_street['Month'].unique()},
                    step=None
                ),
            ],
            style={},
            id='date-container'
            ),

            html.Div([
                html.P(
                    'Filter by crime type:',
                    id='crime-dropdown-text'
                ),
                dcc.Checklist(
                    id='select-all',
                    options=[{'label': 'Select All', 'value': 1}],
                    value=[]
                ),
                dcc.Dropdown(
                    id='crime-dropdown',
                    options=[
                        {'label': c, 'value': c} for c in df_street['Crime type'].unique()
                    ],
                    value=['Violence and sexual offences', 'Theft from the person',
                           'Anti-social behaviour'],
                    multi=True
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
            id='scatter-map',
            style={'height': 800}
        ),
    ],
    style={'width': '48%', 'display': 'inline-block', 'float': 'right',
           'height': '100%'},
    id='right-column'
    )

])

@app.callback(
    Output('scatter-map', 'figure'),
    Input('postal-enter-button', 'n_clicks'),
    Input('year-slider', 'value'),
    Input('month-slider', 'value'),
    Input('crime-dropdown', 'value'),
    State('postal-input','value')
)
def update_map(n_clicks, year, month, crime_types, postal):
    dff = df_street[(df_street['Year']==year) & (df_street['Month']==month)
    & (df_street['Crime type'].isin(crime_types))]

    if postal:
        coords = getPostalCoords(postal)
        center = dict(lat = coords['latitude'].item(), lon = coords['longitude'].item())
        fig = px.scatter_mapbox(dff,
                                lat="Latitude",
                                lon="Longitude",
                                opacity=0.5,
                                center=center,
                                color="Crime type",
                                zoom=14,
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

        fig.update_traces(hoverinfo='skip', hovertemplate=None)
        return fig

    else:
        center = {"lat": 51.5123, "lon": -0.1}
        fig = px.scatter_mapbox(dff,
                                lat="Latitude",
                                lon="Longitude",
                                center=center,
                                opacity=0.5,
                                color="Crime type",
                                zoom=11
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
        fig.update_traces(hoverinfo='skip', hovertemplate=None)
        return fig




if __name__ == '__main__':
    app.run_server(debug=True)
