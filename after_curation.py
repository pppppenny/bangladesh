## Analysis of surface water data in Bangladesh (cleaned data)

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
from bangla import tmplt, complete_date_range





# getting all the station data  (input path)
folder_path = '/Users/biar/Desktop/cleaned_BWDB_tidal_data_1985_2018'             ### change the path name when needed 
csv_files = glob.glob(f'{folder_path}/*.csv')

#getting the danger level water data
DL_data = pd.read_csv('/Users/biar/Desktop/SWL_DL_extracted_from_interpolated.csv')


print(f"Found {len(csv_files)} CSV files to process")



## setting output path
output_path='/Users/biar/Desktop/cleaned_tidal_plots.pdf'                         ### change the output path when needed 






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


                #making the df the complete df with range 1985-2018 
                df = complete_date_range(df)  

                tmplt(df, station_name, axes[i],DL_data)
                   



            else:
                axes[i].set_visible(False)  

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
print(f"PDF saved to: {os.path.abspath(output_path)}")

