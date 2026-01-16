import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

# Load data
df = pd.read_csv('logs/ab_test_results.csv')

print('='*80)
print('A/B TEST RESULTS SUMMARY')
print('='*80)

# Basic info
print(f'\nTest Date: {pd.to_datetime(df["timestamp"]).dt.date.iloc[0]}')
print(f'Total Users: {len(df):,}')

# Group distribution
print(f'\n--- GROUP DISTRIBUTION ---')
grp = df['group'].value_counts()
print(f'Group A: {grp["A"]} users ({grp["A"]/len(df)*100:.1f}%)')
print(f'Group B: {grp["B"]} users ({grp["B"]/len(df)*100:.1f}%)')

# CTR Analysis
print(f'\n--- CLICK-THROUGH RATE (CTR) ---')
ctr_a = df[df['group']=='A']['clicked'].mean()
ctr_b = df[df['group']=='B']['clicked'].mean()
print(f'Group A CTR: {ctr_a:.2%}')
print(f'Group B CTR: {ctr_b:.2%}')
print(f'Absolute Difference: {(ctr_b - ctr_a):.2%}')
print(f'Relative Lift: {((ctr_b / ctr_a - 1) * 100):.2f}%')

# Statistical test
print(f'\n--- STATISTICAL SIGNIFICANCE (Chi-Square Test) ---')
ct = pd.crosstab(df['group'], df['clicked'])
chi2, pval, dof, exp = chi2_contingency(ct)
print(f'Chi-square statistic: {chi2:.4f}')
print(f'P-value: {pval:.4f}')
print(f'Significant at alpha=0.05: {"YES" if pval < 0.05 else "NO"}')

# Purchase count
print(f'\n--- PURCHASE COUNT ---')
pc_a = df[df['group']=='A']['purchase_count'].mean()
pc_b = df[df['group']=='B']['purchase_count'].mean()
print(f'Group A Avg Purchase: {pc_a:.2f}')
print(f'Group B Avg Purchase: {pc_b:.2f}')
print(f'Difference: {(pc_b - pc_a):.2f} ({((pc_b/pc_a - 1)*100):.2f}%)')

# Persona breakdown
print(f'\n--- PERSONA BREAKDOWN ---')
print('\nBy Budget:')
budget_ctr = df.groupby(['group', 'persona_budget'])['clicked'].mean().unstack()
print(budget_ctr)

print('\nBy Age Group:')
df['age_group'] = pd.cut(df['persona_age'], bins=[0, 25, 35, 45, 55, 100], 
                          labels=['18-25', '26-35', '36-45', '46-55', '56+'])
age_ctr = df.groupby(['group', 'age_group'])['clicked'].mean().unstack()
print(age_ctr)

print('='*80)
