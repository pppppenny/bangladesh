## Time series analysis for surface water data in Bangladesh 

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
import datetime
from statsmodels.tsa.seasonal import STL
import shutil



# the time series plot function
def tmplt (stationdata,station_name,ax,danger_level_data):
    dt_used = stationdata.copy()

    matching_station = danger_level_data[danger_level_data['StationID'] == station_name]     # check the matching stations 

    #cleaning NaN only for regression 
    dt_cleaned = dt_used.dropna() # for the regression to run smoothly 

    ## plotting the time series lines and regression part 


    # stl decomposition
    dt_for_stl = dt_cleaned['SWLavg']
    stl = STL(dt_for_stl, seasonal = 13, period =12 , robust =True)
    stl_result= stl.fit()

    seas = stl_result.seasonal

    deseasonalised_swlavg = dt_cleaned['SWLavg']-seas

    #fit a linear trend to the deseasonalised data
    slope, intercept, r_value, p_value, std_err = linregress(dt_cleaned['DecYear'],deseasonalised_swlavg)

    dt_used.plot(x='DecYear',y='SWLavg',  ax=ax,label='Average surface water level')

    trend_line = slope*dt_used['DecYear'] +intercept
    ax.plot(dt_used['DecYear'], trend_line, color='orange', label=f'Linear trend (deseasonalised) slope: {slope:.2f}', linewidth=2)



    #the simple linear regression trend with no seasonal consideration
        #slope, intercept, r_value, p_value, std_err = linregress(dt_cleaned['DecYear'], dt_cleaned['SWLavg'])
        # sns.regplot(x='DecYear', y='SWLavg', data=dt_cleaned, ax=ax,ci=None, color='orange',label=f'Linear trend with a slope of {slope:.4f}', scatter=False)

    
    

    ## matching the danger level station id and station name 

    if matching_station.empty:
        print(f"[Warning] No matching station name for station id: {station_name}")
        ax.set_title(f'{station_name} Water Level Monthly Trend (1985-2018)')
        ax.text(1.02, 0.6, 'No Station Danger Level Record', transform=ax.transAxes, color='red', verticalalignment='top')

    else:
        actual_name = matching_station['StationNam'].iloc[0]
        river_name = matching_station['RiverName'].iloc[0]
        ax.set_title(f'{station_name}-{actual_name} (River: {river_name}) Water Level Monthly Trend (1985-2018)')


    ax.set_xlabel('Year')
    ax.set_ylabel('Water Level (meters)')
    ax.set_xlim(1984, 2020)

    #plotting the mean water level 
    mean_level = dt_cleaned['SWLavg'].mean()
    ax.axhline(mean_level, color='black', linestyle='--', label=f'Mean Water Level: {mean_level:.2f}')



    #plotting the danger level and calculating num of times exceeded 
    count = 0
    if not matching_station.empty:
        
        danger_level = matching_station['DLm'].iloc[0] 
        

        if pd.isna(danger_level):
            danger_level = matching_station['DLmInterp'].iloc[0]
            interpolated_note = '(Interpolated) '
        else: 
            interpolated_note = ''
        
        for watervalue in stationdata['SWLavg']:
            if watervalue >  danger_level:
                count += 1

        percentage = (count/(len(stationdata.dropna())))*100
        ax.text(1.02, 0.6,f'{interpolated_note}Danger Level Exceeded Times: {count} ({percentage:.2f}%)', transform=ax.transAxes, color='red', verticalalignment='top')
        ax.axhline(danger_level, color='red', linestyle='-', label=f'Danger Water Level: {danger_level:.2f}')





    # Calculating percentage of missing month 
    num_of_month_missing = dt_used['SWLavg'].isna().sum()
    percentage_missing_month = (num_of_month_missing/(12*34))*100
    ax.text(1.02, 0.5, f'The percentage of missing month is {percentage_missing_month:.2f}%.', transform=ax.transAxes, fontsize=10, va='top')



    # Legend position and showing the grid 
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True)


# applying the criterias (the filtering process)
def fails_quality_check(sdata,ax):


    # 1. less than 17/34 years
    years_with_data = sdata.loc[sdata['SWLavg'].notna(), 'DecYear'].unique()
    if len(years_with_data) < 204:
        print(f"Skipping {station_name}: Covering too few years")
        ax.set_title(f'{station_name} - Skipped: Less than 50% of data')
        return ax, True
    
    # 2. Long continuous gap (more than 5 years)
    sdata['HasData'] = sdata['SWLavg'].notna().astype(int)
    sdata['GapGroup'] = (sdata['HasData'].diff() != 0).cumsum()
    gap_lengths = sdata[sdata['HasData'] == 0].groupby('GapGroup').size()
    if (gap_lengths >= 60).any():
        print(f'Skipping {station_name}: Long continuous gap')
        ax.set_title(f'{station_name} - Skipped: Long continuous gap')
        return ax, True
    
    # 3. Multiple gaps with each more than 2 years
    if (gap_lengths >= 24).sum() > 1:
        print(f'Skipping {station_name}: Multiple long gaps')
        ax.set_title(f'{station_name} - Skipped: Multiple gaps')
        return ax, True

    # 4. Sudden changes          (need to be discussed)
    #sdata['Change'] = sdata['SWLavg'].diff().abs()
    #if (sdata['Change'] > 1.5).any():  # adjust threshold
    #    print(f'Skipping {station_name}: Abrupt changes')
    #    ax.set_title(f'{station_name} - Skipped: Abrupt changes')
    #    return ax, True

    return False



def complete_date_range(the_data):

 ## checking if the original data starts with 1985 and ends with 2018, and add the rows if not 

    the_data['DateTMS'] = pd.to_datetime(the_data[['Year', 'Month','Day']])     #get the timeseries object 
    # create a new dataframe with all months from 1985 to 2018
    full_range = pd.date_range(start='1985-01-31', end='2018-12-31', freq='ME')
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


    complete_df['DecYear'] = complete_df['DateTMS'].apply(lambda x: year_fraction(x.date()))
    

    # merge the two df and keep existing values
    if not the_data.empty:
        the_data = pd.merge(complete_df, the_data[['DateTMS', 'SWLavg','DecYear']], 
                          on='DateTMS', how='left', suffixes=('', '_existing'))
        
        # use existing values where available, otherwise keep NaN
        the_data['SWLavg'] = the_data['SWLavg_existing'].fillna(the_data['SWLavg'])
        the_data['DecYear'] = the_data['DecYear_existing'].fillna(the_data['DecYear'])
        the_data = the_data.drop(['SWLavg_existing','DecYear_existing'], axis=1)
   
    # sort by data and reset index
    the_data = the_data.sort_values('DateTMS').reset_index(drop=True)
    the_data.index = the_data['DateTMS']

    return the_data




if __name__ == "__main__":


    # getting all the station data 
    folder_path = '/Users/biar/Desktop/BWDB_nontidal_data_1985_2018'             ### change the path name when needed 
    csv_files = glob.glob(f'{folder_path}/*.csv')

    #getting the danger level water data
    danger_level_data = pd.read_csv('/Users/biar/Desktop/BWDB_river_danger_level_data.csv')


    print(f"Found {len(csv_files)} CSV files to process")



    ## setting output path
    output_path='/Users/biar/Desktop/color_deseasonal_filtered_tmp_WDangerLev_for_nontidal.pdf'                         ### change the output path when needed 





    ## Part 1 of writting selected data files into a new folder  
    stations_passed = []
    destination_folder = ''           ### change the output folder name when needed 
    tidal_manually_wanted = ['SW193','SW136.1', 'SW278', 'SW253', 'SW38.1', 'SW323', 'SW320', 'SW121', 'SW230.1', 'SW288.4', 'SW180']
    nontidal_manually_wanted = ['SW8', 'SW313', 'SW326', 'SW172.5', 'SW149.1', 'SW72B', 'SW233A', 'SW236', 'SW252.1', 'SW101.5', 'SW265', 'SW216A', 'SW344', 'SW227', 'SW233', 'SW311.4', 'SW131.5', 'SW150']


    ###the main loop
    # loop through all the stations 
    with PdfPages(output_path) as pdf:

        for j in range(0, len(csv_files), 4):
            fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(12, 18))

            for i in range(4):
                if j + i < len(csv_files):
                    file_path = csv_files[j + i]
                    file_name = os.path.basename(file_path)
                    file_name = os.path.splitext(file_name)[0]
                    station_name = file_name.split('_monthly')[0]

                    df = pd.read_csv(file_path)

                    if df.empty:
                        print(f"Skipping {station_name}: CSV file is empty")
                        axes[i].text(0.5, 0.5, f'No data available for {station_name}', ha='center', va='center', transform=axes[i].transAxes)
                        axes[i].set_title(f'{station_name} - No Data')

                        continue
                    


                    #making the df the complete df with range 1985-2018 
                    df = complete_date_range(df)  

                    

                    # the manual selection
                    if station_name in nontidal_manually_wanted:       ### change the location when needed 
                        tmplt(df, station_name, axes[i])
                        stations_passed.append(file_path)
                    else: 


                    #the filtering part and making the filtered plots grey
                        if fails_quality_check(df, axes[i]):

                            
                            df.plot(x='DecYear',y='SWLavg',  ax=axes[i],label='Average surface water level', color = 'grey')
                            axes[i].set_xlabel('Year')
                            axes[i].set_ylabel('Water Level (meters)')
                            axes[i].set_xlim(1984, 2020)
                            axes[i].text(1.02, 0.6, 'Failed Quality Check', transform=axes[i].transAxes, color='grey', fontsize=15)
                            axes[i].grid(True)
                        
                        else: 
                            #Actual plotting 
                            tmplt(df, station_name, axes[i])
                            stations_passed.append(file_path)



                else:
                    axes[i].set_visible(False)  

            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            
    print(f"PDF saved to: {os.path.abspath(output_path)}")


    ## Part 2 of writting selected data files into a new folder 
    for stations_path in stations_passed:
        if os.path.isfile(stations_path):  
            shutil.copy(stations_path, destination_folder)
        else:
            print(f"File not found: {stations_path}")

