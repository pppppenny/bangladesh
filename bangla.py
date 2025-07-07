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



# the time series plot function
def tmplt (stationdata,station_name,ax):
    dt_used = stationdata[['Year','Month','Day','DecYear','SWLavg']].copy()
    dt_used['DateTMS'] = pd.to_datetime(dt_used[['Year', 'Month','Day']])     #get the timeseries object 

    dt_used.index = dt_used['Year']

    dt_cleaned = dt_used.dropna() # for the regression to run smoothly 
    if len(dt_cleaned) < 2:
        ax.text(0.5, 0.5, f'Insufficient data for {station_name}', 
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f'{station_name} - Insufficient Data')
        return
    

    ## the filtering part 

    slope, intercept, r_value, p_value, std_err = linregress(dt_cleaned['DecYear'], dt_cleaned['SWLavg'])
    dt_used.plot(x='DecYear',y='SWLavg',  ax=ax,label='Average surface water level')
    sns.regplot(x='DecYear', y='SWLavg', data=dt_cleaned, ax=ax,ci=None, color='orange',label=f'Linear trend with a slope of {slope:.4f}', scatter=False)

    ax.set_title(f'{station_name} Water Level Monthly Trend (1985-2018)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Water Level (meters)')

    mean_level = dt_cleaned['SWLavg'].mean()
    ax.axhline(mean_level, color='black', linestyle='--', label=f'Mean Water Level: {mean_level:.2f}')

    ax.legend()
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






# getting all the station data 
folder_path = '/Users/biar/Desktop/BWDB_nontidal_data_1985_2018'             ### change the path name when needed 
csv_files = glob.glob(f'{folder_path}/*.csv')


print(f"Found {len(csv_files)} CSV files to process")



## setting output path
output_path='/Users/biar/Desktop/color_filtered_tmp_for_nontidal.pdf'                         ### change the output path when needed 



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


                #the filtering part and making the filtered plots grey

                if fails_quality_check(df, axes[i]):

                    
                    df.plot(x='DecYear',y='SWLavg',  ax=axes[i],label='Average surface water level', color = 'grey')
                    axes[i].set_xlabel('Year')
                    axes[i].set_ylabel('Water Level (meters)')
                    axes[i].grid(True)

                    continue

                
                #Actual plotting 
                tmplt(df, station_name, axes[i])



            else:
                axes[i].set_visible(False)  

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
print(f"PDF saved to: {os.path.abspath(output_path)}")

