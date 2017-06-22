# This script will evaluate xlsx files in 3importready and do additional formatting, 
# QC, and adding a 'macro row' underneath the column header.
 
import os
import datetime
import pandas as pd

# dictionaries
# Multirec dictionary
d = {'TRUE': True, None: False, 'FALSE': False}

# permit status dictionary
status = {
        'ISSUED': ['OPEN', 'ACTIVE'],
        'FINALED': ['FINAL', 'CLOSED', 'FINALLED', 'C.O. ISSUED']
         }

# directories
rootDir = r'J:\Projects\Permits\16Permit\data\3importready'
outDir = r'J:\Projects\Permits\16Permit\data\3importready\christy_macro_test'

# select only files that need processing
fullList = os.listdir(rootDir)
jurisFiles = [] # store file names in 3importready

for file in fullList:
    if file.endswith(".xlsx"):
        jurisFiles.append(file)

jurisCompleted = os.listdir(outDir)
juris2Process = [afile for afile in jurisFiles if afile not in jurisCompleted]

for afile in juris2Process:
    df = pd.read_excel(os.path.join(rootDir, afile), header = 0)
    df = df.sort_values(by = 'SORT', ascending=True) #sort table
    
    # update PIN with leading zeros
    cnty = afile[:3]   
    if (cnty == '033' or cnty == '053' and df['PIN'][0] > 10) or (cnty == '035' and df['PIN'][0] > 14):
        df['PIN'] = df['PIN'].astype(str)
        for i in range(len(df.index)):
            p = df.ix[df.index[i], 'PIN']
            if p == 'nan':
                df.set_value(df.index[i], 'PIN', '')
            else:
                if cnty == '033' or cnty == '053':
                    if len(p) < 10:
                        pform = '{0:0>10}'.format(p)
                        df.set_value(df.index[i], 'PIN', pform)
                else:
                    if len(p) < 14:
                        pform2 = '{0:0>14}'.format(p)
                        df.set_value(df.index[i], 'PIN', pform2)
    
    # fill in PSRCID col                                           
    for i in range(len(df.index)):
         df.set_value(df.index[i], 'PSRCIDN', i+1)   
    df['PSRCIDN'] = df['PSRCIDN'].astype(int) 
    
    # add macro row and reorder so macro row is below header
    df = df.reset_index(drop=True)   
    newRow = [999999, 'TEXT', 'TEXT', 'TRUE', 'TEXT', 'TEXT', 999999, 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT',	'TEXT', '1/1/01',	'1/1/01', 'TEXT', 'TEXT', 'TEXT',	999999, 9999999, 'TEXT', 'TEXT', '$999,999,999', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 999999, 'TEXT']
    df.loc[-1] = newRow
    df.index = df.index + 1
    df = df.sort_index()
    
    # update macro row date strings to be date object
    df.ix[0, 'ISSUED'] = datetime.datetime.strptime(df.ix[0, 'ISSUED'], '%m/%d/%y').date()
    df.ix[0, 'FINALED'] = datetime.datetime.strptime(df.ix[0, 'FINALED'], '%m/%d/%y').date()
    
    # update Multirec field
    df['MULTIREC'] = df['MULTIREC'].map(d)
    
    # update status field
    sItems = status.items()
    for i in range(len(df.index)):
        currVal = df.ix[i, 'STATUS']
        newVal = [s[0] for s in sItems if currVal in s[1]]
        if len(newVal) > 0:
            newValUpd = newVal[0]
            df.ix[i, 'STATUS'] = newValUpd
        else:
            continue
       
    df.to_excel(os.path.join(outDir, afile), index = False)


         
     
