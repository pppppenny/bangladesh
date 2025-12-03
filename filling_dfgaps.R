install.packages('missForest')
library(missForest)
install.packages("doMC")
library(doMC)

# Set up parallel processing with doMC
cores <- parallel::detectCores() - 1  # leave 1 core free
registerDoMC(cores = cores)




df <- read.csv('/Users/biar/Desktop/merged_surface_water_data.csv')

df1 <- df[, c('Date', 'Year', 'Month', 'Day','DecimYear')]

data <- df[, !(names(df) %in% c('Date', 'Year', 'Month', 'Day','DecimYear'))]




set.seed(42)   

cat("Starting missForest imputation...\n")
start_time <- Sys.time()

result <- missForest(data, ntree = 30, parallelize = 'forests', maxiter = 3, verbose = TRUE)


end_time <- Sys.time()
cat("Imputation finished!\n")
cat("Elapsed time: ", end_time - start_time, "\n")



data_filled <- result$ximp

final_df <- cbind(df1, data_filled)


# Check imputation error estimates
print(result$OOBerror)


write.csv(final_df, '/Users/biar/Desktop/surface_water_data_filled.csv', row.names = FALSE)



