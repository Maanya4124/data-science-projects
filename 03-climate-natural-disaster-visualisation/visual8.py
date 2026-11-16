import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler

df = pd.read_csv('global_climate_events_economic_impact_2020_2025.csv')


#Create categorical bins for the disaster duration
bins = [0, 1, 7, 30, df['duration_days'].max()]
labels = ['Sudden (1 day)', 'Short (2-7 days)', 'Medium (8-30 days)', 'Prolonged (>30 days)']
df['duration_category'] = pd.cut(df['duration_days'], bins=bins, labels=labels, right=True)

#Group by the new category and calculate the mean for our target metrics
summary_df = df.groupby('duration_category').agg(
    avg_casualties=('total_casualties', 'mean'),
    avg_econ_impact=('economic_impact_million_usd', 'mean')
).reset_index()

# Normalize the data to a 0-1 scale for fair comparison
scaler = MinMaxScaler()
summary_df[['avg_casualties', 'avg_econ_impact']] = scaler.fit_transform(summary_df[['avg_casualties', 'avg_econ_impact']])

# 4. "Melt" the DataFrame - transforms from a wide format to a long format, so Seaborn can easily plot grouped bars with separate colors for each metric
melted_df = summary_df.melt(
    id_vars='duration_category',
    var_name='Impact Type',
    value_name='Normalized Impact Score'
)

# Rename values 
melted_df['Impact Type'] = melted_df['Impact Type'].replace({
    'avg_casualties': 'Human Cost (Casualties)',
    'avg_econ_impact': 'Financial Cost (Economic Impact)'
})

# Generates the grouped bar chart with shades of red
plt.figure(figsize=(14, 7))
sns.barplot(
    data=melted_df,
    x='duration_category',
    y='Normalized Impact Score',
    hue='Impact Type',
    palette={'Human Cost (Casualties)': '#8B0000',   
             'Financial Cost (Economic Impact)': '#FF6347'}  
)

plt.title('The "Footprint" of a Disaster by its Duration', fontsize=18, pad=20)
plt.xlabel('Disaster Duration Category', fontsize=12)
plt.ylabel('Relative Impact (Normalized)', fontsize=12)
plt.xticks(rotation=0)
plt.legend(title='Impact Metric', fontsize=11)

plt.tight_layout()
plt.savefig('disaster_footprint_barchart.png')
plt.show()
