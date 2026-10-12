import pandas as pd

df1 = pd.read_csv('data/connections_part1.csv', skiprows=3)
df2 = pd.read_csv('data/connections_part2.csv', skiprows=3)

combined = pd.concat([df1, df2]).drop_duplicates()
combined['Name'] = combined['First Name'] + ' ' + combined['Last Name']

combined.to_csv('data/connections_real.csv', index=False)
print(f"Total connections: {len(combined)}")