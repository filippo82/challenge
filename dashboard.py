import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from nytimes_filippo_py3 import NYTimesSource

no_gutters = False

###################
# Beginning of html
###################

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Reload page for new query", href="#")),
    ],
    brand="New York Times API",
    brand_href="#",
    sticky="top",
)

body = dbc.Container(
    [
        dbc.Row(
            [
                html.H1("New York Times API")
            ],
            justify="center",
            no_gutters=no_gutters
        ),
        dbc.Row(
            [
                html.P(
                    """
                    This simple dashboard allows one to query the
                    Article Search API of the New York Times.
                    First insert your API key and then a search term.
                    Then, click on Initialize and finally on Show results
                    to display a batch of 10 article headlines.
                    Each subsequent click on Show results will display
                    the subsequent 10 results of your search.
                    """
                )
            ],
            justify="center",
            no_gutters=no_gutters
        ),
        dbc.Row(
            [
                dbc.Alert(
                    """
                    In this dashboard, there is no check for handling code 429
                    (per minute query limit)!
                    """
                    , color="danger"
                ),
            ],
            justify="center",
            no_gutters=no_gutters
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.FormGroup(
                            [
                                dbc.Label("API key"),
                                dbc.Input(placeholder="API key goes here...", id="api", type="text"),
                                dbc.FormText("Insert your API key in the box above"),
                            ]
                        )
                    ],
                    width=4
                ),
                dbc.Col(
                    [
                        dbc.FormGroup(
                            [
                                dbc.Label("Query"),
                                dbc.Input(placeholder="What are you looking for?", id="query", type="text"),
                                dbc.FormText("Enter a search term in the box above"),
                            ]
                        )
                    ],
                    width=4
                ),
            ],
            justify="center",
            no_gutters=no_gutters
        ),
        dbc.Row(
            [
              html.Hr()
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button("Initialize", color="secondary", id='initialize'),
                    ],
                    md=3,
                    className=["text-center"]
                ),
                dbc.Col(
                    [
                        dbc.Button("Show results", color="secondary", id='show_results', disabled=True),
                    ],
                    md=3,
                    className=["text-center"]
                ),
            ],
            justify="center",
            no_gutters=no_gutters
        ),
        dbc.Row(
            [
              html.Hr()
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(id="output_text")
                    ],
                    md=8,
                ),
            ],
            justify="center",
            no_gutters=no_gutters
        ),
        dbc.Row(
            [
              html.Hr()
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dash_table.DataTable(
                            id='table',
                            columns=[{"name": i, "id": i} for i in ['pub_date', 'headline.main']],
                            data=[],
                            style_cell={'textAlign': 'left', 'paddingRight': '10px'},
                            style_table={'visibility': 'hidden'},
                            style_as_list_view=True
                        )
                    ],
                    md=8,
                ),
            ],
            justify="center",
            no_gutters=no_gutters
        ),
        dbc.Row(
            [
              html.Hr()
            ],
        ),
    ],
    className="mt-4",
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(children=[navbar, body])

#############
# End of html
#############

########################
# Beginning of callbacks
########################
@app.callback(
    [
        Output(component_id='show_results', component_property='disabled'),
        Output(component_id='initialize', component_property='disabled'),
    ],
    [
        Input(component_id='initialize', component_property='n_clicks'),
    ],
    [
        State(component_id='api', component_property='value'),
        State(component_id='query', component_property='value'),
    ]
)
def button_initialize(n_clicks, api, query):
    """Initialize NYT API
    """
    if n_clicks is None:
        raise PreventUpdate
    
    if api and query:
        return False, True
    else:
        raise PreventUpdate

@app.callback(
    [
        Output(component_id='table', component_property='data'),
        Output(component_id='table', component_property='style_table'),
        Output(component_id='show_results', component_property='children'),
    ],
    [
        Input(component_id='show_results', component_property='n_clicks'),
    ],
    [
        State(component_id='api', component_property='value'),
        State(component_id='query', component_property='value'),
    ]
)
def button_show_results(n_clicks, api, query):
    """Show results (bacth of 10)
    """
    batch_size = 10
    source = init_nyt_api(api, query)
    if n_clicks is None:
        raise PreventUpdate
    else:
        page = n_clicks - 1
        batch = next(source.getDataBatch(batch_size, page=page))
        df = pd.DataFrame.from_dict(batch)
        df['pub_date'] = pd.to_datetime(df['pub_date']).dt.date
        batch_new = df[['pub_date', 'headline.main']].to_dict('records')
        return batch_new, {'visibility': 'visible'}, 'Show results: page {}'.format(page)

##################
# End of callbacks
##################

##################
# Utilities
##################
def init_nyt_api(api, query):
    """Initialize the NYT API
    """
    # Define a few configuration parameters
    config = {
        'api_key': api,
        'api': 'https://api.nytimes.com/svc/search/v2/articlesearch.json',
        'query': query,
        'fq': ''
    }
    source = NYTimesSource(config)
    return source

##################
# End of utilities
##################

######
# Main
######
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
