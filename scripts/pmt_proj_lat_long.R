library(rgdal)
library(sp)

dir <- "C:/Users/Clam/Desktop/inbox"
outdir <- "C:/Users/Clam/Desktop/google_geo_shp"
setwd(dir)

name.list <- list.files(pattern="*_geocoded.csv")

for (file.name in name.list){
  print(paste0("Reading ", file.name))
  split.name <- unlist(strsplit(file.name, "_"))
  df <- read.csv(file.name, header = TRUE, sep = ",")

  # Catch NAs
  df$long[is.na(df$long)] <- 0
  df$lat[is.na(df$lat)] <- 0
  
  # find coordinates from table
  coordinates(df) <- cbind(df[,"long"],df[,"lat"]) 
  
  # set to Lat/Long CoordinatesCRS
  proj4string(df) = CRS("+proj=longlat +datum=WGS84") 
  
  # set to WA State Plane North
  shp <- spTransform(df, ("+init=epsg:2285")) 
  
  # export to shapefile
  writeOGR(obj = shp, dsn = outdir, layer = split.name[[1]], driver = "ESRI Shapefile")
  print(paste0("Exported ", split.name[[1]]))
}
