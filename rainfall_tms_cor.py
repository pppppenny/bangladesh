## rainfall data in Bangladesh 

# imports
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import statistics
from scipy.stats import linregress
from matplotlib.backends.backend_pdf import PdfPages
import glob
import os
import shutil
from datetime import datetime



##merging and clean the rainfall data to get coord and right time
def merging_rainfall_withCoord():
    rainfall_coord_solo = pd.read_csv('/Users/biar/Desktop/rainfallsta_coordinates.csv')

    rainfall_daata = pd.read_csv('/Users/biar/Desktop/BMD_monthly_rainfall_all_stations_07Aug24.csv')

    rainfall_daata['Station'] = rainfall_daata['Station'].str.strip()
    rainfall_coord_solo['Station'] = rainfall_coord_solo['Station'].str.strip()


    rainfall_withCoord = pd.merge(rainfall_daata, rainfall_coord_solo, 
                                on='Station', how='left')

    rainfall_withCoord.to_csv('/Users/biar/Desktop/rainfalldata_withCoord.csv')

    rainfall_withCoord = pd.read_csv('/Users/biar/Desktop/rainfalldata_withCoord.csv')

    right_time_rainfall = rainfall_withCoord[(rainfall_withCoord['Year']>=1985) & (rainfall_withCoord['Year']<= 2018)]
    right_time_rainfall.to_csv('/Users/biar/Desktop/rfdata_rightime_withCoord.csv')


def checking_dl():
    sa_dl = pd.read_csv('/Users/biar/Desktop/All_Dager_Level_sent_by_Sazzad.csv')
    bwdb_dl = pd.read_csv('/Users/biar/Desktop/bwdb_dl_changed_columname.csv')

    all = pd.merge(sa_dl, bwdb_dl, on='STATION_ID', how='left')

    mismatched = all[all['Danger_Level_mPWD'] != all['Danger_Level_meters']]
    mismatched.to_csv('/Users/biar/Desktop/mismatched_dl.csv')


### getting the daily stations wanted 
def matching_daily_wanted():

    folder_path_monthly = '/Users/biar/Desktop/cleaned_BWDB_tidal_data_1985_2018'             ### change the path name when needed 
    csv_files_monthly= glob.glob(f'{folder_path_monthly}/*.csv')
    monthly_list = []

    folder_path_daily= '/Users/biar/Desktop/BWDB_daily_tidal_data'
    csv_files_daily= glob.glob(f'{folder_path_daily}/*.csv')
    daily_list = []

    print(f"Found {len(csv_files_monthly)} CSV files to process")

    ## Part 1 of writting selected data files into a new folder  
    stations_passed = []

    destination_folder = '/Users/biar/Desktop/cleaned_daily_BWDB_tidal_data_1985_2018'           ### change the output folder name when needed 
    os.makedirs(destination_folder, exist_ok=True)


    for monthly_file_path in csv_files_monthly:
        monthly_file_name = os.path.basename(monthly_file_path)
        monthly_file_name = os.path.splitext(monthly_file_name)[0]
        monthly_station_name = monthly_file_name.split('_monthly')[0]

        monthly_list.append(monthly_station_name)
    
    print(len(monthly_list))


    for daily_file_path in csv_files_daily:
        daily_file_name = os.path.basename(daily_file_path)
        daily_file_name = os.path.splitext(daily_file_name)[0]
        daily_station_name = daily_file_name.split('_tidal')[0]

        daily_list.append(daily_station_name)
    

        if daily_station_name in monthly_list:       ### change the location when needed 
                
            stations_passed.append(daily_file_path)

    print(len(stations_passed))
    ## Part 2 of writting selected data files into a new folder 
    for stations_path in stations_passed:
        if os.path.isfile(stations_path):  
            shutil.copy(stations_path, destination_folder)
        else:
            print(f"File not found: {stations_path}")



def merge_surface_water_data(folder_path_tidal, folder_path_nontidal,output_file):

    # Get all CSV files in the folder
    csv_files_tidal = glob.glob(f'{folder_path_tidal}/*.csv')
    print(f"Found {len(csv_files_tidal)} tidal CSV files to process")
    csv_files_nontidal = glob.glob(f'{folder_path_nontidal}/*.csv')
    print(f"Found {len(csv_files_nontidal)} nontidal CSV files to process")
    
    csv_files = csv_files_tidal+csv_files_nontidal
    print(f"Total files to process: {len(csv_files)}")

    date_range = pd.date_range(start='1985-01-01', end='2018-12-31', freq='D')
    
    # Initialize the master dataframe with date components
    master_df = pd.DataFrame({
        'Date': date_range,
        'Year': date_range.year,
        'Month': date_range.month,
        'Day': date_range.day
    })
    
    all_stations_data = {}
    
    # Process each CSV file
    for file_path in csv_files:
            # Extract station name from filename
            file_name = os.path.basename(file_path)
            station_name = file_name.split('_')[0]  
            
            print(f"Processing {station_name}...")
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            df = df[(df['Date'] >= '1985-01-01') & (df['Date'] <= '2018-12-31')]
            
            water_level_col = None
            if 'SWLmpwd' in df.columns:
                water_level_col = 'SWLmpwd'
            if 'SWLmin' in df.columns:
                water_level_col = 'SWLmin'
 
            
            # Keep only Date and water level columns
            station_data = df[['Date',water_level_col]].copy()
            station_data = station_data.rename(columns={water_level_col: station_name})
            
            # Store in dictionary
            all_stations_data[station_name] = station_data
            
       
    # Merge all station data with master dataframe
    print("Merging all station data...")


    for station_name, station_data in all_stations_data.items():
        station_data['Date'] = pd.to_datetime(station_data['Date'])
        station_data = station_data.drop_duplicates(subset='Date', keep='first')

        master_df = master_df.merge(station_data, on='Date', how='left')
        print(f"Added {station_name} - Data points: {station_data[station_name].notna().sum()}")
    
    # Reorder columns to match your desired format: Date, Year, Month, Day, SW1, SW2, etc.
    station_columns = [col for col in master_df.columns if col.startswith('SW')]
    station_columns.sort()  # Sort station names
    
    final_columns = ['Date', 'Year', 'Month', 'Day'] + station_columns
    master_df = master_df[final_columns]

    master_df = master_df.drop_duplicates(subset='Date', keep='first')

    
    # Save to CSV
    master_df.to_csv(output_file, index=False)
    
    # Print summary statistics
    print(f"Output saved to: {output_file}")
    print(f"Time range: {master_df['Date'].min()} to {master_df['Date'].max()}")
    print(f"Total rows: {len(master_df)}")
    print(f"Total stations: {len(station_columns)}")
    
    return master_df

    #if __name__ == "__main__":
            # Set your folder path and output file
           # folder_path_tidal = '/Users/biar/Desktop/data_and_results/daily/cleaned_daily_BWDB_tidal_data_1985_2018'  # Change this to your actual folder path
           # folder_path_nontidal = '/Users/biar/Desktop/data_and_results/daily/cleaned_daily_BWDB_nontidal_data_1985_2018'  # Change this to your actual folder path
           # output_file = '/Users/biar/Desktop/merged_low_tide_surface_water_data.csv'  # Change this to your desired output path
            
            # Merge the data
           # merged_data = merge_surface_water_data(folder_path_tidal, folder_path_nontidal,output_file)


def adding_coordinates():
    # Load your station metadata file
    results_df = pd.read_csv('/Users/biar/Desktop/all_station_summary_result.csv')

    meta_data = pd.read_csv('/Users/biar/Desktop/BWDB_SWL_station_info.csv')  
    # assuming it has columns: StationID, Latitude, Longitude, RiverName, etc.

    # Merge with results_df
    results_with_meta = results_df.merge(meta_data[['StationID','Latitude','Longitude']],
                                        on='StationID', how='left')

    results_df = pd.DataFrame(results_with_meta)
    results_csv_path = '/Users/biar/Desktop/all_station_summary_result_with_coordinates.csv'      # change when needed 
    results_df.to_csv(results_csv_path, index=False)



