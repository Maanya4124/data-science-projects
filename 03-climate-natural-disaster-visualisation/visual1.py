import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import plotly.colors as pc

pio.renderers.default = "browser"

df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')

# We first need to aggregate monthly events to get the count of events happened in each month for each year
monthly_events = df.groupby(['year', 'month']).size().reset_index(name='event_count')

# Sort data by year and month to ensure correct order
monthly_events = monthly_events.sort_values(['year', 'month'])

# Get unique years and months for the timieline
years = monthly_events['year'].unique()
months = sorted(monthly_events['month'].unique())

#red color shades (red palette)
reds = pc.sequential.Reds
if len(years) > len(reds):
    reds = reds * (len(years) // len(reds) + 1)
colors = reds[-len(years):]  # darker reds for later years

# Create initial figure with empty traces for each year
fig = go.Figure()

for j, year in enumerate(years):
    fig.add_trace(go.Scatter(
        x=[],
        y=[],
        mode='lines+markers',
        name=str(year),
        line=dict(color=colors[j]),
        marker=dict(color=colors[j])
    ))

#animation frames for each month
frames = []
for month in months:
    frame_data = []
    for j, year in enumerate(years):
        df_slice = monthly_events[(monthly_events['year']==year) & (monthly_events['month']<=month)]
        frame_data.append(go.Scatter(
            x=df_slice['month'],
            y=df_slice['event_count'],
            mode='lines+markers',
            name=str(year),
            line=dict(color=colors[j]),
            marker=dict(color=colors[j])
        ))
    frames.append(go.Frame(data=frame_data, name=str(month)))

fig.frames = frames

# Layout settings with animation buttons
fig.update_layout(
    title='Monthly Count of Global Climate Events (2020–2025)',
    xaxis_title='Month',
    yaxis_title='Number of Disasters',
    xaxis=dict(dtick=1, range=[1,12]),
    yaxis=dict(range=[0, monthly_events['event_count'].max() + 5]),
    template='plotly_white',
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        buttons=[dict(label="Play",
                      method="animate",
                      args=[None, {"frame": {"duration": 500, "redraw": True},
                                   "fromcurrent": True, "transition": {"duration": 0}}])])]
)

fig.show()
