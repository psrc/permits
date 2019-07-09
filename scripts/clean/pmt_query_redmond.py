import os
import pandas as pd
import re
#https://data.redmond.gov/Vibrant-Economy/Permit-Types/mfbw-uzic

dir = r'J:\Projects\Permits\17Permit\data\1raw\Redmond'
fname = 'Issued_Permits.csv'
rdf = pd.read_csv(os.path.join(dir, fname))

rdf['Permit Type'].unique()

permit_types = ['Multi-Family', 'Residential', 'Demolition', 'Mixed Use']
select_cols = ['Permit Number', 'Location', 'Parcel Number', 'Permit Type', 'Issue Date', 'Project Name', 'Work Description',
            'Valuation', 'Sq Ft', 'Number of Units']

df = rdf.loc[rdf['Permit Type'].isin(permit_types) & rdf['Number of Units'].notnull(), select_cols]
df.shape

pat_remodel1 = '^(R|M.*)(ALT|ADD)(?!.*ADU.*)'
pat_remodel2 = '.*(Remodel|REMODEL).*'
df = df[~df['Work Description'].str.contains(pat_remodel1)]
df = df[~df['Work Description'].str.contains(pat_remodel2)]
df.shape

df['Location'].replace({ r'\A\s+|\s+\Z': '', '\n' : ' '}, regex=True, inplace=True) # remove new line breaks
df['LatLong'] = df['Location'].str.extract('(\(.*\)$)', expand = True)
df['Lat'] = df['Location'].str.extract('((?<=\().*(?=\,))', expand = True)
df['Long'] = df['Location'].str.extract('((?<=\,)\s\-.*(?=\)))', expand = True)
df['Address'] = df['Location'].str.extract('(^.*(?=REDMOND|KIRKLAND))', expand = True)

df.to_excel(os.path.join(dir, 'Issued_Permits.xlsx'), index = None)