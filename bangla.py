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
    dt_used = stationdata[['Year','Month','DecYear','SWLavg']]
    dt_used.index = dt_used['Year']
    dt_cleaned = dt_used.dropna()
    if len(dt_cleaned) < 2:
        ax.text(0.5, 0.5, f'Insufficient data for {station_name}', 
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f'{station_name} - Insufficient Data')
        return

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



# getting all the station data 
folder_path = '/Users/biar/Desktop/BWDB_nontidal_data_1985_2018'             ### change the path name when needed 
csv_files = glob.glob(f'{folder_path}/*.csv')


print(f"Found {len(csv_files)} CSV files to process")


## setting output path
output_path='/Users/biar/Desktop/tmp_for_nontidal.pdf'                         ### change the output path when needed 

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

                tmplt(df, station_name, axes[i])
            else:
                axes[i].set_visible(False)  

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
print(f"PDF saved to: {os.path.abspath(output_path)}")

