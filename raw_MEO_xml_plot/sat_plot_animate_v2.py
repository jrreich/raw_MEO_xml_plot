# Uncomment the next two lines if you want to save the animation
#import matplotlib
#matplotlib.use("Agg")
from lxml import etree 
import numpy as np
from matplotlib.pylab import *
from mpl_toolkits.axes_grid1 import host_subplot
import matplotlib.animation as animation
from matplotlib.dates import MinuteLocator, DateFormatter
from datetime import datetime, timedelta
import sqlite3
import os, re
import xlrd
import zipfile

xlimit = 5.0
timepacket_format = '%Y-%m-%d %H:%M:%S.%f'


if len(sys.argv) > 1:
    configfile = sys.argv[1]
else:
    configfile = 'sat_plot_config.xls'
#reader = csv.reader(open(configfile,'r'))
print 'Reading configuration:'
print '   ' + os.getcwd() + '\\' + configfile

def read_config_file():
    configdict = {}
    wb = xlrd.open_workbook(configfile)
    sh = wb.sheet_by_index(0)
    for i in range(41,57): # Only looking for items in rows 42 - 58 right now - column B and C
        try: 
            cell_value = sh.cell(i,2).value
            cell_key = sh.cell(i,1).value
            configdict[cell_key] = cell_value
        except Exception:
            break
    return configdict

configdict = read_config_file()

zip_folder = str(configdict['zip_folder']) if configdict['zip_folder'] <> '' else os.getcwd()
sql_folder = str(configdict['SQL_folder']) if configdict['SQL_folder'] <> '' else os.getcwd()
sql_file = str(configdict['SQL_file']) if configdict['SQL_file'] <> '' else 'MEOLUT_packets.db'
plot_minutes = configdict['plot_minutes']
update_rate = configdict['update_rate']
time_pad = configdict['time_pad']
beaconsearchstr = str(configdict['BeaconID'])


x = datetime.utcnow() # uncomment for real time 
#x = datetime(2016, 6, 27, 16,5)

time_del = timedelta(seconds = update_rate) # amount of data to grab each run through
timemax = timedelta(minutes = plot_minutes) # time span shown on plots
timepad = timedelta(minutes = time_pad) # time padding the right on plots

t=zeros(0)
# Sent for figure
font = {'size'   : 9}
matplotlib.rc('font', **font)
FiveMinutes = MinuteLocator(interval=5)
pltFmt = DateFormatter("%Y-%m-%d %H:%M")


# Setup figure and subplots
f0 = figure(num = 0, figsize = (12, 8))#, dpi = 100)
f0.suptitle("MEOLUT Raw Data", fontsize=18)





# Data Placeholders
FL1=zeros(0)
FL2=zeros(0)
FL3=zeros(0)
FL4=zeros(0)
FL5=zeros(0)
FL6=zeros(0)

HI1=zeros(0)
HI2=zeros(0)
HI3=zeros(0)
HI4=zeros(0)
HI5=zeros(0)
HI6=zeros(0)

## FL setup

axFL = list()
plotFL = []
axFL = [subplot2grid((6,2), (i,0)) for i in range(6)]

for i in range(6):
    axFL[i].set_ylim(406.0e6, 406.1e6)
    axFL[i].set_xlim(x - time_del,x - time_del + timemax)
    axFL[i].grid(True)
    axFL[i].xaxis.set_major_formatter(pltFmt)
    plotFL.append(axFL[i].plot(t,FL3, 'ro', label = "FL-Ant {}".format(i+1)))
    axFL[i].legend([plotFL[i][0]],[plotFL[i][0].get_label()], loc = "upper left",
        shadow=True, fancybox=True)

axFL[0].set_title('FL', fontsize = 16)



## HI setup

axHI = list()
plotHI = []
axHI = [subplot2grid((6,2), (i,1)) for i in range(6)]

for i in range(6):
    axHI[i].set_ylim(406.0e6, 406.1e6)
    axHI[i].set_xlim(x - time_del,x - time_del + timemax)
    axHI[i].grid(True)
    axHI[i].xaxis.set_major_formatter(pltFmt)
    plotHI.append(axHI[i].plot(t,HI3, 'ro', label = "HI-Ant {}".format(i+1)))
    axHI[i].legend([plotHI[i][0]],[plotHI[i][0].get_label()], loc = "upper left",
        shadow=True, fancybox=True)

axHI[0].set_title('HI', fontsize = 16)

### SQL Update Functions
def make_zip_search_str(MEOLUT, date):
    #generate zipfile name to search
    zipf = MEOLUT + '_' + str(date.year) + '-' + '{:02d}'.format(date.month) + '-' + '{:02d}'.format(date.day) + '.zip'
    return zipf
def find_file_inzip(zipfilename,searchstring):
    with zipfile.ZipFile(zipfilename, 'r') as myzip:
        ziplist = myzip.namelist()
        matches = [string for string in ziplist if re.match(searchstring, string)]
        print 'returning ' + str(len(matches)) + ' files in zip ' + zipfilename
        return matches
def find_packets(sql_file, start_date = 0, end_date = None, MEOLUT = '%',ant = '%', beaconid = '%', sat = '%'):
    conn = sqlite3.connect(sql_file)
    c = conn.cursor()
    query = ['%'+beaconid+'%', MEOLUT, start_date, end_date, ant, sat]
    c.execute('select * from packets where BcnID15 like ? and MEOLUT like ? and time > ? and time < ? and Ant like ? and Sat like?', query)
    packets = c.fetchall()
    return packets
def search_zip_output(MEOLUT, zip,zipmatches,filetype, searchtag = None,searchstr = None, writeto = 'both'):
    with zipfile.ZipFile(zip, 'r') as myzip:
        for files in zipmatches:
            file = myzip.open(files)
            filename = str(file)              
            packets = xml_process(file,filetype, searchtag,searchstr)
            #print len(packets)
            if packets: write_to_sqldb(packets,filetype, MEOLUT,files)

def write_to_sqldb(packets,filetype,MEOLUT, filename):
    if (filetype == "packet" or filetype == "TOA_FOA_DATA"):
        for packet in packets:
            burstlist.append([MF.text for MF in packet])

def xml_process(filename, filetype, searchtag = False, searchstr = False):
    e = etree.parse(filename).getroot()
    packets = e.findall(".//{}".format(filetype))
    #packets = e.findall(".//[contains(antennaId=,'1')])#*".format(filetype))
    #print str(len(packets))
    #print str(len(packets)) + ' packets returned from xml_process with filetype ' + filetype
    #if packets: print 'Found packets. First packet in list is element? ' + str(etree.iselement(packets[0]))
    return packets

### SQL Pull functions
def plot_packets(packets): #, MEOLUT, ant,start_time,end_time, packets_found, percent_packets):
    frequencylist = list()
    timelist = list()
    for packet in packets:
        frequencylist.append(packet[7])
        timelist.append(datetime.strptime(packet[6],timepacket_format))
    return timelist, frequencylist


outpackFL = [],[],[],[],[],[]
FL = [],[],[],[],[],[]
FLtimenew = [],[],[],[],[],[]
FLfreqnew = [],[],[],[],[],[]
tarrayFL = [],[],[],[],[],[]

outpackHI = [],[],[],[],[],[]
HI = [],[],[],[],[],[]
HItimenew = [],[],[],[],[],[]
HIfreqnew = [],[],[],[],[],[]
tarrayHI = [],[],[],[],[],[]

burstlist = []

MEOLUT_list = ['Hawaii', 'Florida']
filetype = 'TOA_FOA_DATA'
os.chdir(zip_folder)
sql_file = sql_folder + sql_file
start_time = x - time_del
end_time = x

def updateData(self):
    global x
    global tarrayFL
    global tarrayHI
    global sql_file
    global burstlist
    global start_time
    global end_time
    
    ### SQLDB updating
    print '\nreading zips from {}\n'.format(zip_folder)    
    for MEO in MEOLUT_list:
        zipf = make_zip_search_str(MEO,x)
        my_regex = r"(.*)"+ re.escape("USSHARE") + r"(.*)"
        zipmatches = find_file_inzip(zipf, my_regex)
        burstlist = list()
        #Main function to search zip files and output to csv or sql
        search_zip_output(MEO, zipf, zipmatches, filetype)
        conn = sqlite3.connect(sql_file)
        c = conn.cursor()
        c.execute('''CREATE TABLE if not exists packets (Burst_ID Integer PRIMARY KEY, 
Sat INT, MEOLUT INT, Ant INT, BcnID15 TEXT, BcnID30 TEXT, Time DATETIME2, Freq REAL, 
Unknown1 INT, Unknown2 INT, CN0 REAL, BitRate REAL, Unknown3 INT, UNIQUE(MEOLUT, Ant, Time))''')
        for row in burstlist:
            dt = datetime.strptime(row[5],'%y %j %H%M %S.%f')  ### this doesn't work if the seconds are exactly .000000 it truncates
            row[5] = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        c.executemany('INSERT OR IGNORE INTO packets(Sat, MEOLUT, Ant, BcnID15, BcnID30, Time, Freq, Unknown1, Unknown2, CN0, BitRate, Unknown3) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', burstlist)
        conn.commit()
        conn.close()




### END OF SQL DB UPDATING

    #end_time = x + time_del
    
    
    #sql_file = r"C:\Users\Jesse\Documents\Programming\test_folder\sql_db\MEOLUT_Raw_test1.db"
    print 'plotting from {} to {}'.format(start_time, end_time)
    for i in range(6):
        outpackFL[i][:] = find_packets(sql_file, start_time, end_time, 3669, i+1, beaconsearchstr)
        #print outpackFL[i]
        FLtimenew[i][:], FLfreqnew[i][:] = plot_packets(outpackFL[i][:])
        print '  new bursts on FL - ant {} = {}'.format(i+1,len(FLtimenew[i]))
        FL[i][:] = append(FL[i][:],FLfreqnew[i])
        tarrayFL[i][:] = append(tarrayFL[i][:],FLtimenew[i])

    for i in range(6):
        outpackHI[i][:] = find_packets(sql_file, start_time, end_time, 3385, i+1, beaconsearchstr)
        HItimenew[i][:], HIfreqnew[i][:] = plot_packets(outpackHI[i][:])
        print '  new bursts on HI - ant {} = {}'.format(i+1,len(HItimenew[i]))
        HI[i][:] = append(HI[i][:],HIfreqnew[i])
        tarrayHI[i][:] = append(tarrayHI[i][:],HItimenew[i])
    
    if len(FLtimenew[5]) == 0:
        tarrayFL[5][:] = append(tarrayFL[5][:],end_time)
        FL[5][:] = append(FL[5][:], [0])  
    for i in range(6):
        plotFL[i][0].set_data(tarrayFL[i],FL[i])
    
    if len(HItimenew[5]) == 0:
        tarrayHI[5][:] = append(tarrayHI[5][:],end_time)
        HI[5][:] = append(HI[5][:], [0]) 
    for i in range(6):
        plotHI[i][0].set_data(tarrayHI[i],HI[i])

    time_spanFL = tarrayFL[5][-1] - tarrayFL[5][0]
    time_spanHI = tarrayHI[5][-1] - tarrayHI[5][0]
    
    if time_spanFL >= timemax - timedelta(minutes = 1):
        for i in range(6):
            plotFL[i][0].axes.set_xlim(tarrayFL[5][-1]-timemax + timedelta(minutes = 1),tarrayFL[5][-1]+timedelta(minutes = 1.0))
    
    if time_spanHI >= timemax - timedelta(minutes = 1):
        for i in range(6):
            plotHI[i][0].axes.set_xlim(tarrayHI[5][-1]-timemax + timedelta(minutes = 1),tarrayHI[5][-1]+timedelta(minutes = 1.0))
    
    start_time = end_time
    x = datetime.utcnow() # update x
    end_time = x
    
    return plotFL, plotHI

# interval: draw new frame every 'interval' ms
# frames: number of frames to draw 
simulation = animation.FuncAnimation(f0, updateData, blit=False, frames=200, interval=update_rate*1000, repeat=False)

# Uncomment the next line if you want to save the animation
#simulation.save(filename='sim.mp4',fps=30,dpi=300)

plt.show()
