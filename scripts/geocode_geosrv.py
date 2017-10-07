# This script will take permit .dbfs from the geocoding/inbox directory and process it through each of the
# available geocoding services for its respective county.

import os, re, arcpy

projYear = '2016'
geosrvYear = '2017'
projYr = projYear[2:4]
geosrvYr = geosrvYear[2:4]
inboxDir = 'J:\\Projects\\Permits\\' + projYr + 'Permit\\geocoding\\inbox'
inboxManual = 'J:\\Projects\\Permits\\' + projYr + 'Permit\\geocoding\\inbox_manual' # remaining ungeocoded records stash
outbox = 'J:\\Projects\\Permits\\' + projYr + 'Permit\\geocoding\\outbox_geosrv' # geocoded record stash
interGdbPath = r'J:\Projects\Permits\16Permit\geocoding\christy' # file geodatabase stash
addrLocatorRoot = 'J:\\Projects\\Geocoding\\' + geosrvYr + 'GEOCODING\\AddressLocators' # address locator path

# Dictionaries
runtypeDict = {'siteaddr': 2, 'prcl': 2, 'stcl': 3}
cntyAddrLocDict = {'033': [geosrvYr + 'kin_siteaddr', geosrvYr +'kin_prcl', geosrvYr + 'kin_stcl'],
                   '035': [geosrvYr +'kit_siteaddr', geosrvYr +'kit_stcl'],
                   '053': [geosrvYr +'prc_siteaddr', geosrvYr +'prc_prcl', geosrvYr +'prc_stcl'],
                   '061': [geosrvYr +'sno_siteaddr', geosrvYr +'sno_prcl', geosrvYr +'sno_stcl']
                   }
   
fullList = [f for f in os.listdir(inboxDir) if f.endswith('.dbf')] #all files ending in .dbf, list comprehension

for afile in fullList:
    arcpy.env.workspace = inboxDir
    
    # extract from filename
    cnty = afile[1:4]
    jurisPattern = re.compile('[A-Z]+')
    juris = jurisPattern.findall(afile)[0]
    
    #create file geodatabase
    interGdbName = cnty + juris + '.gdb'
    currGdb = os.path.join(interGdbPath, interGdbName)
    arcpy.CreateFileGDB_management(interGdbPath, interGdbName)
            
    #loop through addrLocators
    addrLocatorNames = cntyAddrLocDict[cnty] 
    
    unmatchedTbl = ["unmatch"+str(i) for i in range(0, len(addrLocatorNames))] #initialize ungeocoded table names
    
    #address assignement fields
    addrFields = "Street ADDRESS;City City NONE;State State NONE;ZIP ZIP"
    inDir = r'J:\Projects\Permits\16Permit\geocoding\inbox'
    dropFields = ['Status', 'Score', 'Match_type', 'Match_addr', 'Side', 'Ref_ID', 'X', 'Y', 'User_fld', 'Addr_type', 'ARC_Street', 'ARC_ZIP']
    
    # loop through address locators in respective county
    c = 0
    for loc in addrLocatorNames:
        locPattern = re.compile('_(\\w+)')
        locRef = locPattern.findall(loc)[0]
        
        locator = os.path.join(addrLocatorRoot, loc)
        resultFeature = os.path.join(currGdb, 'geocode_result' + str(c))
        
        # geocode
        if c == 0:
            arcpy.GeocodeAddresses_geocoding(os.path.join(inDir, afile), locator, addrFields, resultFeature)
        else:
            arcpy.GeocodeAddresses_geocoding(os.path.join(currGdb, unmatchedTbl[c-1]), locator, addrFields, resultFeature)
        
        totalRowCount = int(arcpy.GetCount_management(resultFeature)[0])
        print "Total Number of Records for " + juris + ": " + str(totalRowCount)
        
        # create layer from which to query by attribute
        arcpy.MakeFeatureLayer_management(resultFeature, "lyr" + str(c))
        arcpy.SelectLayerByAttribute_management("lyr" + str(c), "NEW_SELECTION", ' "X" <> 0 ')
        selectLayerCount = int(arcpy.GetCount_management("lyr" + str(c))[0])
        print "Number of geocoded records by " + loc + ": " + str(selectLayerCount)
        
        if selectLayerCount == totalRowCount:
            arcpy.CopyRows_management("lyr" + str(c), os.path.join(currGdb, "out" + str(c)))
            arcpy.CalculateField_management(os.path.join(currGdb, "out" + str(c)), "RUNTYPE", runtypeDict[locRef], "PYTHON_9.3")
            arcpy.TableToExcel_conversion(os.path.join(currGdb, "out" + str(c)), os.path.join(outbox, cnty + juris + "_geod.xls"))
            print juris + " is done!"
            c = c + 1
            break
        elif selectLayerCount == 0:
            arcpy.CopyRows_management(resultFeature, os.path.join(currGdb, unmatchedTbl[c]))
            arcpy.DeleteField_management(os.path.join(currGdb, unmatchedTbl[c]), dropFields)
        else:
            arcpy.CopyRows_management("lyr" + str(c), os.path.join(currGdb, "out" + str(c)))
            arcpy.CalculateField_management(os.path.join(currGdb, "out" + str(c)), "RUNTYPE", runtypeDict[locRef], "PYTHON_9.3")
            # select records that didn't geocode
            arcpy.SelectLayerByAttribute_management("lyr" + str(c), "SWITCH_SELECTION")
            arcpy.CopyRows_management("lyr" + str(c), os.path.join(currGdb, unmatchedTbl[c]))
            arcpy.DeleteField_management(os.path.join(currGdb, unmatchedTbl[c]), dropFields)
        c = c + 1
         
    # change workspace
    arcpy.env.workspace = currGdb
    # search for tables 
    outTables = arcpy.ListTables("out*")
    unmatchTables = arcpy.ListTables("unmatch*")
    if len(outTables) == 0:
        arcpy.TableToExcel_conversion(str(unmatchTables[len(unmatchTables)-1]), os.path.join(inboxManual, cnty + juris + "_geomanual.xls"))
        print "Exported remainder to inbox_manual"
        for i in range(0, len(addrLocatorNames)):
            arcpy.Delete_management("lyr" + str(i))
        continue
    else:
        arcpy.Merge_management(outTables, "outFinal") # merge outTables
        # get record counts
        arcpy.MakeTableView_management("outFinal", "outFinalView")
        outRecordsCount = int(arcpy.GetCount_management("outFinalView")[0])
        arcpy.MakeTableView_management("geocode_result0", "origRecNumberView")
        origRecordsCount = int(arcpy.GetCount_management("origRecNumberView")[0])
        if outRecordsCount != origRecordsCount:
            arcpy.Append_management(str(unmatchTables[len(unmatchTables)-1]), "outFinal", "NO_TEST")
            arcpy.TableToExcel_conversion("outFinal", os.path.join(outbox, cnty + juris + "_geod.xls"))
            arcpy.TableToExcel_conversion(str(unmatchTables[len(unmatchTables)-1]), os.path.join(inboxManual, cnty + juris + "_geomanual.xls"))
            print "Exported remainder to inbox_manual"
        # delete in-memory layers/table views
        for i in range(0, len(addrLocatorNames)):
            arcpy.Delete_management("lyr" + str(i))
        arcpy.Delete_management("outFinalView")
        arcpy.Delete_management("origRecNumberView")
