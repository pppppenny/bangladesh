
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
from datetime import datetime
import time
import pymannkendall as mk



the_result_table = [] 

# the time series plot function
def tmplt_daily (stationdata,station_name,ax,danger_level_data):

    percentage = np.nan

    mean_level= np.nan
    slope = np.nan
    danger_level= np.nan

    count= np.nan
    



    dt_used = stationdata.copy()

    matching_station = danger_level_data[danger_level_data['StationID'] == station_name]     # check the matching stations 

   

    ## plotting the time series lines and regression part 


    # stl decomposition
    #dt_for_stl = dt_used[station_name]
    #dt_for_stl_clean = dt_for_stl.dropna()

    #stl = STL(dt_for_stl_clean, seasonal = 13, period = 365 , robust =True)
    #stl_result= stl.fit()

    # seas = stl_result.seasonal

    #deseasonalised_swlavg = dt_used[station_name]-seas

    #fit a linear trend to the deseasonalised data
    #slope, intercept, r_value, p_value, std_err = linregress(dt_used['DecimYear'],deseasonalised_swlavg)

    #dt_used.plot(x='DecimYear',y=station_name,  ax=ax,label='Average surface water level')

    #trend_line = slope*dt_used['DecimYear'] +intercept
    #ax.plot(dt_used['DecimYear'], trend_line, color='orange', label=f'Linear trend (deseasonalised) slope: {slope:.5f}', linewidth=2)



    # Theil Sen 
    # seasonal mann-kendall test 
    y_dt_for_sen = dt_used[station_name]
    x_dt_for_sen = dt_used['DecimYear']

    results_mk_sens = mk.seasonal_test(y_dt_for_sen)
    slope =results_mk_sens.slope
    intercept = results_mk_sens.intercept
    p_value = results_mk_sens.p

    ax.plot(dt_used['DecimYear'], dt_used[station_name], color='steelblue', linewidth=1, label='Surface Water Level')

    #dt_used.plot(x='DecimYear',y=station_name,color='blue', ax=ax,label='Average surface water level')


    trend_line = intercept+ slope*x_dt_for_sen

    ax.plot(x_dt_for_sen, trend_line, color='darkorange',
            label=f"Theil Sen trend slope: {slope:.5f}",
            linewidth=2)


    if p_value >0.05 :
        ax.text(1.02, 0.4,f'As the p value is {p_value:.5f}, the trend is not statistically significant.', transform=ax.transAxes, color='red', verticalalignment='top',fontsize=7)
    else:
        ax.text(1.02, 0.4,f'As the p value is {p_value:.5f}, the trend is statistically significant.', transform=ax.transAxes, color='red', verticalalignment='top',fontsize=7)



    #the simple linear regression trend with no seasonal consideration
        #slope, intercept, r_value, p_value, std_err = linregress(dt_cleaned['DecYear'], dt_cleaned['SWLavg'])
        # sns.regplot(x='DecYear', y='SWLavg', data=dt_cleaned, ax=ax,ci=None, color='orange',label=f'Linear trend with a slope of {slope:.4f}', scatter=False)

    
    

    ## matching the danger level station id and station name 
    danger_level = np.nan
    #if matching_station.empty:
        #print(f"[Warning] No matching station name for station id: {station_name}")
        #ax.set_title(f'{station_name} Water Level Daily Trend (1985-2018)')
        #ax.text(1.02, 0.6, 'No Station Danger Level Record', transform=ax.transAxes, color='red', verticalalignment='top')

    #else:

    actual_name = matching_station['StationNam'].iloc[0]
    river_name = matching_station['RiverName'].iloc[0]
    ax.set_title(f'{station_name}-{actual_name} (River: {river_name}) Water Level Daily Trend (1985-2018)')


    ax.set_xlabel('Year')
    ax.set_ylabel('Water Level (meters)')
    ax.set_xlim(1984, 2020)

    #plotting the mean water level 
    mean_level = dt_used[station_name].mean()
    ax.axhline(mean_level, color='black', linestyle='--', label=f'Mean Water Level: {mean_level:.3f}')



    #plotting the danger level and calculating num of times exceeded 
    count = 0
    ninetyfive_percentile_station = ['SW113', 'SW67', 'SW332', 'SW293', 'SW331', 'SW327', 'SW57A', 'SW262', 
                                     'SW209A','SW222', 'SW272', 'SW270', 'SW271','SW182','SW250','SW176','SW107',
                                     'SW128','SW73','SW280','SW158','SW181','SW233','SW114','SW264A','SW157',
                                     'SW335','SW311.4','SW97']
    
    dl_95th = np.percentile(dt_used[station_name].dropna(), 95)
    BWDB_danger_level = matching_station['DLm'].iloc[0] if not matching_station.empty else np.nan
    dl_interp = matching_station['DLmInterp'].iloc[0] if not matching_station.empty else np.nan


    if station_name in ninetyfive_percentile_station:
                danger_level = dl_95th
                interpolated_note = '(95th Percentile) '
    else: 
        if  pd.isna(BWDB_danger_level):
            danger_level = dl_interp
            interpolated_note = '(Interpolated) '
        else: 
            danger_level = BWDB_danger_level
            interpolated_note = '(BWDB) '
        
    for watervalue in dt_used[station_name]:
        if watervalue >  danger_level:
            count += 1

    percentage = (count/(12418))*100
    ax.text(1.02, 0.6,f'{interpolated_note}Danger Level Exceeded Times: {count} ({percentage:.3f}%)', transform=ax.transAxes, color='red', verticalalignment='top',fontsize=7)
    ax.axhline(BWDB_danger_level, color='firebrick', linestyle='-', label=f'BWDB Danger Water Level: {BWDB_danger_level:.3f}')
    ax.axhline(dl_interp, color='lightpink', linestyle='-', label=f'Interpolated Danger Water Level: {dl_interp:.3f}')
    ax.axhline(dl_95th, color='mediumorchid', linestyle='-', label=f'95th Percentile Danger Water Level: {dl_95th:.3f}')



    # Per year num of days exceeds DL
    df_exceed = dt_used[['Date', station_name]].copy()
    df_exceed['Year'] = pd.to_datetime(df_exceed['Date']).dt.year
    df_exceed['Exceed'] = df_exceed[station_name] > danger_level

    exceed_per_year = df_exceed.groupby('Year')['Exceed'].sum().to_dict()  



    # Legend position and showing the grid 
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1),fontsize=7)
    ax.grid(True)

    return {
        'StationID': station_name,
        'StartDate': stationdata['Date'].iloc[0],
        'EndDate': stationdata['Date'].iloc[-1],
        'MeanLevel': mean_level,
        'TrendSlope': slope,
        'DangerLevel_adopted':danger_level,
        'DWDB_DangerLevel': BWDB_danger_level,
        '95th_DL':dl_95th,
        'Interpolated_DL':dl_interp, 
        'Total_Amount_of_Data': (len(dt_used['DecimYear'])), 
        'DL_Exceeded_Count':count,
        'DL_Exceeded_Percentage': percentage,
        'DL_Exceeded_Per_Year': exceed_per_year
    }





# getting all the station data  (input path)
file_csv_path = '/Users/biar/Desktop/low_tide_filtered.csv'    ###change when needed 
print(f"Loading merged CSV: {file_csv_path}")

df_all_stations = pd.read_csv(file_csv_path)

#getting the danger level water data
DL_data = pd.read_csv('/Users/biar/Desktop/SWL_DL_extracted_from_interpolated.csv')




#getting all the stations name columns 
station_columns = [col for col in df_all_stations.columns 
                  if col.startswith('SW') and col not in ['Date', 'Year', 'Month', 'Day', 'DecimYear']]

print(f"Found {len(station_columns)} stations to process")
print("Station names:", station_columns[:10], "..." if len(station_columns) > 10 else "")


## setting output path
output_path='/Users/biar/Desktop/all_station_lowtide_plots.pdf'                         ### change the output path when needed 






###the main loop
# loop through all the stations 

start_time = datetime.now()
print(f"Loop started at: {start_time}")


with PdfPages(output_path) as pdf:

    for j in range(0, len(station_columns), 4):
        fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(12, 18))

        for i in range(4):
            if j + i < len(station_columns):
                station_name = station_columns[j + i]
              
                # Create a subset of data for this station (with all necessary columns)
                station_data = df_all_stations[['Date', 'Year', 'Month', 'Day', 'DecimYear', station_name]].copy()



                result_of_station = tmplt_daily(station_data, station_name, axes[i],DL_data)

                the_result_table.append(result_of_station)



            else:
                axes[i].set_visible(False)  

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        print(f"Completed batch {j//4 + 1}")


results_df = pd.DataFrame(the_result_table)

exceed_per_year_df = pd.json_normalize(results_df['DL_Exceeded_Per_Year'])
exceed_per_year_df['StationID'] = results_df['StationID']

summary_df_final = pd.concat([results_df.drop(columns=['DL_Exceeded_Per_Year']), exceed_per_year_df], axis=1)




results_csv_path = '/Users/biar/Desktop/all_station_lowtide_summary_result.csv'      # change when needed 
summary_df_final.to_csv(results_csv_path, index=False)
print(f"Summary CSV saved to: {results_csv_path}")

print(f"PDF saved to: {os.path.abspath(output_path)}")

end_time = datetime.now()
print(f"Loop ended at: {end_time}")
print(f"Total runtime: {end_time - start_time}")

