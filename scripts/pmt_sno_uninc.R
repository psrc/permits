# This script reconciles raw Unincorporated Snohomish County 'issued' and 'finaled' permit records.
# user must define location and file name of input files and lookup table.

library(openxlsx)
library(data.table)
library(plyr)

in.dir <- "J:/Projects/Permits/16Permit/data/1raw/snohomish"
uninc.iss.file <- "uninc_issued16.xlsx"
Uninc.fin.file <- "uninc_finaled16.xlsx" 
lookup <- "J:/Projects/Permits/Admin/Lookup/template061_uninc.xlsx"

lookup.file <- read.xlsx(lookup, sheet = 1, startRow = 1, colNames = TRUE, rowNames = FALSE, cols = NULL)
lookup.filter <- subset(lookup.file, !is.na(raw))

iss.raw.file <- read.xlsx(file.path(in.dir, uninc.iss.file), sheet = 1, startRow = 1, colNames = TRUE, rowNames = FALSE, cols = NULL)
iss.raw.file$finaled <- NA
iss.raw.file$Issue.Date <- convertToDate(iss.raw.file$Issue.Date) 
iss.raw.file$Site.Unit.Type.Num <- paste(iss.raw.file$Site.Unit.Type, iss.raw.file$`Site.Unit#`, " ")

fin.raw.file <- read.xlsx(file.path(in.dir, Uninc.fin.file), sheet = 1, startRow = 1, colNames = TRUE, rowNames = FALSE, cols = NULL)
fin.raw.file$finaled <- fin.raw.file$Issue.Date
fin.raw.file$Issue.Date <- NA
fin.raw.file$finaled <- convertToDate(fin.raw.file$finaled)
fin.raw.file$Site.Unit.Type.Num <- paste(fin.raw.file$Site.Unit.Type, fin.raw.file$`Site.Unit#`, " ")

dt.iss.raw <- data.table(iss.raw.file)
dt.iss.raw <- dt.iss.raw[,lookup.filter$raw, with = FALSE]

dt.fin.raw <- data.table(fin.raw.file)
dt.fin.raw <- dt.fin.raw[,lookup.filter$raw, with = FALSE]

# based on lookup table, match raw table columns to template names accordingly
setnames(dt.iss.raw, as.character(lookup.filter$raw), as.character(lookup.filter$master))
setnames(dt.fin.raw, as.character(lookup.filter$raw), as.character(lookup.filter$master))

# join dt.fin.raw with dt.iss.raw, find what matches...
setkey(dt.iss.raw, PERMITNO)
setkey(dt.fin.raw, PERMITNO)

match.result <- dt.fin.raw[dt.iss.raw, nomatch = 0] #706 records returned (fin)
match.result <- match.result[, c(1:19), with = F] #iss and fin match

# ...to find what doesn't
unique.fin <- dt.fin.raw[!match.result] #989 records returned that are unique (fin)

# find matching and unique records in dt.iss.raw, update 'finaled' column
match.result2 <- dt.iss.raw[dt.fin.raw, nomatch = 0] #706 records returned (iss)
unique.iss <- dt.iss.raw[!match.result2] #1115 records returned that are unique (iss)
match.result2$FINALED <- match.result2$i.FINALED #update w/finaled dates
match.result2 <- match.result2[, c(1:19), with = F] # (iss)

# piece together a table with unique permitno
l <- list(match.result2, unique.iss, unique.fin)
combine.tables <- do.call("rbind.fill", l)

template <- as.data.frame(setNames(replicate(33, numeric(0), simplify = F), lookup.file$master))
l2 <- list(combine.tables, template)
t <- do.call("rbind.fill", l2)
setcolorder(t, colnames(template))

# clean up fields
t <- data.frame(lapply(t, function(x) {
  if (is.character(x)) return(toupper(x))
  else return(x)
}))

t$PIN <- gsub("-", "", t$PIN)
t$SORT <- t$PERMITNO
t$STATUS <- ifelse(!is.na(t$FINALED), "FINALED", "ISSUED")
search.words <- c("SINGLE FAMILY|SFR|DUPLEX|TOWNHOMES|MOBILE|ADU|ACCESSORY*DWELLING|CARETAKER|TOWNHOUSE")
wrd.match <- grep(search.words, t$NOTES3)

write.xlsx(t, file.path(in.dir, paste0("t61UNINCORPORATEDSNOHOMISH.xlsx")), colNames = TRUE)
