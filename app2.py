import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# Remember - data is expensive! we should load querying data at the start of the app instead
# of inside the callback functions.
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        id='year-slider',
        min=df['year'].min(),
        max=df['year'].max(),
        value=df['year'].min(),
        marks={str(year): str(year) for year in df['year'].unique()},
        step=None
    )
])

@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('year-slider', 'value')
)
def update_figure(selected_year):
    filtered_df = df[df.year == selected_year]
    # Notice - the callback does not modify the original data, but just creates copies of the dataframe.
    # The callback should never mutate variables outside of its scope.

    fig = px.scatter(filtered_df, x="gdpPercap", y="lifeExp",
                     size="pop", color="continent", hover_name="country",
                     log_x=True, size_max=55)
    fig.update_layout(transition_duration=500)
    # Transitions allow the chart to update from one state to the next smoothly.

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
