# This script will read, disaggregate, and format raw Incorporated Snohomish County permit records.
# user must define location and file name of input data and lookup table.
# Test Mark Fork
library(openxlsx)
library(data.table)
library(plyr)

in.dir <- "J:/Projects/Permits/15Permit/data/1raw/snohomish"
sno.file <- "incorp_res_issued2015.xlsx" 
lookup <- "J:/Projects/Permits/Admin/Lookup/template061.xlsx"

lookup.file <- read.xlsx(lookup, sheet = 1, startRow = 1, colNames = TRUE, rowNames = FALSE, cols = NULL)
lookup.filter <- subset(lookup.file, !is.na(raw))

sno.raw.file <- read.xlsx(file.path(in.dir, sno.file), sheet = 1, startRow = 1, colNames = TRUE, rowNames = FALSE, cols = NULL)
sno.raw.file$Issue.Date <- convertToDate(sno.raw.file$Issue.Date) 

# identify issuing cities in snohomish file
cities <- unique(sno.raw.file$BP.City)

dt.raw <- data.table(sno.raw.file)
dt.raw <- dt.raw[,lookup.filter$raw, with = FALSE]

# based on lookup table, match raw table columns to template names accordingly
setnames(dt.raw, as.character(lookup.filter$raw), as.character(lookup.filter$master))

# filter by each unique issuing city, export to separate spreadsheet, and format to template 
for (c in cities){
  template <- NULL
  template <- as.data.frame(setNames(replicate(33, numeric(0), simplify = F), lookup.file$master))
  t <- NULL
  t <- dt.raw[NOTES2 == c,]
  l <- list(t, template)
  t2 <- do.call(rbind.fill, l)
  setcolorder(t2, colnames(template))
  write.xlsx(t2, file.path(in.dir, paste0("t61", toupper(c), ".xlsx")), colNames = TRUE)
}

