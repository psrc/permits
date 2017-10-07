# This script will format jurisdictions for permit processing
# user must list jurisdictions that are 'script ready'
 
import os, usaddress
import pandas as pd

# function to extract piece of parsed address
def extractParsedAddr(parsedAddresses, label):
    v = [item for item in parsedAddresses if label in item] # list tuples containing the label
    if len(v) == 1:
        v2 = map(str, [x[0] for x in v])[0]
        vv = v2
    else:
        v2 = map(str, [x[0] for x in v])
        v3 = ' '.join(v2)
        vv = v3
    return vv

# function to remove decimal places from text (i.e. PIN)
def trim_fraction(text):
    if '.0' in text:
        return text[:text.rfind('.0')]
    return text

# Dictionary for template and usaddress column names
addrDict = {
        'AddressNumber' : 'HOUSENO',
        'StreetNamePreDirectional': 'PREFIX',
        'StreetName': 'STRNAME',
        'StreetNamePostType': 'STRTYPE',
        'StreetNamePostDirectional': 'SUFFIX', 
#        'OccupancyType':,
#        'OccupancyIdentifier':,
        }

addrDictKey = addrDict.keys() # list all keys (usaddress.LABELS) in AddrDict 

# list of jurisdiction names
jurisdictions = ['redmond']#

for juris in jurisdictions:
    # format jurisdiction lookup table
    jurisLu = pd.read_excel(r'J:\Projects\Permits\Admin\Lookup\a_juris_lookup.xlsx')
    jurisLu['cnty'] = jurisLu['cnty'].astype(str).apply('{0:0>3}'.format) # convert to string and pad with leading zero
    
    # raw permit data       
    rootDir = r'J:\Projects\Permits\16Permit\data\1raw'
    jurisFilter = jurisLu[jurisLu['juris'].str.contains(juris)]  
    county = str(jurisFilter.ix[jurisFilter.index[0],'county'])
    cnty = jurisFilter.ix[jurisFilter.index[0],'cnty'] 
    
    filePath = os.path.join(rootDir, county, juris)
    jurisFile = os.listdir(filePath)[0] # list file
    ext = jurisFile[jurisFile.rfind('.'):]
    
    # read csv or excel file...
    if ext == '.csv':
        df = pd.read_csv(os.path.join(filePath, jurisFile), header = 0)
    else:
        df = pd.read_excel(os.path.join(filePath, jurisFile), header = 0)
    
    # Check if juris has a lookup table, apply to template
    lookupFile = 'template' + cnty + '_' + juris + '.xlsx'
    lookup = os.path.join(r'J:\Projects\Permits\Admin\Lookup', lookupFile)
    lookupFileExists = os.path.exists(lookup)
    if lookupFileExists == True:   
        lu = pd.read_excel(lookup)
        luDict = lu.set_index('raw')['master'].to_dict()
        df2 = df.rename(columns=luDict)
        keepCol = luDict.values() # keep columns in lu.master
        template = pd.DataFrame(columns = list(lu.ix[:, 'master']), index = []) # create template df 
        df3 = df2.loc[:, keepCol] # select columns that are relevant
        dfExport = template.append(df3)
        dfExport = dfExport[template.columns] # reorder columns
        dfExport = dfExport.dropna(subset = ['PERMITNO', 'PIN', 'ADDRESS'], how = 'all') # remove records if PERMITNO, PIN, and ADDRESS is NaN
           
    # use usaddress package to parse address into a tupled list
    for i in range(len(dfExport.index)): # loop through each row
        if isinstance(dfExport.ix[dfExport.index[i],'ADDRESS'], float): # if ADDRESS is Nan (float)
            continue
        else:
            addr = dfExport.ix[dfExport.index[i], 'ADDRESS'] 
            addrParsed = usaddress.parse(addr) # parse address
            origLabels = [x[1] for x in addrParsed] # list all labels in tuples
            
            labels = [x for x in origLabels if x in addrDictKey]
            for label in labels:
               extractValue = extractParsedAddr(addrParsed, label) 
               dfExport.set_value(dfExport.index[i], addrDict[label], extractValue) # need dict between template col and usaddress col 
    
    ## additional formatting
    # update PIN with leading zeros
    if (cnty == '033' or cnty == '053' and dfExport['PIN'][0] > 10) or (cnty == '035' and dfExport['PIN'][0] > 14):
        dfExport['PIN'] = dfExport['PIN'].astype(str)
        dfExport['PIN'] = dfExport['PIN'].apply(trim_fraction)
        for i in range(len(dfExport.index)):
            p = dfExport.ix[dfExport.index[i], 'PIN']
            if p == 'nan':
                dfExport.set_value(dfExport.index[i], 'PIN', '')
            else:
                if cnty == '033' or cnty == '053':
                    if len(p) < 10:
                        pform = '{0:0>10}'.format(p)
                        dfExport.set_value(dfExport.index[i], 'PIN', pform)
                else:
                    if len(p) < 14:
                        pform2 = '{0:0>14}'.format(p)
                        dfExport.set_value(dfExport.index[i], 'PIN', pform2)
    
    # convert to uppercase                    
    strCols = ['ADDRESS', 'PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'STATUS', 'NOTES', 'NOTES2', 'NOTES3', 'NOTES4', 'NOTES5', 'NOTES6']
    for col in strCols:
        dfExport[col] = dfExport[col].str.upper()
        
    # export       
    outFilename = cnty + juris.upper() + '.xlsx'            
    dfExport.to_excel(os.path.join(filePath, outFilename), sheet_name = juris, index = False) 

