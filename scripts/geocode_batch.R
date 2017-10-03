#written by: Weiran Zhao
#load up the ggmap library
library(ggmap)
library(dplyr)

#define a function that will process googles server responses for us.
getGeoDetails <- function(address){   
  
  #use the gecode function to query google servers
  geo_reply = geocode(address, output='all', messaging=TRUE, override_limit=TRUE)
  
  #now extract the bits that we need from the returned list
  answer <- data.frame(lat=NA, long=NA, accuracy=NA, formatted_address=NA, address_type=NA, status=NA)
  answer$status <- geo_reply$status
  
  #return Na's if we didn't get a match:
  if (geo_reply$status != "OK"){
    return(answer)
  }   
  
  #else, extract what we need from the Google server reply into a dataframe:
  answer$lat <- geo_reply$results[[1]]$geometry$location$lat
  answer$long <- geo_reply$results[[1]]$geometry$location$lng   
  
  if (length(geo_reply$results[[1]]$types) > 0){
    answer$accuracy <- geo_reply$results[[1]]$types[[1]]
  }
  answer$address_type <- paste(geo_reply$results[[1]]$types, collapse=',')
  answer$formatted_address <- geo_reply$results[[1]]$formatted_address
  
  return(answer)
}

dir <- "C:/Users/Clam/Desktop/inbox"
setwd(dir)

# Get all the .csv file
name.list <- list.files(pattern="*.csv")

# get the input data
for (file.name in name.list)
{
  data <- read.csv(file.name)
  data.add <- data %>%
    mutate(addresses=paste0(ADDRESS,", ",JURIS,", WA, ",ZIP,", US")) #%>%
    #select(-X) #must've been some column called 'X'
  
  addresses = data.add$addresses
  
  #initialise a dataframe to hold the results
  geocoded <- data.frame()
  
  # find out where to start in the address list (if the script was interrupted before):
  startindex <- 1
  
  # Start the geocoding process - address by address. geocode() function takes care of query speed limit.
  for (ii in seq(startindex, length(addresses))){
    
    print(paste("Working on index", ii, "of", length(addresses)))
    
    #query the google geocoder - this will pause here if we are over the limit.
    result = getGeoDetails(addresses[ii]) 
    print(result$status)     
    result$index <- ii
    
    #append the answer to the results file.
    geocoded <- rbind(geocoded, result)
  }
  
  #now we add the latitude and longitude to the main data
  data$lat <- geocoded$lat
  data$long <- geocoded$long
  data$accuracy <- geocoded$accuracy
  data$formatted_address <- geocoded$formatted_address
  
  #finally write it all to the output files
  write.table(data, file=paste0(gsub(".csv","",file.name),
                                "_geocoded.csv"), 
              sep=",", row.names=FALSE)
}







