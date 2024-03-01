import os
from flask import Flask, render_template, request
import plotly.graph_objects as go
import pandas as pd
from multiprocessing.pool import ThreadPool

app = Flask(__name__)

# Data processing and plot generation code
# Data directory
data_dir = "../PHREEQC_dataviz/data/"

def read_csv(file_path):
    return pd.read_csv(file_path, sep='\s+')

# Read all .out files in the data directory into a list of dataframes with multiple threads
data = []
with ThreadPool(4) as pool:
    data = pool.map(read_csv, [data_dir + file for file in os.listdir(data_dir) if file.endswith(".out")])

for raw in data:
    # add two columns: years and days, time column is in seconds
    raw['days'] = raw['time'] / 86400
    raw['years'] = raw['time'] / 31536000
    raw = raw[raw['time'] >= 0.0]
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot-data')
def plot_data():
    l_per_water_per_ha = request.args.get('l_w_ha', default=500000, type=int)
    b_per_vol_soil = request.args.get('b_v_s', default=0.4, type=float)
    
    # Initialize lists to store data
    x_data = []
    y_data = []
    z_data = []
    color_data = []

    for i, df in enumerate(data):
        # Extract relevant data for the plot
        soil_c = (df[df['soln'].between(1, 10)])[["step", "years", "Calcite"]].groupby("step").mean()
        soil_c['Calcite'] = soil_c['Calcite'] * l_per_water_per_ha * (b_per_vol_soil*100) / 1000000 
        # soil_c['Calcite'] = soil_c['Calcite'] * l_per_water_per_ha * 44 / 1000000 
        soil_c.rename(columns={"Calcite": "Soil_Calcite"}, inplace=True)
        
        # Append data to lists
        x_data.extend([i] * len(soil_c))  # X-axis (use index of dataframe)
        y_data.extend(soil_c['years'])    # Y-axis
        z_data.extend(soil_c['Soil_Calcite'])  # Z-axis

    # Create a 3D scatter plot
    fig = go.Figure(data=[go.Scatter3d(
        x=x_data,
        y=y_data,
        z=z_data,
        mode='markers',
        marker=dict(
            size=6,
            color=x_data,
            colorscale='Viridis',
            opacity=0.8
        )
    )])

    # Set titles and axis labels
    fig.update_layout(
        title='3D Scatter Plot of Soil Calcite',
        scene=dict(
            xaxis=dict(title='Dataframe Index'),
            yaxis=dict(title='Years'),
            zaxis=dict(title='Soil Calcite')
        )
    )

    # Convert plot to HTML
    plot_html = fig.to_html(full_html=False)

    # Render the template with the plot
    return plot_html

if __name__ == '__main__':
    app.run(debug=True)
