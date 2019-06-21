# This script produces a record-level permit dataset from 1/1/2009 to present with synthesized dates for OFM

import os
import pandas as pd
import numpy as np
from datetime import timedelta
import pyodbc

curr_year = '17'
out_dir = r'J:\Projects\Permits\17Permit\request\datarequest\ofm'

def sqlconn(dbname):
    con = pyodbc.connect('DRIVER={SQL Server};SERVER=sql2016\DSADEV;DATABASE=' + dbname + ';trusted_connection=true')
    return con

def get_permits_current_dec():
    con = sqlconn('Sandbox')
    table_name = 'Christy.tblBuildingPermits'
    query = "SELECT * FROM " + table_name + " WHERE ISSUED >= '2010-01-01' OR FINALED >= '2010-01-01'"
    df = pd.read_sql(query, con)
    con.close()
    return df

def get_permits_previous_dec():
    prev_df = pd.read_excel("J:/Projects/Permits/MasterDatabase/csv/REG0009PMT.xlsx") # issues with reading csv version
    df = prev_df[(prev_df.ISSUED >= '2009-01-01') & (prev_df.ISSUED <= '2009-12-31') | (prev_df.FINALED >= '2009-01-01') & (prev_df.FINALED <= '2009-12-31')] 
    return df

def collate_permit_datasets(curr_year):
    curr_df = get_permits_current_dec()
    prev_df = get_permits_previous_dec()

    # find column names with specific year, create dictionary
    main_cols = curr_df.columns
    key_cols = curr_df.columns.str.contains(curr_year)
    cols_list= curr_df.columns[key_cols]
    curr_df['ISSUED'] = pd.to_datetime(curr_df['ISSUED'])
    curr_df['FINALED'] = pd.to_datetime(curr_df['FINALED'])

    # change column names in prev_df to match curr_year
    overlay_year = '14'
    prev_key_cols = prev_df.columns.str.contains(overlay_year)
    prev_cols_list = prev_df.columns[prev_key_cols]
    cols_dict = dict(zip(prev_cols_list,cols_list))
    prev_df = prev_df.rename(columns = cols_dict)
    
    # subset columns to match curr_year
    prev_df = prev_df[main_cols]

    df = pd.concat([prev_df, curr_df])
    df = df.reset_index()
    return df

# Get relevant records
df = collate_permit_datasets(curr_year)

# Standardize data types
columns_to_str = ['TYPE','PS', 'CNTY', 'PLC', 'PLC' + curr_year, 'PROJYEAR', 'ISSUEDYEAR', 'RUNTYPE', 'ZIP']
df[columns_to_str] = df[columns_to_str].astype(str)

# Jurisdictions not to synthesize: Seattle, Tacoma, and Unincorporated King, Pierce, and Snohomish
juris = ['SEATTLE', 'UNINCORPORATED KING', 'UNINCORPORATED PIERCE', 'UNINCORPORATED SNOHOMISH']

# Create synthesized finaled date field, carry over dates where where FINALED is not null and PS is not 4
df['SYNTH_FINALED'] = np.where((df['PS'] != '4') & (df['FINALED'] != pd.NaT), df['FINALED'], pd.NaT)
df['SYNTH_FINALED'] = pd.to_datetime(df['SYNTH_FINALED'])

# Demolitions (+181 days)
df.loc[(~df['JURIS'].isin(juris)) & 
       (df['PS'] == '5') & 
       (df['FINALED'].isnull()), 
       'SYNTH_FINALED'] = df['ISSUED'] + timedelta(days=181)

# SF (+219 days)
df.loc[(~df['JURIS'].isin(juris)) & 
       (df['PS'] != '4') & 
       (df['TYPE3'] == 'SF') & 
       (df['FINALED'].isnull()) & 
       (df['SYNTH_FINALED'].isnull()), 
       'SYNTH_FINALED'] = df['ISSUED'] + timedelta(days=219)

# MF1-4 (+307 days)
df.loc[(~df['JURIS'].isin(juris)) & 
       (df['PS'] != '4') & 
       (df['TYPE3'] == 'MF1-4') & 
       (df['FINALED'].isnull()) & 
       (df['SYNTH_FINALED'].isnull()), 
       'SYNTH_FINALED'] = df['ISSUED'] + timedelta(days=307)

# MF+5 (+441 days)
df.loc[(~df['JURIS'].isin(juris)) & 
       (df['PS'] != '4') & 
       (df['TYPE3'] == 'MF5+') & 
       (df['FINALED'].isnull()) & 
       (df['SYNTH_FINALED'].isnull()), 
       'SYNTH_FINALED'] = df['ISSUED'] + timedelta(days=441)

# MH or OTH (+132 days)
df.loc[(~df['JURIS'].isin(juris)) & 
       (df['PS'] != '4') & 
       (df['TYPE3'].isin(['MH', 'OTH'])) & 
       (df['FINALED'].isnull()) & 
       (df['SYNTH_FINALED'].isnull()), 
       'SYNTH_FINALED'] = df['ISSUED'] + timedelta(days=132)

df.sort_values(['JURIS', 'SORT'], inplace = True)

column_order = ['PROJYEAR','PSRCID', 'PSRCIDXY', 'MULTIREC','PERMITNO', 'SORT', 'CNTY', 'MULTICNTY', 'PLC', 'JURIS',
                 'PLC' + curr_year, 'JURIS' + curr_year, 'PLCNOTE','PIN', 'PIN_PARENT','ADDRESS', 'HOUSENO','PREFIX', 'STRNAME', 'STRTYPE', 
                 'SUFFIX', 'UNIT_BLD', 'ZIP', 'ISSUED', 'FINALED','SYNTH_FINALED', 'OTHER_DT','STATUS', 'TYPE', 'PS', 
                 'UNITS', 'BLDGS', 'LANDUSE', 'CONDO', 'VALUE', 'ZONING',  'X_COORD', 'Y_COORD','NOTES', 'NOTES2', 
                 'NOTES3', 'NOTES4', 'NOTES5','NOTES6', 'RUNTYPE', 'Month', 'SUBAREA','TRACT10','TRACTID', 'BLKGRPID', 
                 'BLOCKID', 'TAZ10', 'TAZ4K', 'FAZ10', 'UGA' + curr_year, 'TYPE2', 'TYPE3', 'TYPE4', 'PS2','ISSUEDYEAR', 'LOTSIZE']

df = df[column_order]

df.to_excel(os.path.join(out_dir, 'OFM09' + curr_year + '.xlsx'), index = None, header=True)




