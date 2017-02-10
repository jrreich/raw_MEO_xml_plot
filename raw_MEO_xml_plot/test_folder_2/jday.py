#
#                           function jday.m
#
#  this function finds the julian date given the year, month, day, and time.
#
#  author        : david vallado                  719-573-2600   27 may 2002
#
#  revisions
#                -
#
#  inputs          description                    range / units
#    year        - year                           1900 .. 2100
#    mon         - month                          1 .. 12
#    day         - day                            1 .. 28,29,30,31
#    hr          - universal time hour            0 .. 23
#    min         - universal time min             0 .. 59
#    sec         - universal time sec             0.0 .. 59.999
#    whichtype   - julian .or. gregorian calender   'j' .or. 'g'
#
#  outputs       :
#    jd          - julian date                    days from 4713 bc
#
#  locals        :
#    none.
#
#  coupling      :
#    none.
#
#  references    :
#    vallado       2007, 189, alg 14, ex 3-14
#
# jd = jday(yr, mon, day, hr, min, sec)
# -----------------------------------------------------------------------------
import math as m
import datetime

def JD(dateobj):
        jd = float(367.0 * dateobj.year - m.floor( 
        (7.0 * (dateobj.year + m.floor( (dateobj.month + 9.0) / 12.0) ) ) * 0.25 ) + m.floor(
        275.0 * dateobj.month / 9.0 ) + dateobj.day + 1721013.5 + (
        (dateobj.second/60.0 + dateobj.minute ) / 60.0 + dateobj.hour ) / 24.0)
        return jd
        #  - 0.5 * sign(100.0 * yr + mon - 190002.5) + 0.5;
def jday_now():
    now1 = datetime.datetime.utcnow()
    jdatenow = JD(now1.year,now1.month, now1.day, now1.hour,now1.minute, now1.second)
    return jdatenow
def gst(dateob): 
    JDayObj = datetime.datetime(dateob.year,dateob.month, dateob.day, 0, 0, 0)
    JD0 = JD(JDayObj)
    GMT = float((dateob.hour * 60.0**2 + dateob.minute * 60.0 + dateob.second) / 86400.0)
    Tut1=(JD0-2451545.0)/36525.0
    GST0 = 100.4606184 + 36000.77005361* Tut1 + 0.00038793 * Tut1**2  #- 2.6e-8 * Tut1**3
    GST0 = GST0 % 360.0
    GST = GST0 + 0.25068447733746215 * float((dateob.hour*60.0) + dateob.minute + (dateob.second/60.0))
    GST = GST % 360.0
    #T0=6.697374558 + (2400.051336*T)+(0.000025862*T**2)+(GMT*1.0027379093)
    #T0 = T0 % 24
    #print JD0, GMT, Tut1, GST0
    return GST #returns GST in degrees
def LST(GST, longitude):
    localsidtime = GST + longitude
    if localsidtime < 0:
        localsidtime += 360
    return localsidtime #returns LST in degrees

def LST_now(Longitude): 
    now1 = datetime.datetime.utcnow()
    gstnow = gst(now1)
    LST_now = LST(gstnow, Longitude)
    LST_now = LST_now/360 * 24 
    timeout = dec_hours(LST_now)
    return timeout

def dec_hours(dechours):
    hours = int(dechours)
    dec_mins = (dechours - hours)*60
    mins = int(dec_mins)
    secs = (dec_mins-mins)*60
    time = str.format("{:0>2d}:{:0>2d}:{:.5f}", hours,mins, secs)
    return time 

def utc_now():
    return datetime.datetime.utcnow()