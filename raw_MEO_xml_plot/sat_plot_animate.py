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

xlimit = 5.0
timepacket_format = '%Y-%m-%d %H:%M:%S.%f'

#t = datetime.utcnow()
x = datetime(2016, 6, 10, 0)
time_del = timedelta(seconds = 60)
t=zeros(0)
timemax = timedelta(minutes = 10)
beaconsearchstr = '%'

# Sent for figure
font = {'size'   : 9}
matplotlib.rc('font', **font)
FiveMinutes = MinuteLocator(interval=5)


# Setup figure and subplots
f0 = figure(num = 0, figsize = (12, 8))#, dpi = 100)
f0.suptitle("MEOLUT Raw Data", fontsize=18)




#ax10 = subplot2grid((6, 2), (0, 0))
#ax20 = subplot2grid((6, 2), (1, 0))
#ax30 = subplot2grid((6, 2), (2, 0))
#ax40 = subplot2grid((6, 2), (3, 0))
#ax50 = subplot2grid((6, 2), (4, 0))
#ax60 = subplot2grid((6, 2), (5, 0))

ax11 = subplot2grid((6, 2), (0, 1))
ax21 = subplot2grid((6, 2), (1, 1))
ax31 = subplot2grid((6, 2), (2, 1))
ax41 = subplot2grid((6, 2), (3, 1))
ax51 = subplot2grid((6, 2), (4, 1))
ax61 = subplot2grid((6, 2), (5, 1))
#tight_layout()

# Set titles of subplots
#ax10.set_title('FL', fontsize = 16)
#ax11.set_title('HI', fontsize = 16)


# set y-limits
#ax10.set_ylim(406.02e6, 406.08e6)
#ax20.set_ylim(406e6, 406.1e6)
#ax30.set_ylim(406e6, 406.1e6)
#ax40.set_ylim(406e6, 406.1e6)
#ax50.set_ylim(406e6, 406.1e6)
#ax60.set_ylim(406e6, 406.1e6)

ax11.set_ylim(406e6, 406.1e6)
ax21.set_ylim(406e6, 406.1e6)
ax31.set_ylim(406e6, 406.1e6)
ax41.set_ylim(406e6, 406.1e6)
ax51.set_ylim(406e6, 406.1e6)
ax61.set_ylim(406e6, 406.1e6)


# sex x-limits
#ax10.set_xlim(x,x + timemax)
#ax20.set_xlim(x,x + timemax)
#ax30.set_xlim(x,x + timemax)
#ax40.set_xlim(x,x + timemax)
#ax50.set_xlim(x,x + timemax)
#ax60.set_xlim(x,x + timemax)

ax11.set_xlim(0,xlimit)
ax21.set_xlim(0,xlimit)
ax31.set_xlim(0,xlimit)
ax41.set_xlim(0,xlimit)
ax51.set_xlim(0,xlimit)
ax61.set_xlim(0,xlimit)

# Turn on grids
#ax10.grid(True)
#ax20.grid(True)
#ax30.grid(True)
#ax40.grid(True)
#ax50.grid(True)
#ax60.grid(True)

ax11.grid(True)
ax21.grid(True)
ax31.grid(True)
ax41.grid(True)
ax51.grid(True)
ax61.grid(True)

# set label names
#ax10.set_xlabel("x")
#ax10.set_ylabel("py")
#ax20.set_xlabel("t")
#ax20.set_ylabel("vy")
#ax30.set_xlabel("t")
#ax30.set_ylabel("py")
#ax40.set_ylabel("vy")

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

axFL = list()
plotFL = []
axFL = [subplot2grid((6,2), (i,0)) for i in range(6)]

for i in range(6):
    axFL[i] = subplot2grid((6,2), (i,0))
    axFL[i].set_ylim(406.02e6, 406.08e6)
    axFL[i].set_xlim(x,x + timemax)
    axFL[i].grid(True)
    plotFL.append(axFL[i].plot(t,FL3, 'ro', label = "FL-Ant {}".format(i+1)))
    axFL[i].legend([plotFL[i][0]],[plotFL[i][0].get_label()])

axFL[0].set_title('FL', fontsize = 16)
#ax11.set_title('HI', fontsize = 16)

#p10, = ax10.plot(t,FL1,'ro', label="FL-1")
#p20, = ax20.plot(t,FL2,'ro', label="FL-2")
#p30, = ax30.plot(t,FL3,'ro', label="FL-3")
#p40, = ax40.plot(t,FL4,'ro', label="FL-4")
#p50, = ax50.plot(t,FL5,'ro', label="FL-5")
#p60, = ax60.plot(t,FL6,'ro', label="FL-6")

p11, = ax11.plot(t,HI1,'b', label="HI-1")
p21, = ax21.plot(t,HI2,'b', label="HI-2")
p31, = ax31.plot(t,HI3,'b', label="HI-3")
p41, = ax41.plot(t,HI4,'b', label="HI-4")
p51, = ax51.plot(t,HI5,'b', label="HI-5")
p61, = ax61.plot(t,HI6,'b', label="HI-6")


# set lagends
#ax10.legend([p10], [p10.get_label()])
#ax20.legend([p20], [p20.get_label()])
#ax30.legend([p30], [p30.get_label()])
#ax40.legend([p40], [p40.get_label()])
#ax50.legend([p50], [p50.get_label()])
#ax60.legend([p60], [p60.get_label()])

ax11.legend([p11], [p11.get_label()])
ax21.legend([p21], [p21.get_label()])
ax31.legend([p31], [p31.get_label()])
ax41.legend([p41], [p41.get_label()])
ax51.legend([p51], [p51.get_label()])
ax61.legend([p61], [p61.get_label()])

# Data Update
#xmin = 0.0
#xmax = 5.0



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

FL = [],[],[],[],[],[]
outpack = [],[],[],[],[],[]
FLtimenew = [],[],[],[],[],[]
FLfreqnew = [],[],[],[],[],[]
tarray = [],[],[],[],[],[]
def updateData(self):
    global FL1
    global FL2
    global FL3
    global FL4
    global FL5
    global FL6
    global HI1
    global HI2
    global HI3
    global HI4
    global HI5
    global x
    global tarray

    #tmpp1 = 1 + np.exp(-x) *np.sin(2 * np.pi * x)
    #FL1=append(FL1,tmpp1)
    end_time = x + time_del
    start_time = x
    sql_file = r"C:\Users\Jesse\Documents\Programming\test_folder\sql_db\MEOLUT_Raw_test1.db"
    for i in range(6):
        outpack[i][:] = find_packets(sql_file, start_time, end_time, 3669, i+1, beaconsearchstr)
        FLtimenew[i][:], FLfreqnew[i][:] = plot_packets(outpack[i][:])
        FL[i][:] = append(FL[i][:],FLfreqnew[i])
        tarray[i][:] = append(tarray[i][:],FLtimenew[i])

    if len(FLtimenew[5]) == 0:
        tarray = append(tarray,end_time)
        FL[5] = append(FL[5], 0)
    for i in range(6):
        plotFL[i][0].set_data(tarray[i],FL[i])

    time_span = tarray[5][-1] - tarray[5][0]
    if time_span >= timemax - timedelta(minutes = 1):
        for i in range(6):
            plotFL[i][0].axes.set_xlim(tarray[5][-1]-timemax + timedelta(minutes = 1),tarray[5][-1]+timedelta(minutes = 1.0))
    x += time_del
    return plotFL

# interval: draw new frame every 'interval' ms
# frames: number of frames to draw
simulation = animation.FuncAnimation(f0, updateData, blit=False, frames=200, interval=100, repeat=False)

# Uncomment the next line if you want to save the animation
#simulation.save(filename='sim.mp4',fps=30,dpi=300)

plt.show()
