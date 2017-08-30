import os, usaddress
import pandas as pd
import numpy as np
import re
from simpledbf import Dbf5
from collections import Counter

# function to extract piece of parsed address
def extractParsedAddr(parsedAddresses, label):
    v = [item for item in parsedAddresses if label in item] # list tuples containing the label
    if len(v) == 1:
        v2 = map(str, [x[0] for x in v])[0]
        vv = v2
    elif (label == 'AddressNumber') & (len(v) > 1):
        v2 = map(str, [x[0] for x in v])[0]
        vv = v2
    elif (label == 'SubaddressIdentifier') & (len(v) > 1):  
        v2 = map(str, [x[0] for x in v])[0]
        vv = v2
    else:
        v2 = map(str, [x[0] for x in v])
        v3 = ' '.join(v2)
        vv = v3
    return vv

# Dictionary for template and usaddress column names
addrDict = {
        'AddressNumber' : 'HOUSENO',
        'StreetNamePreDirectional': 'PREFIX',
        'StreetName': 'STRNAME',
        'StreetNamePostType': 'STRTYPE',
        'StreetNamePostDirectional': 'SUFFIX', 
        'OccupancyType': 'UNITBLD_TYPE',
        'OccupancyIdentifier': 'UNIT',
        }

addrDict2 = {
        'SubaddressIdentifier' : 'HOUSENO',
        'StreetNamePreDirectional': 'PREFIX',
        'StreetName': 'STRNAME',
        'StreetNamePostType': 'STRTYPE',
        'StreetNamePostDirectional': 'SUFFIX', 
        'OccupancyType': 'UNITBLD_TYPE',
        'OccupancyIdentifier': 'UNIT',
        }

addrDictKey = addrDict.keys() # list all keys (usaddress.LABELS) in AddrDict 
addrDictKey2 = addrDict2.keys() # list all keys (usaddress.LABELS) in AddrDict2 
                           
rootDir = r'J:\Projects\Geocoding\17GEOCODING\Setup\1Raw\Pierce'
Dir = 'Tax_Parcels'

dbf = Dbf5(os.path.join(rootDir, Dir, 'Tax_Parcels.dbf'))

df = dbf.to_dataframe()

df['HOUSENO'] = np.nan
df = df.reindex(columns = np.append(df.columns.values, ['PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'UNITBLD_TYPE', 'UNIT', 'SUBAREA']))
df['PREFIX'] = df['PREFIX'].astype(str)
df['STRNAME'] = df['STRNAME'].astype(str)
df['STRTYPE'] = df['STRTYPE'].astype(str)
df['SUFFIX'] = df['SUFFIX'].astype(str)
df['SUBAREA'] = df['SUBAREA'].astype(str)
df['UNIT'] = df['UNIT'].astype(str)
df['UNITBLD_TYPE'] = df['UNITBLD_TYPE'].astype(str)

# use usaddress package to parse address into a tupled list
for i in range(len(df.index)): # loop through each row
    if isinstance(df.ix[df.index[i],'Site_Addre'], float): # if ADDRESS is Nan (float)
        continue
    else:
        addr = df.ix[df.index[i], 'Site_Addre'] 
#        addrParsed = set(usaddress.parse(addr)) # parse address and remove any duplicate tuples
        addrParsedOrig = usaddress.parse(addr)
        temp = []
        for a,b in addrParsedOrig :
            if (a,b) not in temp: #to check for the duplicate tuples
               temp.append((a,b))
        addrParsed = temp * 1 #copy temp to d
        addrElements = [a[0] for a in addrParsed] # untupled list
        if 'XXX' in addrElements:
            continue
        else:
            hn = [h[0] for h in addrParsed if 'AddressNumber' in h] # isolate 'AddressNumber'
            pattern = re.compile('[A-Z]|-') # if there are alphabet or dashes detected in the 'AddressNumber'
            pattern4 = re.compile('/') # if there slash in the 'AddressNumber'
            if (len(hn) == 0):
                continue
            elif (len(pattern.findall(hn[0])) != 0):
                continue
            else:
                origLabels = [x[1] for x in addrParsed] # list all labels in tuples
                if (('TO', 'StreetName') in addrParsed) | (('TO', 'StreetNamePreDirectional') in addrParsed):
                    counts = Counter(t for t in origLabels) # evaluate # of AddressNumber and StreetName in origLabels
                    if counts['AddressNumber'] >= 2:
                        # compare the addressNumbers
                        pattern3 = re.compile('[A-Z]|-|/')
                        hns = [h for h in addrParsed if 'AddressNumber' in h]
                        hnExclude = [v for v in hns if len(pattern3.findall(v[0])) != 0]
                        exclude = []
                        if len(hnExclude) != 0: # there something to exclude                      
                            exclude = exclude + hnExclude
                        else:
                            addNum = [an for an in addrParsed if an[1] == 'AddressNumber'][0]
                            exclude.append(addNum)
                        if ('TO', 'StreetName') in addrParsed:
                            exclude.append(('TO', 'StreetName'))
                        else:
                            exclude.append(('TO', 'StreetNamePreDirectional'))
                        addrParsedChg = [y for y in addrParsed if y not in exclude]
                        labels = [x for x in origLabels if x in addrDictKey]
                        for label in labels:
                            extractValue = extractParsedAddr(addrParsedChg, label) 
                            df.set_value(df.index[i], addrDict[label], extractValue)
#                    elif counts['StreetName'] >= 2:
#                         strnames = [s for s in addrParsed if 'StreetName' in s]
                    else:
                        labels = [x for x in origLabels if x in addrDictKey]
                        for label in labels:
                            extractValue = extractParsedAddr(addrParsed, label) 
                            df.set_value(df.index[i], addrDict[label], extractValue)
                elif (len(pattern4.findall(hn[0])) != 0): #('TO','SubaddressType') in addrParsed: #if TO is SubaddressType
                    labels = [x for x in origLabels if x in addrDictKey2]
                    for label in labels:
                        extractValue = extractParsedAddr(addrParsed, label) 
                        pattern2 = re.compile('\\d+')
                        if (label == 'SubaddressIdentifier') & (len(pattern2.findall(extractValue)) != 0):
                            extractDigits = pattern2.findall(extractValue)[0]
                            df.set_value(df.index[i], addrDict2[label], extractDigits) # need dict between template col and usaddress col
                        else:    
                            df.set_value(df.index[i], addrDict2[label], extractValue) # need dict between template col and usaddress col
                else:
                    labels = [x for x in origLabels if x in addrDictKey]
                    for label in labels:
                        extractValue = extractParsedAddr(addrParsed, label) 
                        df.set_value(df.index[i], addrDict[label], extractValue) # need dict between template col and usaddress col

# clean individual columns
parsedHeaders = ['HOUSENO', 'PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'SUBAREA', 'UNITBLD_TYPE', 'UNIT']
for header in parsedHeaders:
    for i in range(len(df.index)):
        p = df.ix[df.index[i], header]
        if p == 'nan':
            df.set_value(df.index[i], header, '')                          
        if (header == 'UNIT') & (p in ['KP N', 'KP S', 'KP', 'FI', 'KI', 'AI']):
            df.set_value(df.index[i], 'SUBAREA', p)
        if (header == 'PREFIX') & (p not in ['N', 'E', 'S', 'W', 'NE', 'NW', 'SE', 'SW', 'NORTH', 'EAST', 'SOUTH', 'WEST']):
            df.set_value(df.index[i], 'PREFIX', '') 
        if (header == 'STRTYPE') & (p == 'KP'):
            df.set_value(df.index[i], 'SUBAREA', p)
            df.set_value(df.index[i], 'STRTYPE', '')
            pattern3 = re.compile('\\sSTCT|\\sAVCT|\\sROAD')
            z = df.ix[df.index[i], 'STRNAME']
            if len(pattern3.findall(z)) != 0:
                newStrtype = re.compile('\s(\w+)').findall(z)[0]
                newStrname = re.compile('(\w+)\s').findall(z)[0]
                df.set_value(df.index[i], 'STRTYPE', newStrtype)
                df.set_value(df.index[i], 'STRNAME', newStrname)
         
dfExport = df[['OBJECTID', 'TaxParcelN', 'Site_Addre', 'HOUSENO', 'PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'SUBAREA', 'UNITBLD_TYPE', 'UNIT']]                         
dfExport.to_excel(os.path.join(r'J:\Projects\Geocoding\17GEOCODING\Setup\2Working\pierce', 'taxparcels_addr.xlsx'), index = False)                                        