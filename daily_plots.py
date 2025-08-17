
## for tidal data, it's SWLavg, for nontidal it's SWLmpwd


# imports
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statistics
from scipy.stats import linregress
from matplotlib.backends.backend_pdf import PdfPages
import glob
import os
import datetime
from statsmodels.tsa.seasonal import STL


the_result_table = [] 

# the time series plot function
def tmplt_daily (stationdata,station_name,ax,danger_level_data):

    percentage = np.nan
    percentage_missing_days = np.nan
    mean_level= np.nan
    slope = np.nan
    danger_level= np.nan
    num_of_days_missing= np.nan
    count= np.nan
    



    dt_used = stationdata.copy()

    matching_station = danger_level_data[danger_level_data['StationID'] == station_name]     # check the matching stations 

    #cleaning NaN only for regression 
    dt_cleaned = dt_used.dropna() # for the regression to run smoothly 

    ## plotting the time series lines and regression part 

    if len(dt_cleaned) == 0:
        print(f"No data for station {station_name}, skipping.")
        ax.text(0.5, 0.5, f'No data available for {station_name}', ha='center', va='center', transform=ax.transAxes)

        return {
        'StationID': station_name,
        'StartDate': stationdata['DateTMS'].iloc[0],
        'EndDate': stationdata['DateTMS'].iloc[-1],
        'MeanLevel': mean_level,
        'TrendSlope': slope,
        'DangerLevel': danger_level,
        'Total_Amount_of_Data': (len(dt_used['DecimYear'])), 
        'DL_Exceeded_Count':count,
        'DL_Exceeded_Percentage': percentage,
        'Missing_Days_Counts':num_of_days_missing,
        'Missing_Days_Percentage': percentage_missing_days
    }

    # stl decomposition
    dt_for_stl = dt_cleaned['SWLavg']
    stl = STL(dt_for_stl, seasonal = 13, period = 365 , robust =True)
    stl_result= stl.fit()

    seas = stl_result.seasonal

    deseasonalised_swlavg = dt_cleaned['SWLavg']-seas

    #fit a linear trend to the deseasonalised data
    slope, intercept, r_value, p_value, std_err = linregress(dt_cleaned['DecimYear'],deseasonalised_swlavg)

    dt_used.plot(x='DecimYear',y='SWLavg',  ax=ax,label='Average surface water level')

    trend_line = slope*dt_used['DecimYear'] +intercept
    ax.plot(dt_used['DecimYear'], trend_line, color='orange', label=f'Linear trend (deseasonalised) slope: {slope:.2f}', linewidth=2)



    #the simple linear regression trend with no seasonal consideration
        #slope, intercept, r_value, p_value, std_err = linregress(dt_cleaned['DecYear'], dt_cleaned['SWLavg'])
        # sns.regplot(x='DecYear', y='SWLavg', data=dt_cleaned, ax=ax,ci=None, color='orange',label=f'Linear trend with a slope of {slope:.4f}', scatter=False)

    
    

    ## matching the danger level station id and station name 
    danger_level = np.nan
    if matching_station.empty:
        print(f"[Warning] No matching station name for station id: {station_name}")
        ax.set_title(f'{station_name} Water Level Daily Trend (1985-2018)')
        ax.text(1.02, 0.6, 'No Station Danger Level Record', transform=ax.transAxes, color='red', verticalalignment='top')

    else:
        actual_name = matching_station['StationNam'].iloc[0]
        river_name = matching_station['RiverName'].iloc[0]
        ax.set_title(f'{station_name}-{actual_name} (River: {river_name}) Water Level Daily Trend (1985-2018)')


    ax.set_xlabel('Year')
    ax.set_ylabel('Water Level (meters)')
    ax.set_xlim(1984, 2020)

    #plotting the mean water level 
    mean_level = dt_cleaned['SWLavg'].mean()
    ax.axhline(mean_level, color='black', linestyle='--', label=f'Mean Water Level: {mean_level:.2f}')



    #plotting the danger level and calculating num of times exceeded 
    count = 0
    ninetyfive_percentile_station = ['SW113', 'SW67', 'SW332', 'SW293', 'SW331', 'SW327', 'SW57A', 'SW262', 'SW209A','SW222', 'SW272', 'SW270', 'SW271','SW182']
    if not matching_station.empty:
        
        danger_level = matching_station['DLm'].iloc[0] 
        

        if pd.isna(danger_level):
            if station_name in ninetyfive_percentile_station:
                danger_level = np.percentile((dt_cleaned['SWLavg']), 95)
                interpolated_note = '(95th Percentile) '
            else: 
                danger_level = matching_station['DLmInterp'].iloc[0]
                interpolated_note = '(Interpolated) '
        else: 
            interpolated_note = ''
        
        for watervalue in stationdata['SWLavg']:
            if watervalue >  danger_level:
                count += 1

        percentage = (count/(len(stationdata.dropna())))*100
        ax.text(1.02, 0.6,f'{interpolated_note}Danger Level Exceeded Times: {count} ({percentage:.2f}%)', transform=ax.transAxes, color='red', verticalalignment='top',fontsize=7)
        ax.axhline(danger_level, color='red', linestyle='-', label=f'Danger Water Level: {danger_level:.2f}')


    # missing days
    num_of_days_missing = dt_used['SWLavg'].isna().sum()
    percentage_missing_days= (num_of_days_missing/(len(dt_used['DecimYear'])))
    ax.text(1.02, 0.5, f'The percentage of missing days is {percentage_missing_days:.2f}%.', transform=ax.transAxes, fontsize=7, va='top')


    # Legend position and showing the grid 
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1),fontsize=7)
    ax.grid(True)

    return {
        'StationID': station_name,
        'StartDate': stationdata['DateTMS'].iloc[0],
        'EndDate': stationdata['DateTMS'].iloc[-1],
        'MeanLevel': mean_level,
        'TrendSlope': slope,
        'DangerLevel': danger_level,
        'Total_Amount_of_Data': (len(dt_used['DecimYear'])), 
        'DL_Exceeded_Count':count,
        'DL_Exceeded_Percentage': percentage,
        'Missing_Days_Counts':num_of_days_missing,
        'Missing_Days_Percentage': percentage_missing_days
    }




def complete_daily_date_range(the_data):

 ## checking if the original data starts with 1985 and ends with 2018, and add the rows if not 

    the_data['DateTMS'] = pd.to_datetime(the_data[['Year', 'Month','Day']])     #get the timeseries object 
    # create a new dataframe with all months from 1985 to 2018
    full_range = pd.date_range(start='1985-01-01', end='2018-12-31', freq='D')
    complete_df = pd.DataFrame({
        'DateTMS': full_range,
        'Year': full_range.year,
        'Month': full_range.month,
        'Day': full_range.day,
        'SWLavg': np.nan})


    def year_fraction(date):
        start = datetime.date(date.year, 1, 1).toordinal()
        year_length = datetime.date(date.year+1, 1, 1).toordinal() - start
        return date.year + float(date.toordinal() - start) / year_length


    complete_df['DecimYear'] = complete_df['DateTMS'].apply(lambda x: year_fraction(x.date()))
    

    # merge the two df and keep existing values
    if not the_data.empty:
        the_data = pd.merge(complete_df, the_data[['DateTMS', 'SWLavg','DecimYear']], 
                          on='DateTMS', how='left', suffixes=('', '_existing'))
        
        # use existing values where available, otherwise keep NaN
        the_data['SWLavg'] = the_data['SWLavg_existing'].fillna(the_data['SWLavg'])
        the_data['DecimYear'] = the_data['DecimYear'].fillna(the_data['DecimYear'])
        the_data = the_data.drop(['SWLavg_existing','DecimYear_existing'], axis=1)
   
    # sort by data and reset index
    the_data = the_data.sort_values('DateTMS').reset_index(drop=True)
    the_data.index = the_data['DateTMS']

    return the_data





# getting all the station data  (input path)
monthly_cleaned_folder = '/Users/biar/Desktop/cleaned_BWDB_tidal_data_1985_2018'             ### change the path name when needed 
monthly_cleaned_csv = glob.glob(f'{monthly_cleaned_folder}/*.csv')


monthly_station_names = [
    os.path.splitext(os.path.basename(f))[0].split('_monthly')[0]
    for f in monthly_cleaned_csv
]


daily_nontidal_folder = '/Users/biar/Desktop/BWDB_daily_tidal_data'             ### change when needed 
daily_nontidal_csv = glob.glob(f'{daily_nontidal_folder}/*.csv')

#getting the danger level water data
DL_data = pd.read_csv('/Users/biar/Desktop/SWL_DL_extracted_from_interpolated.csv')


print(f"Found {len(daily_nontidal_csv)} daily CSV files to process")
print(f"Found {len(monthly_cleaned_csv)} monthly CSV files for reference")



## setting output path
output_path='/Users/biar/Desktop/daily_tidal.pdf'                         ### change the output path when needed 






###the main loop
# loop through all the stations 
with PdfPages(output_path) as pdf:

    for j in range(0, len(daily_nontidal_csv), 4):
        fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(12, 18))

        for i in range(4):
            if j + i < len(daily_nontidal_csv):
                daily_file_path = daily_nontidal_csv[j + i]
               # monthly_file_path = monthly_cleaned_csv[j + i]

                daily_file_name = os.path.basename(daily_file_path)
                daily_file_name = os.path.splitext(daily_file_name)[0]
                daily_station_name = daily_file_name.split('_tidal')[0]     #####   change when needed 

                #monthly_file_name = os.path.basename(monthly_file_path)
               # monthly_file_name = os.path.splitext(monthly_file_name)[0]
             #   monthly_station_name = monthly_file_name.split('_monthly')[0]



                df = pd.read_csv(daily_file_path)


                #making the df the complete df with range 1985-2018 
                df = complete_daily_date_range(df)  


                result_of_station = tmplt_daily(df, daily_station_name, axes[i],DL_data)
                if daily_station_name not in monthly_station_names:
                    axes[i].text(1.02, 0.4, f'Discarded station for monthly data', transform=axes[i].transAxes, fontsize=7
                    , va='top', color='blue')

                the_result_table.append(result_of_station)



            else:
                axes[i].set_visible(False)  

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        print(f"Completed batch {j//4 + 1}")


results_df = pd.DataFrame(the_result_table)
results_csv_path = '/Users/biar/Desktop/daily_tidal_summary_result.csv'      # change when needed 
results_df.to_csv(results_csv_path, index=False)
print(f"Summary CSV saved to: {results_csv_path}")

print(f"PDF saved to: {os.path.abspath(output_path)}")

