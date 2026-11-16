import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')

# Filter for 2025
df_2025 = df[df['year'] == 2025]

# Aggregate deaths and injuries by event type
event_impact_2025 = df_2025.groupby('event_type')[['deaths', 'injuries']].sum()

#stacked bar chart
event_impact_2025.plot(kind='bar', stacked=True, figsize=(10,6), color=['#d62728','#ff7f0e'])

plt.ylabel("Number of Disasters")
plt.xlabel("Type of Natural Disaster")
plt.title("Deaths and Injuries due to Natural Disasters in 2025")
plt.xticks(rotation=45)
plt.legend(title="Impact Type")
plt.tight_layout()
plt.show()

