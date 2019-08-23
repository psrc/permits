# This script produces the single year Residential Building Permit Summaries by county, jurisdiction, and Census Tract that are published on the PSRC website.

import os
import pyodbc
import pandas as pd

curr_year = '17'
issued_date_from = '2017-01-01'
issued_date_to = '2017-12-31'
exclude_type4 = ['GQ', 'TL', '???']
exclude_ps = ['1', '4']
dict_cnty = {'33':'King'  ,
             '35':'Kitsap' ,
             '53':'Pierce',
             '61':'Snohomish'}
mf_types = ['MF1-2', 'MF3-4', 'MF5-9', 'MF10-19', 'MF20-49', 'MF50+']

def sqlconn(dbname):
    con = pyodbc.connect('DRIVER={SQL Server};SERVER=AWS-PROD-SQL\COHO;DATABASE=' + dbname + ';trusted_connection=true')
    return con

def get_permits_current_dec_issued_range():
    con = sqlconn('Sandbox')
    table_name = 'Christy.tblBuildingPermits'
    query = "SELECT * FROM " + table_name + " WHERE ISSUED BETWEEN " + "'" + issued_date_from + "'" + " AND " +  "'" + issued_date_to + "'"
    df = pd.read_sql(query, con)
    con.close()
    return df

def calc_netunits_by_type4(table, *args):
    # Compile permit dataset for net units with total net units by geography by TYPE4 and pivot wider
    
    list_args = []
    input_args = []
    for arg in args:
        list_args.append(arg)
        input_args.append(arg)
    
    list_args.append('TYPE4')
    
    df_netunits = table.loc[table['PS2'].isin(['+', '-'])].groupby(list_args).sum()['UNITS'].reset_index()
    
    a_series = []
    for arg in args:
        a_series.append(df_netunits[arg])
    
    df_netunits_cast = pd.crosstab(a_series, aggfunc = sum, values = df_netunits['UNITS'], columns = df_netunits['TYPE4']) 
    
    column_names = df_netunits_cast.columns
    if 'OTH' not in column_names:
        df_netunits_cast['OTH'] = 0.0
    order_types = ['NETUNITS', 'SF'] + mf_types + ['MH'] + ['OTH']
    df_netunits_cast = df_netunits_cast.fillna(value = 0)
    df_netunits_cast['NETUNITS'] = df_netunits_cast.sum(axis = 1)
    df_netunits_cast = df_netunits_cast[order_types]
    return df_netunits_cast

def calc_lostunits_by_cols(table, *args):
    # Compile permit dataset for total lost units by geographic columns; must be negative value

    input_args = []
    for arg in args:
        input_args.append(arg)

    df_grp_lostunits = table.loc[table['PS2'].isin(['-', '+/-'])]
    df_grp_lostunits.loc[df_grp_lostunits['PS2'] == '+/-','UNITS'] = df_grp_lostunits['UNITS'] * -1.0
    df_lostunits = df_grp_lostunits.groupby(input_args).sum()['UNITS'].reset_index().rename(columns={'UNITS' :'LOSTUNITS'})
    return df_lostunits

def calc_newunits_by_cols(table, *args):
    # Compile permit dataset for total new units by geographic columns

    list_args = []
    input_args = []
    for arg in args:
        input_args.append(arg)
        list_args.append(arg)
    
    list_args = list_args + ['PS2','TYPE4']

    rdf_grp = table.groupby(list_args).sum()['UNITS'].reset_index()
    rdf_newunits = rdf_grp.loc[rdf_grp['PS2'].isin(['+', '+/-'])].groupby(input_args).sum()['UNITS'].reset_index().rename(columns={'UNITS' :'NEWUNITS'})
    return rdf_newunits

def create_county_summary_table(table):
    rdf_netunits_cast = calc_netunits_by_type4(table, 'CNTY')
    
    rdf_grp = table.groupby(['CNTY', 'PS2','TYPE4']).sum()['UNITS'].reset_index()
    rdf_newunits = rdf_grp.loc[rdf_grp['PS2'].isin(['+', '+/-'])].groupby(['CNTY']).sum()['UNITS'].reset_index().rename(columns={'UNITS' :'NEWUNITS'})

    rdf_lostunits = calc_lostunits_by_cols(table, 'CNTY')
    df1 = rdf_newunits.merge(rdf_lostunits, on='CNTY')
    df = df1.merge(rdf_netunits_cast, on = 'CNTY')

    # add countyname field
    df['COUNTYNAME'] = df['CNTY'].map(dict_cnty)

    # tally regional totals
    all_cols = df.columns 
    cols_sum = [x for x in all_cols if not x.startswith("C")]
    df_reg = df[cols_sum].sum(axis = 0)
    df_reg['COUNTYNAME'] = 'Region'

    # append regional totals to main df
    df_all = df.append(df_reg, ignore_index = True)
    df_all_sort_order = ['CNTY', 'COUNTYNAME'] + cols_sum
    df_all = df_all[df_all_sort_order]
    return df_all

def create_juris_summary_table(table):
    rdf_netunits_cast = calc_netunits_by_type4(table, 'CNTY', 'PLC', 'JURIS')
    rdf_lostunits = calc_lostunits_by_cols(table, 'CNTY', 'PLC', 'JURIS')
    rdf_newunits = calc_newunits_by_cols(table, 'CNTY', 'PLC', 'JURIS')

    # import master list of jurisdictions
    juris_lookup = pd.read_excel(r'J:\Projects\Permits\Admin\script_input\a_juris_lookup.xlsx')
    juris_lookup = juris_lookup[['cnty', 'plc', 'jurisname']]

    juris_lookup = juris_lookup.rename(columns = {'cnty':'CNTY', 'jurisname':'JURIS', 'plc':'PLC'})
    juris_lookup['PLC'] = juris_lookup['PLC'].apply('{0:0>5}'.format)
    juris_lookup['CNTY'] = juris_lookup['CNTY'].astype(str)

    df_nu = pd.merge(juris_lookup, rdf_newunits, on = ['CNTY', 'PLC', 'JURIS'], how = 'left')
    df_lu = pd.merge(df_nu, rdf_lostunits, on = ['CNTY', 'PLC', 'JURIS'], how = 'left')
    df_net = pd.merge(df_lu, rdf_netunits_cast, on = ['CNTY', 'PLC', 'JURIS'], how = 'left')
    df_net = df_net.sort_values(['CNTY', 'JURIS'])
    df_net = df_net.fillna(value = 0).reset_index(drop = True)
    return df_net

def create_tract_summary_table(table):
    rdf_netunits_cast = calc_netunits_by_type4(table, 'CNTY', 'TRACTID').reset_index()
    rdf_lostunits = calc_lostunits_by_cols(table, 'CNTY', 'TRACTID')
    rdf_newunits = calc_newunits_by_cols(table, 'CNTY', 'TRACTID')

    # import master list of Census Tracts
    tractname_lookup = pd.read_excel(r'J:\Projects\Permits\Admin\script_input\aBlock10Equiv.xlsx')
    tractname_lookup = tractname_lookup[['TRACTID10', 'TRACTNAME10']].rename(columns = {'TRACTID10': 'TRACTID'})
    tractname_lu = tractname_lookup.drop_duplicates().reset_index(drop = True)
    tractname_lu['TRACTID'] = tractname_lu['TRACTID'].astype(str)

    df_nu = pd.merge(tractname_lu, rdf_newunits, on = ['TRACTID'], how = 'left')
    df_lu = pd.merge(df_nu, rdf_lostunits, on = ['CNTY', 'TRACTID'], how = 'left')
    df_net = pd.merge(df_lu, rdf_netunits_cast, on = ['CNTY', 'TRACTID'], how = 'left')
    df_net.loc[df_net['CNTY'].isnull(), 'CNTY'] = df_net.TRACTID.str[3:5]
    df_net = df_net.fillna(value = 0)
    df_net = df_net.sort_values(['CNTY', 'TRACTNAME10']).reset_index(drop = True)
    df_net['MFTOT'] = df_net[mf_types].sum(axis = 1)
    df_net['MF1-4'] = df_net[['MF1-2', 'MF3-4']].sum(axis = 1)
    df_net['MF5+'] = df_net[['MF5-9', 'MF10-19', 'MF20-49', 'MF50+']].sum(axis = 1)
    df_net['MH/OTH'] = df_net[['MH', 'OTH']].sum(axis = 1)
    df_cols_subset = [x for x in df_net.columns if x not in 'TRACTID']
    df_net = df_net[df_cols_subset]
    return df_net

# filter master dataset
rdf = get_permits_current_dec_issued_range()
rdf_sub = rdf.loc[(~rdf['TYPE4'].isin(exclude_type4)) & (~rdf['PS'].isin(exclude_ps))]

# create county summary
df_cnty = create_county_summary_table(rdf_sub)

# create jurisdiction summary
df_juris = create_juris_summary_table(rdf_sub)

# create tract summary
df_tract = create_tract_summary_table(rdf_sub)