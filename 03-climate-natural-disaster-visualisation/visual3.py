import pandas as pd
import plotly.express as px
import plotly.io as pio

pio.renderers.default = "browser"

df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')

# Aggregate number of disastes per country and per year
country_events = df.groupby(['year', 'country']).size().reset_index(name='event_count')
#size() counts rows per group, reset_index with name='event_count' creates the column

# Creates animated choropleth
fig = px.choropleth(
    country_events,
    locations="country",          # Country names 
    locationmode="country names",
    color="event_count",          # Shading based on count
    hover_name="country",
    animation_frame="year",       # Animation - year by year
    color_continuous_scale="OrRd",
    title="Global Climate Events Across the Globe (2020–2025)",
    labels={"event_count": "Number of Disasters"} 

)

fig.update_layout(
    template="plotly_white",
    title_x=0.5
)

fig.show()

