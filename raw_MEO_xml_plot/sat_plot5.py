from datetime import date, datetime, timedelta, time
import jday
from skyfield import sgp4lib
import scipy
from numpy import array, dot
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, MinuteLocator, drange
import sqlite3
import sys
import xlrd
import os
import re
import itertools
import urllib
import csv



def find_packets(sql_file, beaconid = '%', start_date = 0, end_date = None, MEOLUT = '%',ant = '%', sat = '%'):
    conn = sqlite3.connect(sql_file)
    c = conn.cursor()
    if MEOLUT <> '%': MEO = MEOdict[MEOLUT]
    else: MEO = '%'
    query = ['%'+beaconid+'%', MEO, start_date, end_date, ant, sat]
    c.execute('select * from packets where BcnID15 like ? and MEOLUT like ? and time > ? and time < ? and Ant like ? and Sat like?', query)
    packets = c.fetchall()
    return packets
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
def norm(j):
    num = 0
    for ind, i in enumerate(j):
        num = num + i**2
    return num ** (0.5)
def plot_sat(Xi,sat,start_time,stop_time,delta,MEOLUT,freq0):
    satellite = TLE_read(sat) #,'sarsat3.txt') - use optional argument to read different TLE
    curr = start_time
    timelist = list()
    posilist = list()
    velolist = list()
    Rig_list = list()
    Ri_list = list()
    f_ig_prime_list = list()
    f_i_prime_list = list()   
    f_inv_prime_list = list()
    f_inv_ig_list = list()
    f_ig_list = list()
    while curr < stop_time:
        curr += delta
        timelist.append(curr)     

    for times in timelist:
        position, velocity = satellite.propagate(times.year, times.month, times.day, times.hour, times.minute, times.second)
        V_i_TE = [x*86400 for x in velocity] # conversion because sgp4lib.TEME_to_ITRF function expects V in km/day 
        datetime1 = jday.JD(times)
        X_i_ECEF, V_i_ECEF = sgp4lib.TEME_to_ITRF(datetime1,array(position),array(V_i_TE))
        posilist.append(X_i_ECEF)
        V_i_ECEF = [x/86400 for x in V_i_ECEF] # convert back to #km/sec
        velolist.append(V_i_ECEF)
        Rig = (MEOLUTLocDict[MEOLUT] - X_i_ECEF)
        Rig_list.append(Rig)
        Rig_dot = dot(V_i_ECEF,(Rig/norm(Rig)))
        
        Ri = (Xi -X_i_ECEF)
        Ri_list.append(Ri)
        Ri_dot = dot(V_i_ECEF,(Ri/norm(Ri)))      
        inverted = True if str(sat)[0] == '3' else False
        freq_down = freq_sband if inverted == True else freq_lband
        
        ### working here
        dF_ig = (Rig_dot/c)*freq_down
        dF_i =  -(Ri_dot/c)*freq0 if inverted == True else (Ri_dot/c)*freq0

        f_ig_prime = freq0 + dF_i + dF_ig
        f_ig_prime_list.append(f_ig_prime)
        
        f_i_prime = freq0 + dF_ig # not inverted
        f_i_prime_list.append(f_i_prime)
        
        f_inv = freq_inv - (f_i_prime-freq_inv) + freq_shift
        f_inv_prime_list.append(f_inv)

        f_inv_ig = freq_inv - (f_ig_prime-freq_inv) +freq_shift
        f_inv_ig_list.append(f_inv_ig)

        f_ig = f_inv_ig if inverted == True else f_ig_prime
        f_ig_list.append(f_ig)

    alt = [norm(x) for x in posilist]    
    rangelist = [norm(MEOLUTLocDict[MEOLUT] - x) for x in posilist]
    
    #plotting TLE positional difference below
    #fig, ax = plt.subplots()

    #plt.plot(timelist, f_i_prime_list, 'g')
    #plt.plot(timelist, f_ig_prime_list, 'b-')
    #plt.plot(timelist, f_inv_prime_list,c='orange', linestyle = '-', linewidth = 3)
    plt.plot(timelist, f_ig_list, c = 'purple', linewidth = 3)
    plt.axhline(y=freq0, color = 'g')
    plt.legend(['f_ig'])
    #plt.axhspan(406.04e6, 406.05e6)
    plt.axhline(y=freq_inv, color = 'r', linestyle = '--')
    plt.grid(True)
    #plt.axis([start_time,stop_time,406.05e6,406.07e6])
    #plt.show()
    #ax.plot_date(timelist, rangelist, '-')
    #font = {'family' : 'normal',
    #        'weight' : 'bold',
    #        'size'   : 22}
    #matplotlib.rc('font', **font)

    # format the ticks
    #ax.xaxis.set_major_locator(HourLocator(range(int(Duration_hours)),int(Duration_hours)//int(numtimelabels)))
    #ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M:%S'))
    #ax.autoscale_view()
    #ax.grid(True)
    #ax.set_title( Satellite +' TLE compare')
    #ax.set_xlabel('Date/Time')
    #ax.set_ylabel('Position delta (km), max = ' + '{0:.2f}'.format(max(pos_diff_list2)) + '(km) at ' + datetimeofmaxstr)

def plot_packets(packets, MEOLUT, ant,start_time,end_time, packets_found, percent_packets):
    global ax1
    frequencylist = list()
    timelist = list()
    velolist = list() 
    for packet in packets:
        #print packet
        frequencylist.append(packet[7])
        timelist.append(datetime.strptime(packet[6],timepacket_format))
    #alt = [np.linalg.norm(x) for x in posilist]    
    #rangelist = [np.linalg.norm(MEOLUTLocDict[MEOLUT] - x) for x in posilist]
    #plotting TLE positional difference below
    #fig, ax = plt.subplots()
    #ax.plot_date(timelist, frequencylist, '-')
    #font = {'family' : 'normal',
            #'weight' : 'bold',
            #'size'   : 22}
    #matplotlib.rc('font', **font)
    #print frequencylist
    plt.figure(MEOLUT, figsize=(40,20))
    if ant == 1:
        ax1 = plt.subplot(6,1, ant)
    else:
        plt.subplot(6,1,ant, sharex = ax1, sharey = ax1)
    
    plt.plot(timelist, frequencylist,'ro')
    plt.title('{} - antenna {} ---- {} packets = {:.1f}%'.format(MEOLUT,ant,packets_found,percent_packets))
    plt.grid(True)
    plt.gca().xaxis.set_major_locator(Hours)
    plt.gca().xaxis.set_major_formatter(plot_fmt)
    plt.gca().xaxis.set_minor_locator(FiveMinutes)
    plt.gca().set_xlim(start_time,end_time)
    #if ant == 6:
    #    print 'ant == 6'
    #    plt.gca().set_xticklabels([])
    #    plt.gca().xaxis.set_major_locator(Hours)
    #plt.gcf().autofmt_xdate()

#configdict=dict(reader)
def read_config_file(configfile,row_start,row_end,column_key):
    configdict = {}
    wb = xlrd.open_workbook(configfile)
    sh = wb.sheet_by_index(0)
    for i in range(row_start-1,row_end-1): # Only looking for items in rows 2 - 21 right now - column B and C
        try: 
            cell_value = sh.cell(i,column_key).value
            cell_key = sh.cell(i,column_key-1).value
            configdict[cell_key] = cell_value
        except Exception:
            break
    return configdict


#Dictionaries
MEOdict = {'Hawaii':3385,'Florida':3669,'Maryland':3677}

MEOLUTLocDict = {3385:array((-5504.1435716174506, -2223.6730840851474, 2325.6444552998738)), #21.524427, -158.001277
3669:array((961.37754005286098, -5673.898647480621, 2740.9219220176628)),
3677:array((1128.862026003177, -4833.3592570977518, 3992.286836649925))}
MEOList = [3669, 3385, 3677]
AntList = range(1,7)
MEOref = {3669:'ADDC002%', 3385:'AA5FC00%', 3677:'ADDC002%'}

#Date Formats
timepacket_format = '%Y-%m-%d %H:%M:%S.%f'
sec_f = '%S.%f'
plot_fmt = DateFormatter('%m-%d %H:%M')
Hours = MinuteLocator(interval = 30)
FiveMinutes = MinuteLocator(interval=5)


#anything under here is run only when file is run, and not when it is imported
if __name__ == '__main__':
###START OF SCRIPT          

    ###### END OF FUNCTIONS - Define formats and variables  

    #TLE.URL_read()



    #constants
    c = 2.99792458e5 # speed of light in vacuum [km/s]
    r_e = 6378.137 #WGS84 Re [km]
    r_p = 6356.7523 #WGS84 Rp [km]

    freq_sband = 2226.47234e6
    freq_lband = 1544.5e6


    #read config file from current directory 
    #os.chdir("C:/Users/Jesse/Documents/Programming")
    print '\nCurrent directory is - ' + os.getcwd()

    #Read config file before switching directories
    if len(sys.argv) > 1:
        configfile = sys.argv[1]
    else:
        configfile = 'sat_plot_config.xls'
    #reader = csv.reader(open(configfile,'r'))
    print 'Reading configuration:'
    print '   ' + os.getcwd() + '\\' + configfile

    configdict = read_config_file(configfile,2,20,2)

    #os.chdir("C:/Users/Jesse/Documents/Programming/xml_data")
    #print 'current directory is - ' + os.getcwd()

    sql_folder = str(configdict['SQL_folder']) if configdict['SQL_folder'] <> '' else os.getcwd()
    sql_filename = str(configdict['SQL_file']) if configdict['SQL_file'] <> '' else 'MEOLUT_packets.db'
    MEOLUT_in = str(configdict['MEOLUT'])
    MEOLUT_list = [x.strip() for x in MEOLUT_in.split(',')] 

    sql_file = '{}{}'.format(sql_folder,sql_filename)

    print '\nReading SQL DB:'
    print '   ' + sql_file

    start_time = datetime(*xlrd.xldate_as_tuple(configdict['start_time'],0))
    end_time = datetime(*xlrd.xldate_as_tuple(configdict['end_time'],0))
    plot_now = configdict['Plot_Now']
    plot_hours = configdict['plot_hours']
    beaconidstr = str(configdict['BeaconID'])
    auto_update = configdict['Auto_Update']
    sat = int(configdict['satellite']) if configdict['satellite'] <> '' else '%'
    ant = int(configdict['antenna']) if configdict['antenna'] <> '' else AntList
    plot_theory = configdict['plot_theory']
    freq0 = configdict['freq0']
    freq_inv = configdict['freq_inv']
    freq_shift = configdict['freq_shift']

    time_span = end_time - start_time
    num_bursts = time_span.total_seconds() / 50

    if plot_now: 
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours = plot_hours)
        time_span = end_time - start_time
        num_bursts = time_span.total_seconds() / 50

    ref_flag = False

    if beaconidstr == "Florida_Ref": 
        beaconidstr = "ADDC00"
        ref_flag = True
        num_bursts = num_bursts*3

    if beaconidstr == "Hawaii_Ref": 
        beaconidstr = "AA5"
        ref_flag = True
        num_bursts = num_bursts*3

    print '\nStart time - ' + str(start_time)
    print 'End time - ' + str(end_time)

    if ref_flag: 
        print '\nReference beacon analysis\n'
        print 'Number of expect bursts = {}\n'.format(num_bursts)
    else:
        print '\nAssumed one beacon ("{}") for expected bursts and percentages\n'.format(beaconidstr)
        print 'Number of expect bursts = {}\n'.format(num_bursts)


    D = timedelta(0,10)


    k = 1

    #Beacon = 'Florida'
    #beaconidstr = 'ADDC00'
    #beaconidstr = '9C08D28' #406.025
    #beaconidstr = 'D7AC417'
    #beaconidstr = MEOref[MEOdict[Beacon]]
    #start_time = '2016-01-07 17:06'
    #end_time = '2016-01-07 20:46'
    #MEOLUTsearch = 'Florida'
    #ant = '%'

    #freq_down = freq_sband if str(sat)[0] == '3' else freq_lband

    #plot_theory = True
    #freq0 = 406.065e6
    #freq_inv = 406.05e6
    #freq_shift = 0.030e6 #--- works for 0.065 ref beacon


    for MEO in MEOLUT_list:
        Xi = MEOLUTLocDict[MEOdict[MEO]]
        for ant_i in ant:
        
            outpackets = find_packets(sql_file, beaconidstr, start_time,end_time, MEO, ant_i, sat)
            if plot_theory: plot_sat(Xi,sat,start_time,end_time,D,MEOdict[MEO],freq0)
            packets_found = len(outpackets)
            percent_packets = (packets_found/num_bursts)*100
            if ref_flag: 
                print ' {} - antenna {} ->  {} packets found -- {:.1f}% '.format(MEO,ant_i,packets_found, percent_packets)
            else:
                print ' {} - antenna {} ->  {} packets found -- {:.1f}% '.format(MEO,ant_i,packets_found, percent_packets)
            plot_packets(outpackets, MEO, ant_i,start_time,end_time, packets_found, percent_packets)
    plt.show()
