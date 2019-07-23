# This script produces a record-level permit dataset within an issued date range of permits that fall within the A Regional Coalition for Housing (ARCH) sphere

import os
import pyodbc
from shapely.geometry import Point
import geopandas as gp
from geopandas import GeoSeries, GeoDataFrame
import pandas as pd

outdir = r"J:\Projects\Permits\17Permit\request\DATAREQUEST\arch"
curr_year = '17'
issued_date_from = '2017-01-01'
issued_date_to = '2017-12-31'

coord_sys = 'epsg:2285'
keep_cols = ['PROJYEAR', 'PSRCID', 'PSRCIDXY', 'MULTIREC','PERMITNO', 'SORT', 'CNTY', 'MULTICNTY', 'PLC', 'JURIS',
                 'PLC' + curr_year, 'JURIS' + curr_year, 'PLCNOTE','PIN', 'PIN_PARENT','ADDRESS', 'HOUSENO','PREFIX', 'STRNAME', 'STRTYPE', 
                 'SUFFIX', 'UNIT_BLD', 'ZIP', 'ISSUED', 'FINALED', 'OTHER_DT','STATUS', 'TYPE', 'PS', 
                 'UNITS', 'BLDGS', 'LANDUSE', 'CONDO', 'VALUE', 'ZONING',  'X_COORD', 'Y_COORD','NOTES', 'NOTES2', 
                 'NOTES3', 'NOTES4', 'NOTES5','NOTES6', 'RUNTYPE', 'Month', 'SUBAREA','TRACT10','TRACTID', 'BLKGRPID', 
                 'BLOCKID', 'TAZ10', 'TAZ4K', 'FAZ10', 'UGA' + curr_year, 'TYPE2', 'TYPE3', 'TYPE4', 'PS2','ISSUEDYEAR', 'LOTSIZE']

def sqlconn(dbname):
    con = pyodbc.connect('DRIVER={SQL Server};SERVER=AWS-PROD-SQL\COHO;DATABASE=' + dbname + ';trusted_connection=true')
    return con

def get_permits_current_dec():
    con = sqlconn('Sandbox')
    table_name = 'Christy.tblBuildingPermits'
    query = "SELECT * FROM " + table_name + " WHERE ISSUED BETWEEN " + "'" + issued_date_from + "'" + " AND " +  "'" + issued_date_to + "'"
    df = pd.read_sql(query, con)
    con.close()
    return df

def gp_table_join(update_table,join_shapefile,join_field):
    
    # open join shapefile as a geodataframe
    join_layer = gp.GeoDataFrame.from_file(join_shapefile)

    # table join
    merged = join_layer.merge(update_table, on=join_field)
    
    return merged

def gp_spatial_join(target_shapefile,join_shapefile,coord_sys,keep_columns):
    
    ### open join shapefile as a geodataframe
    ##join_layer = gp.GeoDataFrame.from_file(join_shapefile)
    ##join_layer.crs = {'init' :coord_sys}
    
    ### open layer that the spaital join is targeting
    ##target_layer = gp.GeoDataFrame.from_file(target_shapefile)
    ##target_layer.crs = {'init' :coord_sys}
    
    # spatial join
    merged = gp.sjoin(target_shapefile, join_shapefile, how = "inner", op='intersects')
    
    merged = pd.DataFrame(merged)
    merged = merged[keep_columns]
    
    return merged

def create_point_from_table(current_df,x_coord,y_coord,coord_sys):
    current_df['geometry'] = current_df.apply(lambda x: Point((float(x[x_coord]), float(x[y_coord]))), axis=1)
    geo_layer = gp.GeoDataFrame(current_df, geometry='geometry')
    geo_layer.crs = {'init' :coord_sys}
    
    return geo_layer

df = get_permits_current_dec()
df_sub = df.loc[(df['CNTY'] == '33') | (df['JURIS'] == 'BOTHELL')]

point_shp = create_point_from_table(df_sub, 'X_COORD', 'Y_COORD', coord_sys)

# read in ARCH universe shapefile
universe = gp.read_file(r"J:\Projects\Permits\ShapeFiles\ARCH\ARCHSphereofInfluence.shp")

# spatial join; returns only those that intersect
join_result = gp_spatial_join(point_shp, universe, coord_sys, keep_cols)

# export to excel
join_result.sort_values(['JURIS', 'ISSUED'], inplace = True)
join_result.to_excel(os.path.join(outdir, "ARCH_PMT17.xlsx"), index = None)
