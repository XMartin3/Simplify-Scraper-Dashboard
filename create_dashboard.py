import psycopg2 # PostgreSQL adapter for Python
import pandas as pd # For data manipulation
from dash import Dash, html, dcc # For dashboard creating
from dash.dependencies import Input, Output
import plotly.express as px # For data visualization
from config import DB_PARAMS # Database configurations


def create_app(data):
    """
    Initializes a Dash application pre-configured with a layout
    including a dropdown menu for category filter and a loading spinner.

    :param data: (pandas.DataFrame) The data for creating category filter dropdown options
    :return: (dash.Dash) The initialized Dash application.
    """
    # Initializing external stylesheet for Dash application
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    # Initializing Dash application
    app = Dash(__name__, external_stylesheets=external_stylesheets)

    # Defining application layout
    app.layout = html.Div(style={'height': '100vh'}, children=[
        html.Div(style={'textAlign': 'center'}, children=[
            html.H2(children='Explore desired skills for the niche you want to get an internship in'),
            html.P("""
            Use this interactive treemap to see all skills, mentioned in the internships 
            for different job categories at Simplify.jobs. You can filter by selecting multiple categories 
            from the dropdown menu, or by clicking on the treemap itself. 
            Gain insights into the most desired skills, and improve your career planning!""",
                   style={'width': '70%', 'max-width': '1000px', 'margin-left': 'auto',
                          'margin-right': 'auto', 'margin-bottom': '15px'}),
            # Adding a dropdown filter list
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': i, 'value': i} for i in data['categories'].unique()],
                multi=True,
                placeholder="Filter by category...",
                style={'width': '70%', 'max-width': '600px', 'margin-left':
                       'auto', 'margin-right': 'auto'}
            ),
        ]),
        # Adding a loading screen
        dcc.Loading(
            id="loading",
            type="default",
            children=html.Div(id="loading-output"),
        )
    ])
    return app


def add_callbacks(app, data):
    """
    Adds a callback function to the Dash application, responsible
    for creating and updating a treemap based on the selected categories.

    :param app: (dash.Dash) Dash application
    :param data: (pandas.DataFrame) The data for creating the treemap
    :return: None
    """
    @app.callback(
        Output('loading-output', 'children'),
        Input('category-filter', 'value')
    )
    def handle_category_filter_change(selected_categories):
        fig = update_treemap(selected_categories, data)
        return dcc.Graph(
            figure=fig,
            config={'responsive': True, 'staticPlot': False},
            animate=True,
            id='treemap',
            style={'width': '100%', 'height': '80vh'},
        )


def update_treemap(selected_categories, data):
    """
    Create the treemap plot based on the selected categories.

    :param selected_categories: (list) The list of selected categories
    :param data: (pandas.DataFrame) The data for creating the treemap
    :return: (plotly.graph_objs._figure.Figure) The updated treemap figure
    """
    if selected_categories is None or len(selected_categories) == 0:
        fig = px.treemap(data, path=['categories', 'desired_skills'], values='counts')
    else:
        filtered_df = data[data['categories'].isin(selected_categories)]
        fig = px.treemap(filtered_df, path=['categories', 'desired_skills'], values='counts')

    fig.update_traces(
        textinfo="label+value",
        hovertemplate='<b>%{label} </b> <br> Count: %{value}<extra></extra>',
    )
    return fig


def extract_data():
    """
    Connect to the PostgreSQL database and fetch the data to be visualized.

    :return: (pandas.DataFrame) DataFrame of the fetched data.
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        # Fetch all the neccessary data
        cur.execute("SELECT id, categories, desired_skills FROM job_offers")
        data = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Unable to connect to database, error: {error}")
    finally:
        # Close connections
        if cur: cur.close()
        if conn: conn.close()

    # Refactor fetched data into a dataframe to visualise
    column_names = [desc[0] for desc in cur.description]
    original_df = pd.DataFrame(data, columns=column_names)
    cats_skills_data = original_df[[
        'categories', 'desired_skills']].explode('categories').explode(
            'desired_skills')
    return cats_skills_data.groupby([
        'categories', 'desired_skills']).size().reset_index(
            name='counts')


def main():
    """
    The main driver function.

    :return: (flask.Flask) Flask server to run the application.
    """
    # Extract data from the PostgreSQL database
    data = extract_data()
    # Create a dash application
    app = create_app(data)
    # Add callbacks to the application
    add_callbacks(app, data)

    return app


# Create a dash application
app = main()

if __name__ == '__main__':
    # Start the application
    app.run_server(debug=True)
