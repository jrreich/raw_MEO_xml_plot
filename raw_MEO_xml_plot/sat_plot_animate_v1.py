# Uncomment the next two lines if you want to save the animation
#import matplotlib
#matplotlib.use("Agg")

import numpy as np
from matplotlib.pylab import *
from mpl_toolkits.axes_grid1 import host_subplot
import matplotlib.animation as animation
from matplotlib.dates import MinuteLocator
from datetime import datetime, timedelta
import sqlite3
import os
import xlrd

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

sql_folder = str(configdict['SQL_folder']) if configdict['SQL_folder'] <> '' else os.getcwd()
sqlfile = str(configdict['SQL_file']) if configdict['SQL_file'] <> '' else 'MEOLUT_packets.db'
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
    axFL[i].set_ylim(406.02e6, 406.08e6)
    axFL[i].set_xlim(x,x + timemax)
    axFL[i].grid(True)
    plotFL.append(axFL[i].plot(t,FL3, 'ro', label = "FL-Ant {}".format(i+1)))
    axFL[i].legend([plotFL[i][0]],[plotFL[i][0].get_label()])

axFL[0].set_title('FL', fontsize = 16)



## HI setup

axHI = list()
plotHI = []
axHI = [subplot2grid((6,2), (i,1)) for i in range(6)]

for i in range(6):
    axHI[i].set_ylim(406.02e6, 406.08e6)
    axHI[i].set_xlim(x,x + timemax)
    axHI[i].grid(True)
    plotHI.append(axHI[i].plot(t,HI3, 'ro', label = "HI-Ant {}".format(i+1)))
    axHI[i].legend([plotHI[i][0]],[plotHI[i][0].get_label()])

axHI[0].set_title('HI', fontsize = 16)





def find_packets(sql_file, start_date = 0, end_date = None, MEOLUT = '%',ant = '%', beaconid = '%', sat = '%'):
    conn = sqlite3.connect(sql_file)
    c = conn.cursor()
    query = ['%'+beaconid+'%', MEOLUT, start_date, end_date, ant, sat]
    c.execute('select * from packets where BcnID15 like ? and MEOLUT like ? and time > ? and time < ? and Ant like ? and Sat like?', query)
    packets = c.fetchall()
    return packets

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



sql_file = sql_folder + sqlfile
def updateData(self):
    global x
    global tarrayFL
    global tarrayHI
    global sql_file

    end_time = x + time_del
    start_time = x
    #sql_file = r"C:\Users\Jesse\Documents\Programming\test_folder\sql_db\MEOLUT_Raw_test1.db"
    for i in range(6):
        outpackFL[i][:] = find_packets(sql_file, start_time, end_time, 3669, i+1, beaconsearchstr)
        FLtimenew[i][:], FLfreqnew[i][:] = plot_packets(outpackFL[i][:])
        FL[i][:] = append(FL[i][:],FLfreqnew[i])
        tarrayFL[i][:] = append(tarrayFL[i][:],FLtimenew[i])

        outpackHI[i][:] = find_packets(sql_file, start_time, end_time, 3385, i+1, beaconsearchstr)
        HItimenew[i][:], HIfreqnew[i][:] = plot_packets(outpackHI[i][:])
        HI[i][:] = append(HI[i][:],HIfreqnew[i])
        tarrayHI[i][:] = append(tarrayHI[i][:],HItimenew[i])
    
    if len(FLtimenew[5]) == 0:
        tarrayFL[5][:] = append(tarrayFL[5][:],end_time)
        FL[5][:] = append(FL[5][:], [0])  # Fix here, fails when no data on that antenna for that beacon. 
    for i in range(6):
        plotFL[i][0].set_data(tarrayFL[i],FL[i])
    
    if len(HItimenew[5]) == 0:
        tarrayHI[5][:] = append(tarrayHI[5][:],end_time)
        HI[5][:] = append(HI[5][:], [0]) # Fix here, fails when no data on that antenna for that beacon. 
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
    
    x += time_del
    return plotFL, plotHI

# interval: draw new frame every 'interval' ms
# frames: number of frames to draw
print 'plotting...' 
simulation = animation.FuncAnimation(f0, updateData, blit=False, frames=200, interval=update_rate*1000, repeat=False)

# Uncomment the next line if you want to save the animation
#simulation.save(filename='sim.mp4',fps=30,dpi=300)

plt.show()
