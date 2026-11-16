import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')


# Create categorical bins for the two axes of our matrix

# Bin 'response_time_hours' into two categories based on the median value
df['response_speed'] = pd.cut(
    df['response_time_hours'],
    bins=[0, df['response_time_hours'].median(), df['response_time_hours'].max()],
    labels=['Fast Response', 'Slow Response']
)

# Bin 'infrastructure_damage_score' into three categories (Low, Medium, High)
df['damage_level'] = pd.qcut(
    df['infrastructure_damage_score'],
    q=3,
    labels=['Low Damage', 'Medium Damage', 'High Damage']
)

#Create the pivot table to structure the data for the heatmap
# The values will be the average 'of the total casualties for each combination
pivot_table = df.pivot_table(
    values='total_casualties',
    index='damage_level',
    columns='response_speed',
    aggfunc='mean' #the average number of casualties
)

#heatmap visualization
plt.figure(figsize=(10, 7))
sns.heatmap(
    pivot_table,
    annot=True,          # Display the numbers inside the cells
    fmt=".1f",           # Format the numbers to one decimal place
    cmap='YlOrRd',       # A yellow-to-red color scheme 
    linewidths=.5,
    annot_kws={"size": 14} 
)

plt.title('The Human Cost Matrix', fontsize=18, pad=20)
plt.xlabel('Response Speed', fontsize=12)
plt.ylabel('Infrastructure Damage Level', fontsize=12)
plt.xticks(rotation=0) 
plt.yticks(rotation=0) 

plt.tight_layout()
plt.savefig('human_cost_matrix_heatmap.png')
plt.show()