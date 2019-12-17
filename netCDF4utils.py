"""
Creator: Conner Carnahan
Company: GeoOptics
Script Name: netCDF4Utils.py
Creation Date: 12/17/2019
Last Updated: 12/17/2019 by Conner Carnahan
Description: Various scripts for dealing with netCDF4 files to make them more usable in python environments
Dependencies: python, os, netCDF4, numpy, pandas
Disclaimer: THIS CODE IS PROVIDED AS IS WITH NO GUARENTEES OF STABLE USAGE.
"""

import os
import netCDF4 as net
import numpy as np
import pandas as pd

DEFAULT_VARIABLES = ['occ_id','start_time','lat','lon','overall_qual','snr_L2p','bangle','impact','impact_opt','refrac',
                     'alt_refrac','geop_refrac','undulation','r_coc','roc']

def mergeNetCDF4Directory(directoryName, fileBeginning, outputFileName, separator = '|', variables = DEFAULT_VARIABLES):
    """ mergeNetCDF4Directory(string: directoryName, string: fileBeginning, string: outputFileName,
                              character: separator = '|', array of strings: variables = DEFAULT_VARIABLES):
        This function takes netCDF4 files in a directory with a certain fileBeginning and will merge them into a pandas dataframe
        this dataframe is then printed into a csv and will return the dataframe
        
        The reason for this function: 
        When using ropp to post process occultations it outputs a file that is unwieldy and terrible, additionally it will only be one
        occultation at a time.
        Pandas dataframes are much more user friendly and work with way more packages, so it is nicer to just have all the data in
        that form.
        Also, it is far more useful to have all of the occultations in one bin so they can be analyzed together.

        Things to note:
        Data should be indexed by occultation id by default 
        use something like this to select the row:
            df.loc[df['occ_id'] == id]
        Data is stored in an array of one array for each column (this is the easiest way to store data), 
        so to use the array in any meaningful way you should add a [0] at the end of when you access it.
    """

    pandadata = pd.DataFrame()
    
    for filename in os.listdir(directoryName) :
        if filename.startswith(fileBeginning) :
            getVariables(net.Dataset(directoryName + "/" + filename), pandadata, variables)
    
    pandadata.to_csv(path_or_buf=outputFileName, sep = separator)
    
    return pandadata

def getVariables(dat, datframe, variables):
    """ getVariables (netCDF4 Dataset: dat, Pandas DataFrame: datframe, array of strings: variables) :
        this is a helper function for mergeNetCDF4Directory
        it converts a single dataset into a pandas dataframe column
    """
    tempData = pd.DataFrame()
    for s in variables :
        try :
            if s == 'occ_id':
                w = ""
                for l in dat.variables[s][:][0]:
                    if l != '--':
                        w += (l.decode('utf-8'))
                tempData[s] = [w]
            else :
                temparray = np.array(dat.variables[s][:][0])
                #temparray[temparray=='--'] = np.nan
                tempData[s]= [temparray]
        except KeyError:
            print("Something went wrong (a dataset is either corrupted or didn't process right) \n skipping this dataset")
            return

    datframe = datframe.append(tempData, ignore_index = True)
    