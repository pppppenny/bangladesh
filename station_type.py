import pandas as pd

# load your new results file
new_results = pd.read_csv('/Users/biar/Desktop/data_and_results/daily/version3/all_station_high_summary_result.csv')  ### change when needed

# load your previous results / station info file that has the station type
previous_results = pd.read_csv('/Users/biar/Desktop/data_and_results/merged_stainfo_DL.csv')  ### change when needed

# merge on StationID to bring in StationType
new_results = new_results.merge(
    previous_results[['StationID', 'StationType']],  ### adjust column names to match your file
    on='StationID',
    how='left'
)

# save
new_results.to_csv('/Users/biar/Desktop/stationType.csv', index=False)  ### change when needed
