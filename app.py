import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import mysql.connector
import numpy as np
from scipy.stats import norm, uniform, kurtosis

# Initialize a variable to keep track of the button clicks
prev_n_clicks = 0

# Database configuration
DB_CONFIG = {
    'user': 'root',
    'password': 'password',
    'host': '127.0.0.1',
    'database': 'mydb'
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
    mu, std = norm.fit(data_col)
    norm_sse = np.sum((data_col - norm.pdf(data_col, mu, std))**2)
    min_val, max_val = np.min(data_col), np.max(data_col)
    uniform_sse = np.sum((data_col - uniform.pdf(data_col, min_val, max_val - min_val))**2)
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

# Constants for Ishigami function
a = 7.0
b = 0.1

# Historical data storage for evolutions
historical_data = {
    'means': [],
    'variances': [],
    'kurtoses': [],
    'ishigami_means': []
}

def ishigami_function(x1, x2, x3):
    return np.sin(x1) + a * np.sin(x2)**2 + b * x3**4 * np.sin(x1)

def create_evolution_plot(data, y_label, title):
    fig = px.line(data, title=title)
    fig.update_layout(yaxis_title=y_label, xaxis_title='Intervals')
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
    dcc.Graph(id=f'graph-ishigami-mean'),
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
     Output(f'graph-kurtosis', 'figure'),
     Output(f'graph-ishigami-mean', 'figure')],
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
        x_range = np.linspace(min(col_data), max(col_data), 100)
        mu, std = norm.fit(col_data)
        norm_pdf = norm.pdf(x_range, mu, std)
        
        min_val, max_val = np.min(col_data), np.max(col_data)
        uniform_pdf = uniform.pdf(x_range, min_val, max_val - min_val)
        fig = px.line(x=x_range, y=norm_pdf, labels={'x': label, 'y': 'Probability Density'})
        fig.add_scatter(x=x_range, y=uniform_pdf, mode='lines')
        best_fit_distribution = fit_distributions(col_data)
        n_samples = len(col_data)
        fig.add_annotation(x=0.05, y=0.95, xref="paper", yref="paper",
                           text=f"Best Fit based on {n_samples} samples: {best_fit_distribution}",
                           showarrow=False, font=dict(color="red"))
        figures.append(fig)

    means = np.mean(data, axis=0)
    variances = np.var(data, axis=0)
    kurt = kurtosis(data, axis=0, fisher=False)
    
    historical_data['means'].append(means)
    historical_data['variances'].append(variances)
    historical_data['kurtoses'].append(kurt)
    
    mean_fig = create_evolution_plot({'x1': [m[0] for m in historical_data['means']],
                                      'x2': [m[1] for m in historical_data['means']],
                                      'x3': [m[2] for m in historical_data['means']]},
                                     'Mean Value', 'Evolution of Means')
    variance_fig = create_evolution_plot({'x1': [v[0] for v in historical_data['variances']],
                                          'x2': [v[1] for v in historical_data['variances']],
                                          'x3': [v[2] for v in historical_data['variances']]},
                                         'Variance', 'Evolution of Variances')
    kurt_fig = create_evolution_plot({'x1': [k[0] for k in historical_data['kurtoses']],
                                      'x2': [k[1] for k in historical_data['kurtoses']],
                                      'x3': [k[2] for k in historical_data['kurtoses']]},
                                     'Kurtosis', 'Evolution of Kurtosis')
    figures.extend([mean_fig, variance_fig, kurt_fig])

    ishigami_values = ishigami_function(data[:, 0], data[:, 1], data[:, 2])
    ishigami_mean = np.mean(ishigami_values)
    historical_data['ishigami_means'].append(ishigami_mean)
    ishigami_mean_fig = create_evolution_plot({'Ishigami Mean': historical_data['ishigami_means']},
                                              'Ishigami Mean Value',
                                              'Evolution of Mean of Ishigami Function')
    figures.append(ishigami_mean_fig)

    return figures[0], figures[1], figures[2], figures[3], figures[4], figures[5], figures[6]

if __name__ == '__main__':
    app.run_server(debug=True)
