import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc

df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')

# Group by year and country then get average
impact_by_country = df.groupby(['year', 'country'], as_index=False)['economic_impact_million_usd'].mean()

# keep top 10 countries per year 
impact_by_country = impact_by_country.groupby('year', group_keys=False).apply(lambda x: x.nlargest(10, 'economic_impact_million_usd')).reset_index(drop=True)

# Extract unique years for animation frames
years = sorted(impact_by_country['year'].unique())

reds = pc.sequential.Reds
if len(impact_by_country['country'].unique()) > len(reds):
    reds = reds * (len(impact_by_country['country'].unique()) // len(reds) + 1)

# Create figure with first frame (initial year)
first_year = years[0]
data_first = impact_by_country[impact_by_country['year'] == first_year]

fig = go.Figure(
    data=[go.Pie(
        labels=data_first['country'],
        values=data_first['economic_impact_million_usd'],
        hole=0.4,
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Avg Impact: %{value:,.2f} million USD<extra></extra>',
        marker=dict(colors=reds[:len(data_first)])
    )]
)

# Add frames for each year to animate the pie chart
frames = []
for year in years:
    data_year = impact_by_country[impact_by_country['year'] == year]
    frames.append(go.Frame(
        data=[go.Pie(
            labels=data_year['country'],
            values=data_year['economic_impact_million_usd'],
            hole=0.4,
            marker=dict(colors=reds[:len(data_year)])  # <-- same red shades
        )],
        name=str(year)
    ))

fig.frames = frames

# Add Play/Pause buttons and slider
fig.update_layout(
    title='Average Economic Impact of Natural Disasters by Country (2020–2025)',
    title_x=0.5,
    template='plotly_white',
    updatemenus=[{
        'type': 'buttons',
        'buttons': [
            {'label': 'Play', 'method': 'animate', 'args': [None, {'frame': {'duration':1500, 'redraw':True}, 'fromcurrent':True}]},
            {'label': 'Pause', 'method': 'animate', 'args': [[None], {'frame': {'duration':0}, 'mode':'immediate'}]}
        ],
        'x':0.1,
        'y':-0.1
    }],
    sliders=[{
        'steps': [
            {'args': [[str(year)], {'frame': {'duration':1000, 'redraw':True}, 'mode':'immediate'}],
             'label': str(year), 'method':'animate'}
            for year in years
        ],
        'x':0.1,
        'y':-0.15,
        'len':0.8
    }]
)

fig.show()
