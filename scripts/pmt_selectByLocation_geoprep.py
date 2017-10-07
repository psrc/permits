# This script takes shapefiles from the workspace and identifies which records intersect the parcels layer. Records that do and do not
# intersect will be filtered and exported to the appropriate folder for updating or further geocoding.
# Output directories should be empty before running script

import os
import arcpy

# Dictionary containing joining features
def prclDictPath(x):
    return {
        '033': 'king\parcel_address_proj.shp',
        '035': 'kitsap\parcels.shp',
        '053': 'pierce\parcels.shp',
        '061': 'snohomish\parcels.shp',
    }[x]

prclRootDir = r'J:\Projects\Geocoding\17GEOCODING\Setup\3FinalProducts'
counties = ['033', '035', '061', '053'] #,  

workspace = r'C:\Users\CLam\Desktop\google_geo_shp'
arcpy.env.workspace = workspace

outWorkspace1 = r'J:\Projects\Permits\16Permit\geocoding\prep\1inbox'
outWorkspace2 = r'J:\Projects\Permits\16Permit\geocoding\prep\0outbox'

fieldName1 = "X_COORD"
fieldName2 = "Y_COORD"

fc = arcpy.ListFeatureClasses()

for cnty in counties:
    fcSubset = [f for f in fc if cnty in f]
    if len(fcSubset) == 0:
        continue
    else:
        parcel = os.path.join(prclRootDir, prclDictPath(cnty)) 
        
        for fs in fcSubset:
            # check for XY coord fields
            fieldNames = [field.name for field in arcpy.ListFields(fs)]
            if ("X_COORD" not in fieldNames) & ("Y_COORD" not in fieldNames):
                # add XY coord fields to shapefile in workspace
                arcpy.AddField_management(fs, fieldName1, "DOUBLE")
                arcpy.AddField_management(fs, fieldName2, "DOUBLE")
                print "Added new fields to " + fs 
                # calculate centroid
                arcpy.CalculateField_management(fs, fieldName1, "!SHAPE.CENTROID.X!", "PYTHON_9.3")
                arcpy.CalculateField_management(fs, fieldName2, "!SHAPE.CENTROID.Y!", "PYTHON_9.3")
                print "Updated XY coordinates to " + fs
            
            arcpy.MakeFeatureLayer_management(fs, "points_lyr")
            totalRowCount = int(arcpy.GetCount_management("points_lyr")[0])
            SelectedLayer = arcpy.SelectLayerByLocation_management("points_lyr", "intersect", parcel)
            
            matchcount = int(arcpy.GetCount_management(SelectedLayer)[0]) 
            if matchcount == 0:
                arcpy.MakeFeatureLayer_management(fs, "nomatch_points_lyr")
                #export records of layer to 1inbox (so they can be geocoded)
                outTableNoMatch = os.path.join(outWorkspace1, fs.strip(".shp") + ".dbf")
                arcpy.CopyRows_management("nomatch_points_lyr", outTableNoMatch)
                print "no features intersected with parcel layer from " + fs
            else:
                #export attribute table where some joins took place to 0outbox (to update master files in permit database)
                outTableSelected2 = os.path.join(outWorkspace2, fs.strip(".shp") + ".dbf")
                arcpy.CopyRows_management(SelectedLayer, outTableSelected2)
                print "Exported selected records of " + fs
                if matchcount < totalRowCount: 
                    #invert selection and export remaining records to 1inbox (so they can be geocoded)
                    NonSelectedLayer = arcpy.SelectLayerByLocation_management("points_lyr", "intersect", parcel, invert_spatial_relationship = "invert")
                    outTableNonSelected = os.path.join(outWorkspace1, fs.strip(".shp") + ".dbf")
                    arcpy.CopyRows_management(NonSelectedLayer, outTableNonSelected)
                    print "Exported nonselected records of " + fs
                
            arcpy.Delete_management(SelectedLayer)
            arcpy.Delete_management("points_lyr") 
            arcpy.Delete_management("nomatch_points_lyr") 
        
##-------------------------------------------------------------------------------------    
#remove XY coordinates from .dbf in J:\Projects\Permits\16Permit\geocoding\prep\1inbox
removeFields = [fieldName1, fieldName2, "lat", "long", "accurcy", "frmttd_"]

# change workspace, remove XY coordinates from 1inbox tables
arcpy.env.workspace = outWorkspace1
tables = arcpy.ListTables()
for dbf in tables:
    arcpy.DeleteField_management(dbf, removeFields)