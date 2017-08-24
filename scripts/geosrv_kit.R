# This script formats assessor tables main and siteaddr. Will export dbfs to be joined to parcel(polygons) and siteaddr shapefiles
# for geocoding services. Requires 'dbfs' directory

library(foreign)
library(dplyr)
library(stringr)

rootDir <- 'J:/Projects/Geocoding'
dir <- '17GEOCODING'
county <- 'Setup/1Raw/Kitsap'
path <- file.path(rootDir, dir, county)

main <- file.path(path, 'main', 'main.dbf')
siteaddr <- file.path(path, 'siteaddr/export/parcel', 'siteaddr.dbf')
# building <- file.path(path, 'building', 'building.dbf')
# flatats <- file.path(path, 'flatats', 'flatats.dbf') 

# read dbfs
mdf <- read.dbf(main)
sadf <- read.dbf(siteaddr)
# bldg <- read.dbf(building)
# fdf <- read.dbf(flatats)

# reformat ACCT_NO as PIN
mdf$PIN <- gsub("-", "", mdf$ACCT_NO)

# export dbfs
mdf.export <- mdf %>% select(RP_ACCT_ID, PIN)
write.dbf(mdf.export, file.path(path, "dbfs/pin_parcels.dbf"))

sadf.export <- sadf %>% left_join(mdf, by = "LD_ACCT_ID") %>% select(LD_ACCT_ID, PIN)
write.dbf(sadf.export, file.path(path, "dbfs/pin_siteaddr.dbf"))

