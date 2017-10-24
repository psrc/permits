import os
import pandas as pd

# function to remove decimal places from text (i.e. PIN)
def trim_fraction(text):
    if '.0' in text:
        return text[:text.rfind('.0')]
    return text

#set raw dir, file, lookup
projyr = '2016'
snoFile = 'incorp_issued16.xlsx'
lookupFile = r"J:\Projects\Permits\Admin\Lookup\template061.xlsx"

pjyr = projyr[2:]
rootDir = 'J:\\Projects\\Permits\\' + pjyr + 'Permit\\data\\1raw\\snohomish\\original'
#jurisLuFile = r'J:\Projects\Permits\Admin\Lookup\a_juris_lookup.xlsx'

#read files
df = pd.read_excel(os.path.join(rootDir, snoFile), keep_default_na=False, header = 0)
lu0 = pd.read_excel(lookupFile)
lu = lu0.iloc[:,0:2]
#jurislu = pd.read_excel(jurisLuFile)

#set column names
luDict = lu.set_index('raw_py')['master'].to_dict()
df2 = df.rename(columns=luDict)
keepCol = luDict.values() # keep columns in lu.master
template = pd.DataFrame(columns = list(lu.ix[:, 'master']), index = []) # create template df 
df3 = df2.loc[:, keepCol] # select columns that are relevant
dfExport = template.append(df3)
dfExport = dfExport[template.columns] # reorder columns
dfExport = dfExport.dropna(subset = ['PERMITNO', 'PIN', 'ADDRESS'], how = 'all') # remove records if PERMITNO, PIN, and ADDRESS is NaN

# format PIN to 14 digits or copy from PIN_PARENT 
dfExport['PIN'] = dfExport['PIN'].astype(str)
dfExport['PIN_PARENT'] = dfExport['PIN_PARENT'].astype(str)

dfExport['PIN'] = dfExport['PIN'].apply(trim_fraction)
for i in range(len(dfExport.index)):
    p = dfExport.ix[dfExport.index[i], 'PIN']
    pparent = dfExport.ix[dfExport.index[i], 'PIN_PARENT']
    if p == '' and pparent != '':
        dfExport.set_value(dfExport.index[i], 'PIN', pparent) #set equal to PIN_PARENT
    elif p == '' and pparent == '':
        dfExport.set_value(dfExport.index[i], 'PIN', '')
    elif len(p) < 14:
        pform2 = '{0:0>14}'.format(p)
        dfExport.set_value(dfExport.index[i], 'PIN', pform2)
                        
#Concatenate to create ADDRESS
#dfExport['PREFIX'] = dfExport['PREFIX'].astype(str)
for i in range(len(dfExport.index)):
    if pd.isnull(dfExport.ix[dfExport.index[i], 'PREFIX']) or dfExport.ix[dfExport.index[i], 'PREFIX'] == '' or dfExport.ix[dfExport.index[i], 'PREFIX'] == 'nan':
        dfExport.set_value(dfExport.index[i], 'ADDRESS', dfExport.ix[dfExport.index[i], 'HOUSENO'] + ' ' + dfExport.ix[dfExport.index[i], 'STRNAME'] + ' ' + dfExport.ix[dfExport.index[i], 'STRTYPE'] + ' ' + dfExport.ix[dfExport.index[i], 'SUFFIX'])
    else:
        dfExport.set_value(dfExport.index[i], 'ADDRESS', dfExport.ix[dfExport.index[i], 'HOUSENO'] + ' ' + dfExport.ix[dfExport.index[i], 'PREFIX'] + ' ' + dfExport.ix[dfExport.index[i], 'STRNAME'] + ' ' + dfExport.ix[dfExport.index[i], 'STRTYPE'] + ' ' + dfExport.ix[dfExport.index[i], 'SUFFIX'])
dfExport['ADDRESS'] = dfExport['ADDRESS'].str.strip()

# toupper all fields
strCols = ['ADDRESS', 'STRNAME', 'STRTYPE', 'SUFFIX', 'STATUS', 'NOTES', 'NOTES2', 'NOTES3', 'NOTES4', 'NOTES5', 'NOTES7']
for col in strCols:
        dfExport[col] = dfExport[col].str.upper()

# status as ISSUED
dfExport['STATUS'] = 'ISSUED'

#identify unique cities
cities = dfExport.NOTES2.unique()

for city in cities:
    dfFilter = dfExport[dfExport['NOTES2'] == city]
    fname = city.replace(" ", "")
    outFilename = '061' + fname + '.xlsx'
    dfFilter.to_excel(os.path.join(r'J:\Projects\Permits\16Permit\data\1raw\snohomish\test', outFilename), sheet_name = city, index = False) 


