"""
Creator: Conner Carnahan
Company: GeoOptics
Script Name: netCDF4Utils.py
Creation Date: 12/17/2019
Last Updated: 12/17/2019 by Conner Carnahan
Description: Various scripts for dealing with netCDF4 files to make them more usable in python environments
Dependencies: python, os, netCDF4, numpy, pandas, sys, matplotlib.pyplot
Disclaimer: THIS CODE IS PROVIDED AS IS WITH NO GUARENTEES OF STABLE USAGE.
"""

import os
import netCDF4 as net
import numpy as np
import pandas as pd
import sys
import matplotlib.pyplot as plt
np.set_printoptions(threshold=sys.maxsize)

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
            print(directoryName + "/" + filename)
            pandadata = pandadata.append(getVariables(net.Dataset(directoryName + "/" + filename), pandadata, variables),
                                         ignore_index = True)
    
    pandadata.to_csv(path_or_buf=outputFileName, sep = '|')
    
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
                temparray[temparray=='--'] = np.nan
                tempData[s] = [temparray]
        except KeyError:
            print("Something went wrong (a dataset is either corrupted or didn't process right) \n skipping this dataset")
            return
    return tempData
    
def ReadMergedCSV(fname, datframe):
    """ ReadMergedCSV(string fname, pandas dataframe datframe):
        This will read the csv file created by mergeNetCDF4Directory and overwrite datframe with the values
        Returns: datframe
        Notes: 
        It is a little computationally expensive, since it has to parse a bunch of strings to floats for every occultation
        and perhaps there is a way around this but currently I am not optimizing, just getting things to work
        
        This 100% should not be considered stable for anything other than the files generated by mergeNetCDF4Directory
        
        If we add new variables we want to consider this might also need to be tweeked based on their value types, ect.
    """
    mergeData = pd.read_csv(fname,sep='|')
    mergeData = mergeData.loc[:, ~mergeData.columns.str.contains('^Unnamed')]
    for s in mergeData.columns:
        print("Converting Columns: " + s)
        if s != 'occ_id' and isinstance(mergeData[s][0], str):
            for i in np.arange(len(mergeData.index)):
                temp = np.array(mergeData[s][i].replace('\n','')[1:-1].split(' '))
                temp = temp[temp != '']
                temp = temp.astype(np.float)
                mergeData[s][i]=temp
    datframe = mergeData
    return mergeData

def plotslopeoflnrefrac(datframe):
    """ plotslopeoflnrefrac(pandas dataframe):
        The refractivity as a function of geopotential is approximately e^(at), so this approximates a for each occultation and then
        plots it vs latitude and longitude
    """

    dlnft = np.zeros(len(datframe.index))
    lat = datframe.lat[:]
    lon = datframe.lon[:]
    for i in np.arange(len(datframe.index)):
        dlnft[i] = np.average(dlnf(datframe.refrac[i],datframe.geop_refrac[i]))
    
    fig = plt.figure(figsize=(12,10))
    a = plt.axes()
    a.plot(lat,dlnft,'b.')
    plt.xlabel("latitude")
    plt.ylabel("average change in ln(refrac)")
    plt.show()
    
    fig = plt.figure(figsize=(12,10))
    a = plt.axes()
    plt.xlabel("longitude")
    plt.ylabel("average change in ln(refrac)")
    a.plot(lon,dlnft,'b.')
    plt.show()

def da(a):
    """ da(numpy array of floats a)
        This returns an array that is the change in an array a
    """
    dat = np.zeros(len(a)-1)
    for i in np.arange(len(a)-1):
        dat[i] = a[i+1]-a[i]
    return dat

def dlnf(f,t):
    """ dlnf(numpy array f, numpy array t):
        This returns an array that is a first order approximation of the derivative of logarithm of f which is a function of t
    """
    df = da(f)
    dt = da(t)
    return np.divide(df,np.multiply(dt,f[:-1]))-np.divide(np.multiply(df,df),2*np.multiply(dt,np.multiply(f[:-1],f[:-1])))

def plotbindataaverage(datframe, xname, yname, minx, maxx, binsize):
    """ plotbindataverage(datframe pandas dataframe, xname string, yname string, minx float, maxx float, binsize = float):
        This plots the average values of binned data, minx should be < maxx, binsize should be positive
    """
    xbins = np.linspace(minx,maxx,num = (int)((maxx-minx)/binsize))
    ybins = np.zeros(len(xbins))
    ybins[0] = np.average(datframe[yname][datframe[xname] < xbins[1]])
    for i in np.arange(len(xbins)-2):
        ybins[i+1] = np.average(datframe[yname][(datframe[xname] < xbins[i+2]) & (datframe[xname] > i)])
    ybins[len(ybins)-1] = np.average(datframe[yname][datframe[xname] > xbins[len(ybins)-2]])
    
    fig = plt.figure(figsize=(12,10))
    a = plt.axes()
    a.plot(xbins,ybins,'b.-')
    plt.xlabel(xname)
    plt.ylabel(yname)
    plt.legend()
    plt.show()

def appenddlnvar(datframe, varname, tname):
    """ appenddlnvar(datframe pandas dataframe, varname string, tname):
        appends the estimated change in the natural logarithm of a variable (varname) (which should be an array) with respect to tname (should be an array of
        the same length of varname's array)
        returns a pandas dataframe but also updates the datframe anyway
    """
    dln = np.zeros(len(datframe.index))
    for i in np.arange(len(datframe.index)):
        dln[i] = np.average(dlnf(datframe[varname][i],datframe[tname][i]))
    return datframe.insert(len(datframe.columns),'dln' + varname, dln)