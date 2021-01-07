import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

#Plan:
# Two visualization types, heatmap and scatter.
# Put these in the header: Select vizualisation type.
# Will affect menus that pop up,

# For heatmap, options will be year and month. Year and month will both be
# Adjustable ranges.
# Radio items that suggest which crime you want.
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

df_street = pd.read_csv("street_data.csv")
# Change the writing format for concatDatasets so it writes a usable date!

token = "pk.eyJ1IjoiZXRoYW5jaGVvbmciLCJhIjoiY2tqbWRtdmNnMDN2dTJ3cGVyOHdpaDJuOSJ9.v7rcDmVITTKevrcT5HCXKA"
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

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

            html.P(
                'Drag the slider to change the year:',
                id='year-slider-text'),

            dcc.Slider(
                id='year-slider',
                min=df_street['Year'].min(),
                max=df_street['Year'].max(),
                value=df_street['Year'].min(),
                marks={str(year): str(year) for year in df_street['Year'].unique()},
                step=None
            ),

            html.P(
                'Drag the slider to change the month:',
                id='month-slider-text'),

            dcc.Slider(
                id='month-slider',
                min=df_street['Month'].min(),
                max=df_street['Month'].max(),
                value=df_street['Month'].min(),
                marks={str(month): str(month) for month in df_street['Month'].unique()},
                step=None
            ),

        ], id='input-container'),

        html.Div([

            dcc.Graph(
                id='scatter-map'
            )

        ], id='map-container')
    ],
    id='left-column',
    style={'width': '48%', 'display': 'inline-block','background-color': 'powderblue'}
    ),

    html.Div([
        html.Div([

        ]),
    ], style={'width': '48%', 'float': 'right', 'display': 'inline-block',
              'background-color': 'powderblue'}),
])

@app.callback(
    Output('scatter-map', 'figure'),
    Input('year-slider', 'value'),
    Input('month-slider', 'value')
)
def update_map(year, month):
    dff = df_street[(df_street['Year']==year) & (df_street['Month']==month)]

    fig = px.scatter_mapbox(dff,
                            lat="Latitude",
                            lon="Longitude",
                            hover_name="Crime type",
                            hover_data=["Location"],
                            color="Crime type",
                            zoom=5)
    fig.update_layout(mapbox_style="dark", mapbox_accesstoken=token)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
