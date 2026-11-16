import pandas as pd
import plotly.express as px
import plotly.colors as pc
import plotly.io as pio

pio.renderers.default = "browser"

df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')

# Aggregate number of disasters by type and year
event_counts = df.groupby(['year', 'event_type']).size().reset_index(name='count')

event_types = event_counts['event_type'].unique()

#red color shades (red palette)
reds = pc.sequential.Reds
if len(event_types) > len(reds):
    reds = reds * (len(event_types) // len(reds) + 1)
colors = reds[-len(event_types):]  # darker reds for later event types

# Creates animated bar chart
fig = px.bar(
    event_counts,
    x='event_type',
    y='count',
    color='event_type',
    color_discrete_sequence=colors,  
    animation_frame='year',  # Animate by year
    range_y=[0, event_counts['count'].max() + 5],
    title='Natural Disasters Over Years 2020–2025',
    labels={'event_type': 'Type of Natural Disaster', 'count': 'Number of Disasters'},
    text='count'
)

fig.update_layout(
    template='plotly_white',
    title_x=0.5,
    xaxis_tickangle=-45,
    showlegend=False,
    xaxis=dict(
        title=dict(
            text='Type of Natural Disaster',
            standoff=75
        )
    ),
    margin=dict(b=100)
)

fig.show()
