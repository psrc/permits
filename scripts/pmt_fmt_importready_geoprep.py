#This script will evaluate xlsx files in 3importready and do the following:
#  additional formatting of permit fields,
#  create additional fields found in the master permit database,
#  update XY coordinate columns from the master permit file and parcel data files,
#  export revised permit table for QC, and
#  export records ready for geocoding 
  
import os
import re
import datetime
import pandas as pd
import numpy as np

# function to remove decimal places from text (i.e. PIN)
def trim_fraction(text):
    if '.0' in text:
        return text[:text.rfind('.0')]
    return text

# parcels table dictionary
parcelDict = {'033': 'pKin', '035': 'pKit', '053': 'pPrc', '061': 'pSno'}

# Multirec dictionary
d = {'TRUE': True, None: False, 'FALSE': False}

# permit status dictionary
status = {
        'ISSUED': ['OPEN', 'ACTIVE', 'issued'],
        'FINALED': ['FINAL', 'CLOSED', 'FINALLED', 'C.O. ISSUED', 'finalled', 'final']
         }

# year
projyear = '2016'
pjyr = projyear[2:]
master = 'REG15PMT.xlsx' 

# directories
rootDir = r'J:\Projects\Permits' + '\\' + pjyr + 'Permit'
inPath = r'data\3importready'
outPath1 = r'geocoding\prep\0all'
outPath2 = r'geocoding\prep\0inbox'
refPath = os.path.join(rootDir, r'geocoding\prep\reference')

inDir = os.path.join(rootDir, inPath)
outDir1 = os.path.join(rootDir, outPath1)
outDir2 = os.path.join(rootDir, outPath2)

# format jurisdiction lookup table
jurisLu = pd.read_excel(r'J:\Projects\Permits\Admin\Lookup\a_juris_lookup.xlsx')
jurisLu['cnty'] = jurisLu['cnty'].astype(str).apply('{0:0>3}'.format)
jurisLu['juris'] = jurisLu['juris'].str.upper()
jurisLu['plc'] = jurisLu['plc'].astype(str).apply('{0:0>5}'.format)

masterPmt = pd.read_excel(os.path.join(refPath, master))
pKin = pd.read_excel(os.path.join(refPath, 'gKIN17.xlsx'), header = 0, keep_default_na=False)
pKit = pd.read_excel(os.path.join(refPath, 'gKIT17.xlsx'), header = 0, keep_default_na=False)
pPrc = pd.read_excel(os.path.join(refPath, 'gPRC17.xlsx'), header = 0, keep_default_na=False)
pSno = pd.read_excel(os.path.join(refPath, 'gSNO17.xlsx'), header = 0, keep_default_na=False)

pKin['PIN'] = pKin['PIN'].astype(str)
pKin['PIN'] = pKin['PIN'].apply(trim_fraction)
for i in range(len(pKin.index)):
    p = pKin.loc[pKin.index[i], 'PIN']
    if p == 'nan' or p == '':
        pKin.set_value(pKin.index[i], 'PIN', '')
    else:
        if len(p) < 10:
            pform = '{0:0>10}'.format(p)
            pKin.set_value(pKin.index[i], 'PIN', pform)
            
pPrc['PIN'] = pPrc['PIN'].astype(str)
pPrc['PIN'] = pPrc['PIN'].apply(trim_fraction)
for i in range(len(pPrc.index)):
    p1 = pPrc.loc[pPrc.index[i], 'PIN']
    if p1 == 'nan' or p1 == '':
        pPrc.set_value(pPrc.index[i], 'PIN', '')
    else:
        if len(p1) < 10:
            pform1 = '{0:0>10}'.format(p1)
            pPrc.set_value(pPrc.index[i], 'PIN', pform1)
 
pKit['PIN'] = pKit['PIN'].astype(str)
pKit['PIN'] = pKit['PIN'].apply(trim_fraction)
for i in range(len(pKit.index)):
    p2 = pKit.loc[pKit.index[i], 'PIN']
    if p2 == 'nan'or p2 == '':
        pKit.set_value(pKit.index[i], 'PIN', '')
    else:
        if len(p2) < 14:
            pform2 = '{0:0>14}'.format(p2)
            pKit.set_value(pKit.index[i], 'PIN', pform2)

pSno['PIN'] = pSno['PIN'].astype(str)
pSno['PIN'] = pSno['PIN'].apply(trim_fraction)
for i in range(len(pSno.index)):
    p3 = pSno.loc[pSno.index[i], 'PIN']
    if p3 == 'nan' or p3 == '':
        pSno.set_value(pSno.index[i], 'PIN', '0000000000000')
    else:
        if len(p3) < 14:
            pform3 = '{0:0>14}'.format(p3)
            pSno.set_value(pSno.index[i], 'PIN', pform3)
                       
# select only files that need processing
fullList = os.listdir(inDir)
jurisFiles = [] # store file names in 3importready

for file in fullList:
    if file.endswith(".xlsx"):
        jurisFiles.append(file)

jurisCompleted = os.listdir(outDir1)
juris2Process = [afile for afile in jurisFiles if afile not in jurisCompleted]

for afile in juris2Process:
    df = pd.read_excel(os.path.join(inDir, afile), keep_default_na=False, header = 0)
    df = df.sort_values(by = 'SORT', ascending=True) #sort table

    # update PIN with leading zeros
    cnty = afile[:3]
    
    if (cnty == '033' or cnty == '053' and df['PIN'][0] > 10) or (cnty == '035' and df['PIN'][0] > 14):
        df['PIN'] = df['PIN'].astype(str)
        df['PIN'] = df['PIN'].apply(trim_fraction)   
    
    df['PIN'] = df['PIN'].astype(str)
    for i in range(len(df.index)):
        pp = df.loc[df.index[i], 'PIN']
        if pp == 'nan' or pp == '':
            df.set_value(df.index[i], 'PIN', '')
        else:
            if cnty == '033' or cnty == '053':
                if len(pp) < 10:
                    ppform = '{0:0>10}'.format(pp)
                    df.set_value(df.index[i], 'PIN', ppform)
            else:
                if len(pp) < 14:
                    ppform2 = '{0:0>14}'.format(pp)
                    df.set_value(df.index[i], 'PIN', ppform2)
    
    # fill in PSRCID col                                           
    for i in range(len(df.index)):
         df.set_value(df.index[i], 'PSRCIDN', i+1)   
    df['PSRCIDN'] = df['PSRCIDN'].astype(int) 
    
    df = df.reset_index(drop=True)   
    df = df.sort_index()
    
    # update Multirec field
    df['MULTIREC'] = df['MULTIREC'].map(d)
    
    # update status field
    sItems = status.items()
    for i in range(len(df.index)):
        currVal = df.loc[i, 'STATUS']
        newVal = [s[0] for s in sItems if currVal in s[1]]
        if len(newVal) > 0:
            newValUpd = newVal[0]
            df.loc[i, 'STATUS'] = newValUpd
        else:
            continue
        
    # add new columns
    currJuris = 'JURIS' + pjyr
    currPlc = 'PLC' + pjyr
    newColNames = ['JURIS', currJuris, 'PLC', currPlc, 'PROJYEAR', 'CNTY', 'MULTICNTY', 'PSRCID', 'X_COORD', 'Y_COORD', 'RUNTYPE']
    for name in newColNames:
        df[name] = np.nan
      
    pJuris = re.compile("\\d+(\\w+)[.]")
    jPatterns = pJuris.findall(afile)
    juris = [j for j in jPatterns][0]
    jurisFilter = jurisLu[(jurisLu['juris'].str.contains(juris)) & (jurisLu['cnty'].str.contains(cnty))] 
    
    # update new columns
    df['JURIS'] = jurisFilter.loc[jurisFilter.index[0], 'jurisname']  
    df[currJuris] = jurisFilter.loc[jurisFilter.index[0], 'jurisname']
    df['PROJYEAR'] = projyear 
    df['CNTY'] = cnty 
    df['PLC'] = jurisFilter.loc[jurisFilter.index[0], 'plc']
    df[currPlc] = jurisFilter.loc[jurisFilter.index[0], 'plc']
    df['PSRCID'] = pjyr + cnty[1:] + jurisFilter.loc[jurisFilter.index[0], 'plc'] + (df['PSRCIDN'].astype(str).apply('{0:0>5}'.format)) 
    if juris in ['AUBURN', 'BOTHELL', 'ENUMCLAW', 'MILTON', 'PACIFIC']:
        df['MULTICNTY'] = True
    else:
        df['MULTICNTY'] = False
    
    # join to masterPmt by Sort; update XY coords and Runtype
    dJuris = str(jurisFilter.loc[jurisFilter.index[0], 'jurisname']) 
    
    mPmtFilter = masterPmt.loc[masterPmt['JURIS'] == dJuris, ['JURIS', 'SORT', 'X_COORD', 'Y_COORD', 'RUNTYPE']]
    df1 = pd.merge(df, mPmtFilter, how = 'left', on = ['JURIS', 'SORT'])
    df1['X_COORD_x'] = df1['X_COORD_y']
    df1['Y_COORD_x'] = df1['Y_COORD_y']
    df1['RUNTYPE_x'] = df1['RUNTYPE_y']
    df1 = df1.drop(['X_COORD_y', 'Y_COORD_y', 'RUNTYPE_y'], axis=1)
    df1 = df1.rename(columns = {'X_COORD_x': 'X_COORD', 'Y_COORD_x': 'Y_COORD', 'RUNTYPE_x': 'RUNTYPE'})
    
    # join to parcel table by PIN ; update X_COORD, Y_COORD
    parcelFile = eval(parcelDict[cnty])
    df2 = pd.merge(df1, parcelFile, how = 'left', on = ['PIN'])              
    df2.loc[df2['X_COORD_x'].isnull(), 'X_COORD_x'] = df2['X_COORD_y']      
    df2.loc[df2['Y_COORD_x'].isnull(), 'Y_COORD_x'] = df2['Y_COORD_y']   
    df2.loc[(df2['RUNTYPE'].isnull()) & (df2['X_COORD_x'].notnull()), ['RUNTYPE']] = '1' #runtype as string
    df2 = df2.drop(['X_COORD_y', 'Y_COORD_y'], axis=1)
    df2 = df2.rename(columns = {'X_COORD_x': 'X_COORD', 'Y_COORD_x': 'Y_COORD'})
            
    # select records where X_COORD.isnull(); export to 0inbox
    df3 = df2.loc[df2['X_COORD'].isnull()] 
    if len(df3.index) > 0:
        df3 = df3[['SORT', 'PSRCID', 'PIN', 'PLC', 'JURIS', 'ADDRESS', 'HOUSENO', 'PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'ZIP', 'TYPE', 'PS', 'UNITS', 'BLDGS', 'RUNTYPE']]
        df3.to_csv(os.path.join(outDir2, 't'+ afile[:afile.rfind('.')] + '_geo.csv'), index = False)
    
    # prep df2 for export to 0all   
    # add macro row and reorder so macro row is below header
    newRow = [999999, 'TEXT', 'TEXT', 'TRUE', 'TEXT', 'TEXT', 999999, 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', '1/1/01', '1/1/01', 'TEXT', 'TEXT', 'TEXT',	999999, 9999999, 'TEXT', 'TEXT', 999999999, 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 999999, 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT','TRUE','TEXT', 999999999, 999999999,'TEXT']
    df2.loc[-1] = newRow
    df2.index = df2.index + 1
    df2 = df2.sort_index()
    
    # update macro row date strings to be date object
    df2.loc[0, 'ISSUED'] = datetime.datetime.strptime(df2.loc[0, 'ISSUED'], '%m/%d/%y').date()
    df2.loc[0, 'FINALED'] = datetime.datetime.strptime(df2.loc[0, 'FINALED'], '%m/%d/%y').date()    
    df2.to_excel(os.path.join(outDir1, afile), index = False)