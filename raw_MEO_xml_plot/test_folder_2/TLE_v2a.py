# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 21:22:28 2015

@author: Jesse
"""

import scipy
import numpy as np
import sys
import re
import datetime
import itertools 
from sgp4.earth_gravity import wgs72
from sgp4.io import twoline2rv
import urllib
import csv
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange

# norad(sat) returns norad ID for sat where sat is SARSAT ID ex S7 or 329 (MEO)
def norad(sat):
    data = []
    with open('sats.csv') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
             data.append(row)
    ind = [item for item in range(len(data)) if data[item][0] == str(sat)]
    try: norad = data[ind[0]][1] 
    except IndexError as e: 
        print "Satellite - " + sat + " not listed in 'sats.csv'" 
        return 0 
    return norad

def URL_read(source = 1):
    if source == "B":
        try:
            urllib.urlretrieve('http://simdat.eumetsat.int/metopTLEs/html/data_out/latest_m01_long_tle.txt','Metop-B.txt')
        except IOError:
            print 'Connection Error - url not retrieved'
    if source == "A":
        try:
            urllib.urlretrieve('http://simdat.eumetsat.int/metopTLEs/html/data_out/latest_m02_long_tle.txt','Metop-A.txt')
        except IOError:
            print 'Connection Error - url not retrieved'
    else:
        try: 
            urllib.urlretrieve('http://celestrak.com/NORAD/elements/sarsat.txt','sarsat.txt')
        except IOError:
            print 'connection problem'

def TLE_read(sat, TLEfile1in = False):
    norad_id = norad(sat) 
    if norad_id == 0: return 0
    if TLEfile1in:
        TLEfile1 = TLEfile1in
    else:
        TLEfile1 = "sarsat.txt"
    with open(TLEfile1) as TLE:
        for line in TLE:
            #print(sats)
            if norad_id in line[2:7]:           
                TLEout = []
                if int(line[0]) == 1:
                    TLEout1 = line[:]
                elif int(line[0]) == 2:
                    TLEout2 = line[:]
    if TLEout1 == None: return 0
    satellite = twoline2rv(TLEout1,TLEout2,wgs72)
    return satellite


# pass TLE to twoline2rv function

#position, velocity = satellite.propagate(2015, 11, 29, 12, 50, 18) # position 
#... (km), velocity (km/s)
#print(TLEout1, TLEout2)
#print('Errors = ' + str(satellite.error))    # nonzero on error
#print(satellite.error_message)
#print(position)
#print(velocity)
#position2, velocity2 = satellite.propagate(2015, 11, 29, 12, 50, 19)
#print position2
#print numpy.linalg.norm(position2) - 6378
#pos_comp2 = np.subtract(position,position2)
#print(pos_comp2)
#ps_comp = numpy.asarray(pos_comp2)
#print(ps_comp)
#mag = np.linalg.norm(pos_comp2)
#print(mag)

def LLHtoECEF(lat, lon, h):
    # see http://www.mathworks.de/help/toolbox/aeroblks/llatoecefposition.html
    a = np.float64(6378137.0)        # Radius of the Earth (in meters)
    f = np.float64(1.0/298.257223563)  # Flattening factor WGS84 Model
    b = a * (1 - f)
    e = np.sqrt((a**2 - b**2) / a**2)
    N = a / np.sqrt(1 - e**2 * (np.sin(np.radians(lat)))**2)
    x = (N + h) * np.cos(np.radians(lat))*np.cos(np.radians(lon))
    y = (N + h) * np.cos(np.radians(lat))*np.sin(np.radians(lon))
    z = ((b**2/a**2) * N + h) * np.sin(np.radians(lat))
    return (x, y, z)

def ECEFtoLLA(x,y,z):
    a = np.float64(6378137.0)        # Radius of the Earth (in meters)
    f = np.float64(1.0/298.257223563)  # Flattening factor WGS84 Model
    b = a * (1 - f)
    e = np.sqrt((a**2 - b**2) / a**2)
    e2 = np.sqrt((a**2 - b**2) / b**2)  
    p = np.sqrt(x**2 + y**2)
    theta = np.arctan((z*a)/(p*b))
    lon = np.degrees(np.arctan(y/x))
    lat = np.degrees(np.arctan((z+e2**2*b*(np.sin(theta))**3)/(
    p-e**2*a*(np.cos(theta))**3)))
    N = a / np.sqrt(1 - e**2 * (np.sin(np.radians(lat)))**2)     
    h = (p / np.cos(np.radians(lat))) - N   
    return (lat, lon, h)
    
def TLE_comp(TLE1, TLE2, timetocomp): # TLEs are satellite objects, timetocomp is datetime
    position1, velocity1 = TLE1.propagate(timetocomp.year, timetocomp.month, timetocomp.day, timetocomp.hour, timetocomp.minute, timetocomp.second)
    position2, velocity2 = TLE2.propagate(timetocomp.year, timetocomp.month, timetocomp.day, timetocomp.hour, timetocomp.minute, timetocomp.second)
    position_delta = np.subtract(position1,position2)
    #velocity_delta = np.subtract(velocity1,velocity2)
    return position_delta

## UNCOMMENT BELOW FOR NORMAL USAGE to update TLES!!

#URL_read()
#URL_read("A")
#URL_read("B")



