import TLE_v2a as TLE
from datetime import date, datetime, timedelta, time
import jday
from skyfield import sgp4lib
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, MinuteLocator, drange
import sqlite3
import sys
import xlrd
import os
import re
import zipfile
from lxml import etree
import time

def file_search_regex(filetypesearch):
    if filetypesearch == "packet" or "TOA_FOA_DATA":
        my_regex = r"(.*)"+ re.escape("USSHARE") + r"(.*)"
    else:
        my_regex = r"(.*)"+ re.escape("USMCC") + r"(.*)"
    return my_regex

# Return list of files of in zip file matching searchstring
def find_file_inzip(zipfilename,searchstring):
    with zipfile.ZipFile(zipfilename, 'r') as myzip:
        ziplist = myzip.namelist()
        matches = [string for string in ziplist if re.match(searchstring, string)]
        return matches

def plot_sat(Xi,sat,start_time,stop_time,delta,MEOLUT,freq0):
    satellite = TLE.TLE_read(sat) #,'sarsat3.txt') - use optional argument to read different TLE
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
        X_i_ECEF, V_i_ECEF = sgp4lib.TEME_to_ITRF(datetime1,np.array(position),np.array(V_i_TE))
        posilist.append(X_i_ECEF)
        V_i_ECEF = [x/86400 for x in V_i_ECEF] # convert back to #km/sec
        velolist.append(V_i_ECEF)
        Rig = (MEOLUTLocDict[MEOLUT] - X_i_ECEF)
        Rig_list.append(Rig)
        Rig_dot = np.dot(V_i_ECEF,(Rig/np.linalg.norm(Rig)))
        
        Ri = (Xi -X_i_ECEF)
        Ri_list.append(Ri)
        Ri_dot = np.dot(V_i_ECEF,(Ri/np.linalg.norm(Ri)))      
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

    alt = [np.linalg.norm(x) for x in posilist]    
    rangelist = [np.linalg.norm(MEOLUTLocDict[MEOLUT] - x) for x in posilist]
    
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

def search_zip_output(MEOLUT, zip,zipmatches,filetypesearch,searchtag = None,searchstr = None):
    with zipfile.ZipFile(zip, 'r') as myzip:
        for files in zipmatches:
            file = myzip.open(files)
            filename = str(file)   
            packets = xml_process(file,filetypesearch, searchtag,searchstr)
            if packets: 
                write_to_sqldb(packets,filetypesearch, MEOLUT,files)

def xml_process(filename, filetype, searchtag = False, searchstr = False):
    ET = etree.parse(filename)
    e = ET.getroot()
    if searchstr: # could use this statement with the default bcnID = False to process all or using search string
        packets = find_str_in_tag(ET, searchtag, searchstr)
        print packets
    else:
        packets = e.findall(".//{}".format(filetype))
        #packets = e.findall(".//[contains(antennaId=,'1')])#*".format(filetype))
        #print str(len(packets))
    #print str(len(packets)) + ' packets returned from xml_process with filetype ' + filetype
    #if packets: print 'Found packets. First packet in list is element? ' + str(etree.iselement(packets[0]))
    return packets

def write_to_sqldb(packets,filetype,MEOLUT, filename):
    for packet in packets:
        burstlist.append([MF.text for MF in packet])

def find_packets(sql_file, beaconid = '%', start_date = 0, end_date = None, MEOLUT = '%',ant = '%', sat = '%'):
    conn = sqlite3.connect(sql_file)
    c = conn.cursor()
    if MEOLUT <> '%': MEO = MEOdict[MEOLUT]
    else: MEO = '%'
    query = ['%'+beaconid+'%', MEO, start_date, end_date, ant, sat]
    c.execute('select * from packets where BcnID15 like ? and MEOLUT like ? and time > ? and time < ? and Ant like ? and Sat like?', query)
    packets = c.fetchall()
    return packets

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

def make_plot_packets(packets):
    frequencylist = list()
    timelist = list()
    for packet in packets:
        #print packet
        frequencylist.append(packet[7])
        timelist.append(datetime.strptime(packet[6],timepacket_format))
    return timelist, frequencylist   

def plot_packets(timelist, frequencylist, MEOLUT, ant,start_time,end_time, packets_found, percent_packets):
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
    #plt.ion()
    fig = plt.figure(MEOLUT, figsize=(40,20))
    ax = fig.add_subplot(6,1, ant)
    plt.plot(timelist, frequencylist,'ro')
    #plt.title(MEOLUT + ' - antenna ' + str(ant) + ', ' + str(packets_found) + ' packets = ' + {}'.format(percent_packets))
    plt.title('{} - antenna {} ---- {} packets = {:.1f}%'.format(MEOLUT,ant,packets_found,percent_packets))
    plt.grid(True)
    plt.gca().xaxis.set_major_locator(Hours)
    plt.gca().xaxis.set_major_formatter(plot_fmt)
    plt.gca().xaxis.set_minor_locator(FiveMinutes)
    plt.gca().set_xlim(start_time,end_time)
      
    #for MEO in MEOLUT_list:
    #    fig = plt.figure(MEO, figsize=(40,20))
    #    for ant in ant_list:
    #        ax = fig.add_subplot(len(ant_list),1,ant)
    #    fig.show()
    #    fig.suptitle(MEO)
    #    fig.canvas.draw()
        #fig, axes = plt.subplots(nrows=len(ant))
    #fig, axes = plt.subplots(fig= MEO, nrows=len(ant))

    plt.show(block = False)

    # We need to draw the canvas before we start animating...
    #plt.gcf().autofmt_xdate()

#Dictionaries
MEOdict = {'Hawaii':3385,'Florida':3669,'Maryland':3677}

MEOLUTLocDict = {3385:np.array((-5504.1435716174506, -2223.6730840851474, 2325.6444552998738)), #21.524427, -158.001277
3669:np.array((961.37754005286098, -5673.898647480621, 2740.9219220176628)),
3677:np.array((1128.862026003177, -4833.3592570977518, 3992.286836649925))}
MEOList = [3669, 3385, 3677]
AntList = range(1,7)    
MEOref = {3669:'ADDC002%', 3385:'AA5FC00%', 3677:'ADDC002%'}

#Date Formats
timepacket_format = '%Y-%m-%d %H:%M:%S.%f'
sec_f = '%S.%f'
plot_fmt = DateFormatter('%m-%d %H:%M')
Hours = MinuteLocator(interval = 30)
FiveMinutes = MinuteLocator(interval=5)

filetypesearch = "TOA_FOA_DATA"

print '\nCurrent directory is - ' + os.getcwd()

#Read config file before switching directories
if len(sys.argv) > 1:
    configfile = sys.argv[1]
else:
    configfile = 'sat_plot_config.xls'

print 'Reading configuration:'
print '   ' + os.getcwd() + '\\' + configfile

configdict = read_config_file(configfile,42,56,2)

#get config - for folders, if blank will use current directory
zip_folder = str(configdict['zip_folder']) if configdict['zip_folder'] <> '' else os.getcwd()
sql_folder = str(configdict['SQL_folder']) if configdict['SQL_folder'] <> '' else os.getcwd()
sql_filename = str(configdict['SQL_file']) if configdict['SQL_file'] <> '' else 'MEOLUT_packets.db'
MEOLUT_in = str(configdict['MEOLUT'])
MEOLUT_list = [x.strip() for x in MEOLUT_in.split(',')] 
beaconidstr = str(configdict['BeaconID'])
sat = int(configdict['satellite']) if configdict['satellite'] <> '' else '%'
if configdict['antenna'] <> '': 
    ant_list = [int(x) for x in str(int(configdict['antenna']))]
else:
    ant_list = AntList

print ' ant list'
print ant_list

plot_theory = configdict['plot_theory']
freq0 = configdict['freq0']
freq_inv = configdict['freq_inv']
freq_shift = configdict['freq_shift']

sql_file = '{}{}'.format(sql_folder,sql_filename)

print '\nWriting packets to and reading from SQL DB:'
print '   ' + sql_file

plot_hours = configdict['plot_hours']
update_rate = configdict['update_rate']


#end_time = datetime.utcnow()
end_time = datetime(2016,6,1)

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


timelist = []
frequencylist = []

while True:
    #end_time = datetime.utcnow()
    end_time = datetime(2016,6,1)
    start_time = end_time - timedelta(hours = plot_hours)
    daynow = end_time.date()

    print end_time
    burstlist = list()
    for MEO_i, MEO in enumerate(MEOLUT_list):
        yMEO = []
        xMEO = []
        zipf = zip_folder + '\\' + MEO + '_' + str(daynow) + '.zip'
        my_regex = file_search_regex(filetypesearch)
        zipmatches = find_file_inzip(zipf, my_regex)
    ### PICKUP HERE 06-04 - need to search zip files and output to sql... search_zip_output function from xml_process
        burstlist = list()
        search_zip_output(MEO, zipf, zipmatches, filetypesearch)
        conn = sqlite3.connect(sql_file)
        c = conn.cursor()
        c.execute('''CREATE TABLE if not exists packets (Burst_ID Integer PRIMARY KEY, 
        Sat INT, MEOLUT INT, Ant INT, BcnID15 TEXT, BcnID30 TEXT, Time DATETIME2, Freq REAL, 
        Unknown1 INT, Unknown2 INT, CN0 REAL, BitRate REAL, Unknown3 INT, UNIQUE(MEOLUT, Ant, Time))''')
        for row in burstlist:
            row[5] = datetime.strptime(row[5],'%y %j %H%M %S.%f')
        c.executemany('INSERT OR IGNORE INTO packets(Sat, MEOLUT, Ant, BcnID15, BcnID30, Time, Freq, Unknown1, Unknown2, CN0, BitRate, Unknown3) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', burstlist)
        conn.commit()
        conn.close()
        Xi = MEOLUTLocDict[MEOdict[MEO]]
        for ant_i, ant in enumerate(ant_list):
            xAnt = []
            yAnt = []
            outpackets = find_packets(sql_file, beaconidstr, start_time,end_time, MEO, ant, sat)
            if plot_theory: plot_sat(Xi,sat,start_time,end_time,D,MEOdict[MEO],freq0)
            packets_found = len(outpackets)
            percent_packets = (packets_found/num_bursts)*100
            if ref_flag: 
                print ' {} - antenna {} ->  {} packets found -- {:.1f}% '.format(MEO,ant,packets_found, percent_packets)
            else:
                print ' {} - antenna {} ->  {} packets found -- {:.1f}% '.format(MEO,ant,packets_found, percent_packets) # same for now, may chanage later
            xAnt, yAnt = make_plot_packets(outpackets)
            xMEO.extend(xAnt)
            yMEO.extend(yAnt)
            plot_packets(timelist, frequencylist, MEO, ant,start_time,end_time, packets_found, percent_packets)
        timelist.append(xMEO)
        frequencylist.append(yMEO)

    nptimelist = np.array(timelist)
    npfrequencylist = np.array(frequencylist)

    #print nptimelist
    #print npfrequencylist
    #print nptimelist.shape
    #print npfrequencylist.shape


    #for MEO in MEOLUT_list:
    #    #fig = plt.figure(MEO, figsize=(40,20))
    #    #axes = plt.subplots(nrows = len(ant))
    #    fig, axes = plt.subplots(nrows=len(ant_list))
    #styles = ['r-']
    #print 'fig = '
    #print fig
    #print 'axes'
    #print axes
    #lines = [ax1.plot(x, y, style) for ax1, style in zip(axes, styles)]
    #fig.show()
    plt.show(block = False)
    time.sleep(update_rate) 
