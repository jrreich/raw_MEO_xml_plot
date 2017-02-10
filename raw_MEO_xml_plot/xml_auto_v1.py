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
import itertools


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
    packets = []
    ET1, ET2 = itertools.tee(etree.iterparse(filename))
    #for i, item in ET:
    #        print 'tag - {}, attrib - {}, text - {}'.format(item.tag, item.attrib, item.text)
    #        print item.items(), item.keys()
    #        packets = ET
    #waiting = raw_input('wait for enter')
    if searchstr: # could use this statement with the default bcnID = False to process all or using search string
        packets = find_str_in_tag(ET, searchtag, searchstr)
        print packets
    elif (filetype == 'packets' or filetype == 'TOA_FOA_DATA'):
        e = etree.parse(filename).getroot()
        packets = e.findall(".//{}".format(filetype))
        #packets = e.findall(".//[contains(antennaId=,'1')])#*".format(filetype))
        #print str(len(packets))
    #print str(len(packets)) + ' packets returned from xml_process with filetype ' + filetype
    #if packets: print 'Found packets. First packet in list is element? ' + str(etree.iselement(packets[0]))
    else:
        for i, item in ET1:
            if (item.tag == 'solutionsMessage'):
                packets = ET2
    #print packets 
    return packets
    
# Write packets [element] to csv file

def write_to_sqldb(packets,filetype,MEOLUT, filename):
    if (filetype == "packet" or filetype == "TOA_FOA_DATA"):
        for packet in packets:
            burstlist.append([MF.text for MF in packet])

#search through zip file - if searchtag and searchstr are defined; write packets to csvoutfile - write all if not define
def search_zip_output(MEOLUT, zip,zipmatches,filetypesearch,csvoutfile,searchtag = None,searchstr = None, writeto = 'both'):
    with zipfile.ZipFile(zip, 'r') as myzip:
        for files in zipmatches:
            file = myzip.open(files)
            filename = str(file)              
            packets = xml_process(file,filetypesearch, searchtag,searchstr)
            if packets: write_to_sqldb(packets,filetypesearch, MEOLUT,files)
                
#~~~~~~~ Setting up parameters and calling functions

#header line for csv file if raw USSHARE
USSHAREfileheader = ['Sat','MEOLUT','Ant?','BcnID15','BcnID30','Time','Freq','?','?','CN0?','BitRate','?']


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


zip_folder = str(configdict['zip_folder']) if configdict['zip_folder'] <> '' else os.getcwd()
sql_out_folder = str(configdict['SQL_out_folder']) if configdict['SQL_out_folder'] <> '' else os.getcwd()
sql_out_file = str(configdict['SQL_out_file']) if configdict['SQL_out_file'] <> '' else 'MEOLUT_packets.db'
date1 = datetime.datetime(*xlrd.xldate_as_tuple(configdict['start_date'],0))

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
        print 'filetypesearch = '
        print filetypesearch
        if (writeto == 'sql_db' or writeto == 'both') and (filetypesearch == 'packets' or filetypesearch == 'TOA_FOA_DATA'):
            print 'writing packets to db  2313'
            print sql_out_folder + sql_out_file
            conn = sqlite3.connect(sql_out_folder + sql_out_file)
            c = conn.cursor()
            c.execute('''CREATE TABLE if not exists packets (Burst_ID Integer PRIMARY KEY, 
    Sat INT, MEOLUT INT, Ant INT, BcnID15 TEXT, BcnID30 TEXT, Time DATETIME2, Freq REAL, 
    Unknown1 INT, Unknown2 INT, CN0 REAL, BitRate REAL, Unknown3 INT, UNIQUE(MEOLUT, Ant, Time))''')
            for row in burstlist:
                dt = datetime.datetime.strptime(row[5],'%y %j %H%M %S.%f')  ### this doesn't work if the seconds are exactly .000000 it truncates
                row[5] = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            c.executemany('INSERT OR IGNORE INTO packets(Sat, MEOLUT, Ant, BcnID15, BcnID30, Time, Freq, Unknown1, Unknown2, CN0, BitRate, Unknown3) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', burstlist)
            conn.commit()
            conn.close()
        if (writeto == 'sql_db' or writeto == 'both') and (filetypesearch == 'solutionsMessage'):
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
            print burstlist[0:20]
            print len(burstlist)
            for row in burstlist:
                print row
                row[5] = datetime.datetime.strptime(row[5],'%y %j %H%M %S.%f')
            c.executemany('''INSERT OR IGNORE INTO packets(SolId, SourceId, DataType, BeaconMessageType,
    BeaconMessageValid, BcnId36, BcnId30, BcnId15, FrameSync, NumBursts, NumPackets, NumSatellites, NumPacketsUnUsed,
    DOP, TimeFirst, TimeLast, Latitude, Longitude, Altitude, FreqBias, FreqDrift, QualityFactor, Iterations, 
    AverageCN0, MinimumCN0, MaximumCN0, EEMajor, EEMinor, EEHeading, EERadius, EEArea, TimeSolutionGenerated, 
    TimeSolutionAdded, ExpectedHorzError) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', burstlist)
            conn.commit()
            conn.close()
