import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')


# Calculates the total people affected by each disaster (deaths + injuries)
df['total_affected'] = df['deaths'] + df['injuries']
# Sum total affected per country --> sort descending --> pick top 10
country_impact = df.groupby('country')['total_affected'].sum().sort_values(ascending=False).head(10).reset_index()

plt.figure(figsize=(12,6))
sns.barplot(data=country_impact, x='country', y='total_affected', palette='Reds_r')
plt.title("Top 10 Most Affected Countries (Deaths + Injuries)")
plt.ylabel("Total People Affected")
plt.xlabel("Country", fontsize=12) 
plt.xticks(rotation=45)
plt.tight_layout() 
plt.show()
