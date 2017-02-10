from lxml import etree 
import lxml
import csv
import glob, os
import zipfile
import re
import sqlite3
import sys
import xlrd
import datetime


# - version 6 - 5/23/16 - What works =
# read from config file - "config_file.xls"
# filetype status - will read status messages and writes to csv but doing it with the attrib - component each line instead of header
# filetype packet - reads zip files for USSHARE messages and writes to csv or sql_db, can use search string or get all
# able to add status messages to sqlite db
# real from 'all' LUTs (currently, MD, FL, HI)

## Things left to add
# 
# - find statuses where any column (component) status is 1 - working on 12/27 in 'retreive_from_sqldb.py'
# - Read Antenna schedules and pass summaries
# - Read solutions 
# - Make different csv output that only writes errors
# - Make csv output for status messages correct (it will have to go to a sql db first it seems - or use pandas for keywords? ) 
# - Add up num of errors in status messages. 


####NOTES###
# number of components in status messages must've increased by one on 12/23 - Adding multiple DB Proxies to the end
# on 12/27 - there was no longer a Interference Processor component 


#list1 = [b for b in ET.iterfind(".//9C02BE29630F0A0")] # I think this worked... might be quicker
#etree.dump(ET) # good for viewing xml data

# Return list of files in working directory matching searchstring

def make_zip_search_str(MEOLUT, date):
    #generate zipfile name to search
 
    zipf = MEOLUT + '_' + str(date.year) + '-' + '{:02d}'.format(date.month) + '-' + '{:02d}'.format(date.day) + '.zip'
    return zipf

def file_search_regex(filetypesearch):
    if (filetypesearch == "packet" or filetypesearch == "TOA_FOA_DATA"):
        my_regex = r"(.*)"+ re.escape("USSHARE") + r"(.*)"
    else:
        my_regex = r"(.*)"+ re.escape("USMCC") + r"(.*)"
    return my_regex

def find_files(searchstring):
    sharefiles = list()
    for files in glob.glob(searchstring):
        sharefiles.append(files)
    return sharefiles

# Return list of files of in zip file matching searchstring
def find_file_inzip(zipfilename,searchstring):
    with zipfile.ZipFile(zipfilename, 'r') as myzip:
        ziplist = myzip.namelist()
        matches = [string for string in ziplist if re.match(searchstring, string)]
        print 'num of files in ' + zipfilename + ' = ' + str(len(ziplist))
        print 'returning ' + str(len(matches)) + ' files in zip with search string ' + searchstring 
        return matches

#returns list of packets from an ET after finding the search string in the search tag - ie find a beacon ID in tag MF22. 
def find_str_in_tag(ET,searchtag,searchstr):
    packetlist = list()
    packets = ET.xpath("//{}[contains(.,'{}')]".format(searchtag,searchstr))
    for elem in packets:
        packet = elem.getparent()
        packetlist.append(packet)
    return packetlist
 
#returns packets meeting searchstring from an XML file if no search defined returns all - inputs - XML file name and searchtag and searchstring - 
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
    
# Write packets [element] to csv file
def write_bursts_csv(packets,csvoutfile, filetypesearch, filename):
    burst = list()
    componentlist = list()
    with open(csvoutfile, 'ab') as myfile:
        if filetypesearch == "status":
            headerdate = packets[0].xpath('//header')[0].attrib['date']
            burst.append(headerdate)
            burst.append(filename)
            componentlist.append(headerdate)
            componentlist.append(filename)
            for row in packets:
                for v in row.attrib['status']:
                    statusout = [v]
                    #componentout = [row.attrib['component']] # writes components each line
                    burst.extend(statusout)
                    #componentlist.extend(componentout)
            wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
            #wr.writerow(componentlist) #### writes component list each line 
            wr.writerow(burst)
            componentlist = list()
            burst = list()
        elif (filetypesearch == "packet" or filetypesearch == "TOA_FOA_DATA"):
            for packet in packets:
                for MF in packet:
                    burst.append(MF.text)
                wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
                wr.writerow(burst)
                burst=list()
def write_to_sqldb(packets,filetype,MEOLUT, filename):
    if filetype == "status":
        print 'test 4'
        conn = sqlite3.connect('MEOLUT.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE if not exists status (date_time DATETIME2 PRIMARY KEY, MEOLUT TEXT, filename TEXT, AntControlSW INT, ACU INT, CalibSW INT,
CmdNotifier INT, CommSrvr INT, DBSrvr1a INT, DBSrvr1b INT, DBProxy INT, DCU INT, GPSRcvr INT, 
InterferenceProc INT, LocProc INT,InterferenceLocProc INT,LocProcSim INT, MatchMergeProc INT, 
OrbitRetrvr INT, ProcSW INT, BcnProcSrvr INT, Scheduler INT, RcvrSrvr INT, Srvr1a INT, Srvr1b INT, 
Srvr2a INT, Srvr2b INT, Srvr3a INT, Srvr3b INT, SysCont INT,InterfererLocProc INT, BcnProcSW INT, 
DASSAntMC INT, DASSAnt INT)''')
        headerdate = packets[0].xpath('//header')[0].attrib['date']
        headerdate2 = headerdate.replace("T"," ")
        headerdate3 = headerdate2.replace("Z"," ")
        entry = list()
        entry.append(headerdate3)
        entry.append(MEOLUT)
        entry.append(filename)
        c.execute("INSERT OR IGNORE INTO status(date_time, MEOLUT, filename) VALUES (?,?,?)",entry)
        conn.commit()
        for row in packets:
            for v in row.attrib['status']:
                component = row.attrib['component']
                c.execute('UPDATE status SET {cmp}={val} WHERE date_time = ?'.format(cmp = CompDict[component], val=v),(headerdate3,))
                conn.commit()
                statusout = [v]
                entry.extend(statusout)
        #bindings = '?,' * (len(entry)-1) + '?'
    if (filetype == "packet" or filetype == "TOA_FOA_DATA" or filetype == 'solution'):
        for packet in packets:
            burstlist.append([MF.text for MF in packet])
        print len(burstlist)
        print burstlist
        waiting = raw_input('waiting')
#Opens csvfile with 'write' to erase data and then write headers, filetype determines what headers to write
def write_headers(filetype,csvoutfile, writeto):
    with open(csvoutfile, 'wb') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        if (filetype == "packet" or filetype == "TOA_FOA_DATA"): wr.writerow(USSHAREfileheader)
        elif filetype == 'status': wr.writerow(Statusfileheader)

#search through zip file - if searchtag and searchstr are defined; write packets to csvoutfile - write all if not define
def search_zip_output(MEOLUT, zip,zipmatches,filetypesearch,csvoutfile,searchtag = None,searchstr = None, writeto = 'both'):
    #open file and write headers which erases data in it
    #write_headers_USSHARE(csvoutfile) - Need new Functions to write different headers other than USSHARE raw data
    #if filetypesearch == 'packet': write_headers_USSHARE(csvoutfile)
    if writeto == 'csv' or writeto == 'both' : write_headers(filetypesearch,csvoutfile,writeto)
    with zipfile.ZipFile(zip, 'r') as myzip:
        for files in zipmatches:
            file = myzip.open(files)
            filename = str(file)   
            #print 'searching file = ' + str(file) + ' for ' + filetypesearch
            
            packets = xml_process(file,filetypesearch, searchtag,searchstr)
            #print 'num of packets = ' + str(len(packets)) ### possibly only write if packets aren't 'none'
            if packets: 
                if writeto == 'csv': write_bursts_csv(packets,csvoutfile,filetypesearch, files)
                elif writeto == 'sql_db': write_to_sqldb(packets,filetypesearch, MEOLUT,files)
                else: 
                    write_bursts_csv(packets,csvoutfile,filetypesearch,files)
                    write_to_sqldb(packets,filetypesearch, MEOLUT,files)
                
#~~~~~~~ Setting up parameters and calling functions

#header line for csv file if raw USSHARE
USSHAREfileheader = ['Sat','MEOLUT','Ant?','BcnID15','BcnID30','Time','Freq','?','?','CN0?','BitRate','?']
Statusfileheader = ['Date/Time','File Name','Antenna Control Software','Antenna Control Unit','Calibration Software',
'Command Notifier','Communications Server','Database Server 1a','Database Server 1b','Database Proxy',
'Downconverter Unit','GPS Receiver','Interference Processor','Location Processor','Interference Location Processor',
'Location Processor Simulator','Match/Merge Processor','Orbit Retriever (Ephemeris Program)','Processor Software',
'Beacon Processor Server','Scheduler','Receiver Server','Server 1a','Server 1b','Server 2a','Server 2b',
'Server 3a','Server 3b','System Controller', 'DASS Antenna Master Control','DASS Antenna']

CompDict = {'Date/Time':'date_time','Antenna Control Software':'AntControlSW','Antenna Control Unit':'ACU',
'Calibration Software':'CalibSW','Command Notifier':'CmdNotifier','Communications Server':'CommSrvr',
'Database Server 1a':'DBSrvr1a','Database Server 1b':'DBSrvr1b','Database Proxy':'DBProxy','Downconverter Unit':'DCU',
'GPS Receiver':'GPSRcvr','Interference Processor':'InterferenceProc','Location Processor':'LocProc',
'Interference Location Processor':'InterferenceLocProc', 'Location Processor Simulator':'LocProcSim',
'Match/Merge Processor':'MatchMergeProc','Orbit Retriever (Ephemeris Program)':'OrbitRetrvr','Processor Software':'ProcSW',
'Beacon Processor Server':'BcnProcSrvr','Scheduler':'Scheduler','Receiver Server':'RcvrSrvr','Server 1a':'Srvr1a',
'Server 1b':'Srvr1b','Server 2a':'Srvr2a','Server 2b':'Srvr2b','Server 3a':'Srvr3a','Server 3b':'Srvr3b',
'System Controller':'SysCont','Interferer Location Processor':'InterfererLocProc','Beacon Processor Software':'BcnProcSW',
'DASS Antenna Master Control':'DASSAntMC','DASS Antenna':'DASSAnt'}


#Dict for translatting Message Fields 
MFDict = {'Sat':'MF6','MEOLUT':'MF11','Ant':'MF71','Bcn15':'MF22','Bcn36':'MF77','Date':'MF67',
'Freq':'MF68'}

print '\nCurrent directory is - ' + os.getcwd()

#Read config file before switching directories
if len(sys.argv) > 1:
    configfile = sys.argv[1]
else:
    configfile = 'sat_plot_config.xls'
#reader = csv.reader(open(configfile,'r'))
print 'Reading configuration:'
print '   ' + os.getcwd() + '\\' + configfile

## reading config file into dictionary  - for csv 
#configdict=dict(reader)
def read_config_file():
    configdict = {}
    wb = xlrd.open_workbook(configfile)
    sh = wb.sheet_by_index(0)
    for i in range(21,37): # Only looking for items in rows 22 - 38 right now - column B and C
        try: 
            cell_value = sh.cell(i,2).value
            cell_key = sh.cell(i,1).value
            configdict[cell_key] = cell_value
        except Exception:
            break
    return configdict

configdict = read_config_file()

zip_folder = str(configdict['zip_folder']) if configdict['zip_folder'] <> '' else os.getcwd()
MEOLUT_in = str(configdict['MEOLUT'])
MEOLUT_list = [x.strip() for x in MEOLUT_in.split(',')] 
filetypesearch = str(configdict['filetypesearch'])
csvoutfilestr = str(configdict['csvoutfile'])
sql_out_folder = str(configdict['SQL_out_folder']) if configdict['SQL_out_folder'] <> '' else os.getcwd()
sql_out_file = str(configdict['SQL_out_file']) if configdict['SQL_out_file'] <> '' else 'MEOLUT_packets.db'
searchtag1 = str(configdict['searchtag1'])
searchstr1 = str(configdict['searchstr1'])
searchtag2 = str(configdict['searchtag2'])
searchstr2 = str(configdict['searchstr2'])
writeto = str(configdict['writeto'])
date1 = datetime.datetime(*xlrd.xldate_as_tuple(configdict['start_date'],0))


if configdict['end_date']: 
    date2 = datetime.datetime(*xlrd.xldate_as_tuple(configdict['end_date'],0))
    datelist = [date1 + datetime.timedelta(days=x) for x in range(0,(date2-date1).days+1)]
else:
    datelist = [date1]

os.chdir(zip_folder)
print '\nReading zips from:' 
print '   ' + os.getcwd()

burstlist = list()
for day in datelist:
    for MEO in MEOLUT_list:
        zipf = make_zip_search_str(MEO,day)
        print csvoutfilestr
        if csvoutfilestr == "":
            csvoutfile = zipf + '_' + filetypesearch + '_' + searchstr1 + '.csv'
        else:
            csvoutfile = zipf + '_' + csvoutfilestr + '.csv'

        my_regex = file_search_regex(filetypesearch)
        zipmatches = find_file_inzip(zipf, my_regex)
        burstlist = list()
        #Main function to search zip files and output to csv or sql
        search_zip_output(MEO, zipf, zipmatches, filetypesearch, csvoutfile,searchtag1,searchstr1, writeto)
        if (writeto == 'sql_db' or writeto == 'both') and (filetypesearch == 'packets' or filetypesearch == 'TOA_FOA_DATA'):
            print 'writing packets to db'
            conn = sqlite3.connect(sql_out_folder + sql_out_file)
            c = conn.cursor()
            c.execute('''CREATE TABLE if not exists packets (Burst_ID Integer PRIMARY KEY, 
    Sat INT, MEOLUT INT, Ant INT, BcnID15 TEXT, BcnID30 TEXT, Time DATETIME2, Freq REAL, 
    Unknown1 INT, Unknown2 INT, CN0 REAL, BitRate REAL, Unknown3 INT, UNIQUE(MEOLUT, Ant, Time))''')
            for row in burstlist:
                row[5] = datetime.datetime.strptime(row[5],'%y %j %H%M %S.%f')
            c.executemany('INSERT OR IGNORE INTO packets(Sat, MEOLUT, Ant, BcnID15, BcnID30, Time, Freq, Unknown1, Unknown2, CN0, BitRate, Unknown3) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', burstlist)
            conn.commit()
            conn.close()
        if (writeto == 'sql_db' or writeto == 'both') and (filetypesearch == 'solution'):
            print 'writing packets to db'
            conn = sqlite3.connect(sql_out_folder + sql_out_file)
            c = conn.cursor()
            c.execute('''CREATE TABLE if not exists packets (SolId Integer PRIMARY KEY, 
    SourceId INT, DataType INT, BeaconMessageType INT, BeaconMessageValid INT, BcnId36 TEXT, BcnId30 TEXT, 
    BcnId15	TEXT, FrameSync TEXT, NumBursts	INT, NumPackets INT, NumSatellites INT, NumPacketsUnUsed INT,
    DOP REAL, TimeFirst DATETIME2, TimeLast DATETIME2, Latitude REAL, Longitude REAL, Altitude REAL, FreqBias REAL,
    FreqDrift REAL, QualityFactor INT, Iterations INT, AverageCN0 REAL, MinimumCN0 REAL, MaximumCN0 REAL,
    EEMajor REAL, EEMinor REAL, EEHeading REAL, EERadius REAL, EEArea REAL, TimeSolutionGenerated DATETIME2, 
    TimeSolutionAdded DATETIME2, ExpectedHorzError REAL, UNIQUE(SolId))''')
    # AntId1Sat INT, AntId2Sat INT, AntId3Sat INT, SatelliteIds	SourceAntennaIds
    # SitFunc MsgNum QualityIndicator NumAntennas Srr PositionConfFlag SortId SortType Distance	
            for row in burstlist:
                row[5] = datetime.datetime.strptime(row[5],'%y %j %H%M %S.%f')
            c.executemany('''INSERT OR IGNORE INTO packets(SolId, SourceId, DataType, BeaconMessageType,
    BeaconMessageValid, BcnId36, BcnId30, BcnId15, FrameSync, NumBursts, NumPackets, NumSatellites, NumPacketsUnUsed,
    DOP, TimeFirst, TimeLast, Latitude, Longitude, Altitude, FreqBias, FreqDrift, QualityFactor, Iterations, 
    AverageCN0, MinimumCN0, MaximumCN0, EEMajor, EEMinor, EEHeading, EERadius, EEArea, TimeSolutionGenerated, 
    TimeSolutionAdded, ExpectedHorzError) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', burstlist)
            conn.commit()
            conn.close()
