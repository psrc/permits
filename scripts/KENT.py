import pandas as pd 
import numpy as np
import os
os.getcwd()

working_dir = 'J:/Projects/Permits/17Permit/data/2working/'

temp = pd.read_csv(working_dir + 'template.csv')
raw_data = pd.read_csv(working_dir + 'KENT.csv')

test1 = raw_data 
# import the permit number and address column name 
my_permit_id = 'Permit ID#' #the column name for permit id from raw data
my_address = 'Site Address'

######### Sort: Creat Sort ID by following previous format. The format could be different from city to city.  
test1['SORT'] = ''
for i in range(len(test1)): 
    p = test1['Permit ID#'][i]
    p1 = '2017' + p[:5] + '0' + p[-4:]
    test1['SORT'][i] = p1

# Site Address: split full address into ['HOUSENO', 'PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'UNIT_BLD', 'CITY', 'STATE', 'ZIP'] columns
col1 = ['HOUSENO', 'PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'UNIT_BLD', 'CITY', 'STATE', 'ZIP']
for c in col1:
    test1[c] = ''

# Roughly split full adress into columns, without QA/QC
for i in range(len(test1)):
    test1[my_address][i] = test1[my_address][i].replace(',', ' ')
    address = test1[my_address][i].split()
    if len(address) <= 9:
        for j in range(len(address)): 
            test1[col1[j]][i] = address[j]
    else: 
        print address 
        #for j in range(4): #why 4? already investigated (the default is 6)
            #test1[col1[j]][i] = address[j+2]

print np.unique(test1[[ 'STRTYPE']])
print np.unique(test1[[ 'STRNAME']])
list_prefix = ['S', 'SE', 'SW', 'W', 'NW', 'N','NE','E']
list_suffix = ['S', 'SE', 'SW', 'W', 'NW', 'N','NE','E']

# Fix the prefix 
for i in range (len(test1)): 
    if test1['PREFIX'][i] not in list_prefix: 
        # move the value into next column 
        test1.loc[i:i,['PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'UNIT_BLD']] = test1.loc[i:i,['PREFIX', 'STRNAME', 'STRTYPE', 'SUFFIX', 'UNIT_BLD']].shift(1,axis=1)
    else:
        continue 

city_list = ['Auburn', 'AUBURN', 'RENTON', 'ENUMCLAW', 'Enumclaw', 'BEND', 'CARNATION', 
            'DUVALL', 'ISSAQUAH', 'Issaquah', 'KENT', 'King', 'PRESTON', 'RAVENSDALE',
            'REDMOND', 'Renton', 'SAMMAMISH', 'SNOQUALMIE', 'VASHON', 'WOODINVILLE']


street_type = ['AVE', 'BLVD', 'CIR','CIRCLE','CROSSING', 'COVE', 'CT', 'DR', 'HWY', 
               'LN', 'LINE', 'LOOP', 'PL', 'RD', 'ROAD','Road','SHORE',
               'ST', 'TRAIL', 'TRL',  'WAY']

backup_test1 = test1 # just in case, if I lost all data later 

# use ['SUFFIX'] as the base to inspect the row # data, QA/QC street name and unit building name.
for i in range(len(test1)): 
    #print test1['SUFFIX'][i]
    if len(test1[my_address][i].split()) > 4: 
        #print i 
        if str(test1['SUFFIX'][i]) in street_type: 
            test1['STRNAME'][i] = test1['STRNAME'][i] + ' ' + test1['STRTYPE'][i] 
            test1.loc[i:i,['STRTYPE', 'SUFFIX', 'UNIT_BLD']] = test1.loc[i:i,['STRTYPE', 'SUFFIX', 'UNIT_BLD']].shift(-1,axis=1)
        else: 
            if str(test1['SUFFIX'][i]) in list_suffix: # suffix is suffix
                continue
            if str(test1['SUFFIX'][i]) in city_list: # city name in suffix
                test1.loc[i:i,['SUFFIX', 'UNIT_BLD']] = test1.loc[i:i,['SUFFIX', 'UNIT_BLD']].shift(1,axis=1)
            if str(test1['SUFFIX'][i]) in ['WA']: # state name in suffix
                test1.loc[i:i,['SUFFIX', 'UNIT_BLD']] = test1.loc[i:i,['SUFFIX', 'UNIT_BLD']].shift(2,axis=1)
            if str(test1['SUFFIX'][i])[0] == 9: # zipcode in suffix
                test1.loc[i:i,['SUFFIX', 'UNIT_BLD']] = test1.loc[i:i,['SUFFIX', 'UNIT_BLD']].shift(2,axis=1)
            else: #may be street name in suffix ? or nothing in suffix 
                #print test1['ADDRESS'][i]
                continue
            #test1.loc[i:i,['SUFFIX', 'UNIT_BLD']] = test1.loc[i:i,['SUFFIX', 'UNIT_BLD']].shift(1,axis=1)
    else: 
        continue 

#validate
#print np.unique(test1[[ 'HOUSENO']])
print np.unique(test1[[ 'PREFIX']])
print np.unique(test1[[ 'STRNAME']])
print np.unique(test1[[ 'STRTYPE']])
print np.unique(test1[[ 'SUFFIX']])
print np.unique(test1[[ 'UNIT_BLD']])
print np.unique(test1[[ 'CITY']])
print np.unique(test1[[ 'STATE']])
print np.unique(test1[[ 'ZIP']])

test1['ZIP'] = test1['Site ZipCode']

print np.unique(test1['ZIP'])
drop_index = []
for i in range(len(test1)):
    des = test1[i:i+1]['Work Description'].tolist()[0].split()
    if 'COMMERCIAL' in des:
        print i 
        for j in range(len(des)):
            if des[j] == 'COMMERCIAL':
                print des[j:j+9]
        drop_index = drop_index + [i]

print drop_index
test2 = test1.drop(test1.index[drop_index]).reset_index(drop=True)

# TYPE, PS, BLDGS, UNITS
'''
Step1: get MF/Mobile home unit number (###)
* find unit number from work description
* confirm MF numbers from structure type information, permit activities infor, or other available informations

Step2: get SF unit number (1, -1)
* detect if it is new
* detect if it is demolished 
* detect if it is additional dewell unit - depends on new structure type to jusdge unit#
'''

test2['UNITS'] = ''
test2['PS'] = ''
test2['TYPE'] = ''
test2['BLDGS'] = 1 #default - will have it updated if need

print np.unique(test2['Structure Type'])
print np.unique(test2['Permit Activity'])
print "----------------check correlation---------------------"
print np.unique(test2[(test2['Structure Type'] == 'ADU')]['Permit Activity'])
print np.unique(test2[(test2['Structure Type'] == 'MF')]['Permit Activity'])
print np.unique(test2[(test2['Structure Type'] == 'MH')]['Permit Activity'])
print np.unique(test2[(test2['Structure Type'] == 'OTHER')]['Permit Activity'])
print np.unique(test2[(test2['Structure Type'] == 'SF')]['Permit Activity'])

# -----> Step 1

# find unit number from work description
units_index = []
for i in range(len(test2)):
    des = test2[i:i+1]['Work Description'].tolist()[0].split()
    if 'UNITS' in des:
        print i 
        for j in range(len(des)):
            if des[j] == 'UNITS':
                j = max(0, j-4)
                print des[j:j+10]
        units_index = units_index + [i]

    else: 
        if 'UNITS:' in des:
            print i 
            for j in range(len(des)):
                if des[j] == 'UNITS:':
                    j = max(0, j-4)
                    print des[j:j+10]
            units_index = units_index + [i]

print units_index
###### hard coding required {unit index : number of unit } ######
units_index_dict = {3: 154, 4:28, 5:2, 6:2, 7:2, 8:2, 9:32, 10:16, 11:14, 12:16, 
                    492:4, 493:2, 494:2, 495:2, 496:4, 496:4, 497:4, 
                    498:4, 499:4, 500:4}

#fill in the unit number found at work descriptions 
for i in units_index:
    test2.loc[i, 'UNITS'] = units_index_dict[i]
    test2.loc[i, 'PS'] = 0

# Validate: comfirm if we got everything for multi-family, based on structure type and permit activity, to check if there is any MF permits been left behind 
print len(units_index_dict)
print len(test2[test2['Structure Type'] == 'MF'])
print len(test2[(test2['Structure Type'] == 'MF') & (test2['Permit Activity'] == 'New')])
#If the numbers above are all same, perfectly match! No need to do futhure investigation 

# BUILDING NUMBERS FOR THESE MULTI-FAMILY UNITS
# building
# find unit number from work description
building_index = []
for i in units_index:
    des = test2[i:i+1]['Work Description'].tolist()[0].split()
    if 'BUILDING' in des:
        print i 
        for j in range(len(des)):
            if des[j] == 'BUILDING':
                j = max(0, j-4)
                print des[j:j+10]
        building_index = building_index + [i]

    else: 
        if 'BUILDING' in des:
            print i 
            for j in range(len(des)):
                if des[j] == 'BUILDING':
                    j = max(0, j-4)
                    print des[j:j+10]
            building_index = building_index + [i]

'''
################### hard coding required {building index : number of building } ##########################
building_index_dict = {:}

#fill in the building number found at work descriptions 
for i in building_index:
    test2.loc[i, 'BLDGS'] = building_index_dict[i]
    
    '''

# ------> step2
print len(test2[test2['Structure Type'] == 'SF'])
print len(test2[(test2['Structure Type'] == 'SF') & (test2['Permit Activity'] == 'New')])

test2[(test2['Structure Type'] == 'SF') & (test2['Permit Activity'] == 'New')]['UNITS'] = 1
test2[(test2['Structure Type'] == 'SF') & (test2['Permit Activity'] == 'New')]['PS'] = 0
test2[(test2['Structure Type'] == 'SF') & (test2['Permit Activity'] == 'New')]['TYPE'] = 111
print len(test2['TYPE'] == 111)

test2[(test2['Structure Type'] == 'SF') & (test2['Permit Activity'] == 'Addition')]['UNITS'] = 1
test2[(test2['Structure Type'] == 'SF') & (test2['Permit Activity'] == 'Addition')]['PS'] = 1
test2[(test2['Structure Type'] == 'SF') & (test2['Permit Activity'] == 'Addition')]['TYPE'] = 111
print len(test2['TYPE'] == 111)

print len(test2[test2['Structure Type'] == 'SF'])
print len(test2[(test2['Structure Type'] == 'SF') & (test2['Permit Activity'] == 'Addition')])

# find the situation from work description
units_index = []
for i in range(len(test2)):
    des = test2[i:i+1]['Work Description'].tolist()[0].split()
    if 'UNITS' in des:
        print i 
        for j in range(len(des)):
            if des[j] == 'UNITS':
                j = max(0, j-4)
                print des[j:j+10]
        units_index = units_index + [i]

# Demolish
# find unit number from work description
demo_index = []
for i in range(len(test2)):
    des = test2[i:i+1]['Work Description'].tolist()[0].split()
    if 'DEMO' in des:
        print i 
        for j in range(len(des)):
            if des[j] == 'DEMO':
                j = max(0, j-4)
                print des[j:j+10]
        demo_index = units_index + [i]

    else: 
        if 'DEMO' in des:
            print i 
            for j in range(len(des)):
                if des[j] == 'DEMO':
                    j = max(0, j-4)
                    print des[j:j+10]
            demo_index = units_index + [i]

print demo_index
for i in demo_index:
    test2.loc[i,'TYPE']= 111
    test2.loc[i,'PS']= 5

###### NOTES, 2, 3, 4, 5
for c in ['NOTES', 'NOTES2', 'NOTES3', 'NOTES4', 'NOTES5']:
    test2[c] = ''

test2['NOTES'] = test2['Project Name']
#test2['NOTES2'] = test2['Lot Area/Size']
test2['NOTES3'] = test2['Structure Type']
test2['NOTES5'] = test2['Status']
test2['NOTES6'] = ''
test2['NOTES7'] = ''
#test2['NOTES6'] = test2['Type'] # just reserve some info from raw data
#test2['NOTES7'] = test2['Sub-Type'] # reserve some info from raw data 
for i in range(len(test2)):
    work = test2['Work Description'][i]
    test2['NOTES4'][i] = work[:50]

### Extra information to carry over if needed
'''
The first two digits indicate the project year. The second two digits indicate the county in which the permit is located by abbreviated FIPS county code. The next five digits (included since 2000) indicate the jurisdiction of permit issue by FIPS place code. The last five digits serve as an automatic counter.
'''
test3 = test2
test3['PERMITNO'] = test3['Permit ID#']
test3['PSRCIDN'] = '' # no data 
test3['PIN'] = test3['Tax PID#'] # no data 
test3['MULTIREC'] = ''
test3['LANDUSE'] = ''
test3['CONDO'] = ''
test3['ZONING'] = ''
test3['LOTSIZE'] = '' 
test3['PIN_PARENT'] = ''
test3['FINALED'] = test3['Final Date']
test3['ISSUED'] = test3['Issue Date']
test3['STATUS'] = test3['Status']
test3['VALUE'] = test3['Est. Value']
test3['ADDRESS'] = test3['Site Address']

#### Template
final_col = temp.columns.tolist()
print final_col
df = test3[final_col]

os.getcwd()
df.to_csv(r'J:\Projects\Permits\17Permit\data\2working\after_process_KENT3.csv')
