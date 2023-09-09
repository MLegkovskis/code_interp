import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import mysql.connector
import numpy as np
import scipy.stats

# Initialize a variable to keep track of the button clicks
prev_n_clicks = 0

# Database configuration
DB_CONFIG = {
    'user': 'root',
    'password': 'password',
    'host': '127.0.0.1',
    'database': 'mydb'
}

historical_data = {
    'means': {'x1': [], 'x2': [], 'x3': []},
    'variances': {'x1': [], 'x2': [], 'x3': []},
    'kurtoses': {'x1': [], 'x2': [], 'x3': []}
}

def get_data():
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
    cursor.execute("SELECT x1, x2, x3 FROM my_table")
    data = cursor.fetchall()
    cursor.close()
    cnx.close()
    return np.array(data)

def fit_distributions(data_col):
    mu, std = scipy.stats.norm.fit(data_col)
    norm_sse = np.sum((data_col - scipy.stats.norm.pdf(data_col, mu, std))**2)
    min_val, max_val = np.min(data_col), np.max(data_col)
    uniform_sse = np.sum((data_col - scipy.stats.uniform.pdf(data_col, min_val, max_val - min_val))**2)
    if norm_sse < uniform_sse:
        return f"N({mu:.2f}, {std:.2f})"
    else:
        return f"U({min_val:.2f}, {max_val:.2f})"

def reset_db():
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
    get_last_five_query = "SELECT id FROM my_table ORDER BY id DESC LIMIT 5;"
    cursor.execute(get_last_five_query)
    last_five_ids = [str(x[0]) for x in cursor.fetchall()]
    if len(last_five_ids) < 5:
        cursor.close()
        cnx.close()
        return
    delete_query = f"DELETE FROM my_table WHERE id NOT IN ({','.join(last_five_ids)});"
    cursor.execute(delete_query)
    cnx.commit()
    cursor.close()
    cnx.close()

def create_evolution_plot(data, ylabel, title):
    time_points = list(range(len(data['x1'])))
    fig = px.line(x=time_points, y=data['x1'], labels={'x': 'Time', 'y': ylabel}, title=title)
    fig.add_scatter(x=time_points, y=data['x2'], mode='lines', name='x2')
    fig.add_scatter(x=time_points, y=data['x3'], mode='lines', name='x3')
    return fig

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id=f'graph-x1'),
    dcc.Graph(id=f'graph-x2'),
    dcc.Graph(id=f'graph-x3'),
    dcc.Graph(id=f'graph-mean'),
    dcc.Graph(id=f'graph-variance'),
    dcc.Graph(id=f'graph-kurtosis'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,
        n_intervals=0
    ),
    html.Button('Reset', id='reset-button')
])

@app.callback(
    [Output(f'graph-x1', 'figure'),
     Output(f'graph-x2', 'figure'),
     Output(f'graph-x3', 'figure'),
     Output(f'graph-mean', 'figure'),
     Output(f'graph-variance', 'figure'),
     Output(f'graph-kurtosis', 'figure')],
    [Input('interval-component', 'n_intervals'),
     Input('reset-button', 'n_clicks')]
)
def update_graph(n_intervals, n_clicks):
    global prev_n_clicks
    if n_clicks is None:
        n_clicks = 0
    if n_clicks > prev_n_clicks:
        reset_db()
        prev_n_clicks = n_clicks

    data = get_data()
    figures = []

    for i, label in enumerate(['x1', 'x2', 'x3']):
        col_data = data[:, i]

        # Calculate mean, variance, and kurtosis
        mean_value = np.mean(col_data)
        variance_value = np.var(col_data)
        kurtosis_value = scipy.stats.kurtosis(col_data)

        # Update the historical data
        historical_data['means'][label].append(mean_value)
        historical_data['variances'][label].append(variance_value)
        historical_data['kurtoses'][label].append(kurtosis_value)

        x_range = np.linspace(min(col_data), max(col_data), 100)
        mu, std = scipy.stats.norm.fit(col_data)
        norm_pdf = scipy.stats.norm.pdf(x_range, mu, std)
        min_val, max_val = np.min(col_data), np.max(col_data)
        uniform_pdf = scipy.stats.uniform.pdf(x_range, min_val, max_val - min_val)
        fig = px.line(x=x_range, y=norm_pdf, labels={'x': label, 'y': 'Probability Density'})
        fig.add_scatter(x=x_range, y=uniform_pdf, mode='lines')
        best_fit_distribution = fit_distributions(col_data)
        n_samples = len(col_data)
        fig.add_annotation(x=0.05, y=0.95, xref="paper", yref="paper",
                           text=f"Best Fit based on {n_samples} samples: {best_fit_distribution}",
                           showarrow=False, font=dict(color="red"))
        figures.append(fig)

    mean_fig = create_evolution_plot(historical_data['means'], 'Mean Value', 'Evolution of Means for x1, x2, and x3')
    variance_fig = create_evolution_plot(historical_data['variances'], 'Variance Value', 'Evolution of Variances for x1, x2, and x3')
    kurtosis_fig = create_evolution_plot(historical_data['kurtoses'], 'Kurtosis Value', 'Evolution of Kurtosis for x1, x2, and x3')
    figures.extend([mean_fig, variance_fig, kurtosis_fig])

    return figures[0], figures[1], figures[2], figures[3], figures[4], figures[5]

if __name__ == '__main__':
    app.run_server(debug=True)
