#!/usr/bin/python

# Requires SmokePing ver 2.4.2

from zenoss import Zenoss
import sys, logging, re

CLEARSTR = "-clear"
logging.basicConfig(filename='/opt/smokeping2zenoss/zensmokeping.log', level=logging.INFO, format='%(asctime)s %(levelname)s : %(message)s')

def get_avertt(rttstring):
    rtttotal = 0
    rttcount = 0
    for r in rtt[5:].split(', '):
        try:
            rtttotal += float(r[:-2])
            rttcount += 1
        except ValueError:
            pass
    try:
        rttave = rtttotal/rttcount
        rttave = str(rttave) + "ms"
    except ZeroDivisionError:
        rttave = "Unkown"
    return rttave

def get_avepercent_loss(lossstring):
    losstotal = 0
    losscount = 0
    for l in loss[6:].split(', '):
        try:
# josephson
            print len(l)-1
            losstotal += float(l[:len(l)-1])
            losscount += 1
        except ValueError:
            pass
    lossave = losstotal/losscount
    losspercent =  "%.2f%%" % lossave
    return losspercent


if len(sys.argv) < 2:
        logging.error("Event details not specified")
        sys.exit("Event details not specified");

alert = sys.argv[1]
device = sys.argv[2]
loss = sys.argv[3]
rtt = sys.argv[4]
ipAddress = sys.argv[5]

# TEMPORARY: just curious about the content of 'alert' - Josephson
# outfile = open('/home/ubuntu/smoke.alerts.test.txt', 'a')
# outfile.write(alert + '; ' + device + '; ' + loss + '; ' + rtt + '; ' + ipAddress + '\n')
# outfile.close()
# TEMPORARY

#FIXME: Try to find better device mapping
#FIXME: Not all device are in the format *.devicename
m = re.match(".*\.(\S+)", device)
device = m.group(1).replace('_', '.')
device = device.replace('..', '_')

alert = alert.title().replace('_', ' ')
losspercent = get_avepercent_loss(loss)
rttave = get_avertt(rtt)

# map different severity levels
from ConfigParser import ConfigParser
cfg = ConfigParser()
cfg.read('/opt/smokeping2zenoss/zensmokeping.cfg')

#Clear detection
#TODO: Severity value should come from Smokeping alert to Zenoss severity mapping
clear = alert.find(CLEARSTR.title())
if clear >= 0:
    alert = alert[0:-len(CLEARSTR)]
    severity = "Clear"
else:
###    severity = "Critical"
    if (cfg.has_section(alert)):
###        print "Severity should be", cfg.get(alert, 'severity')
        severity = cfg.get(alert, 'severity')

event = ""
if alert == "Lossdetector":
    event = losspercent + " packet loss detected to "
elif alert == "Rttdetector":
    event = rttave + " RTT detected to "

summary = event
summary += device + " " + loss + " "
summary += rtt

evdata = {'device': device, 'summary': summary, 'severity': severity, 'component': alert, 'evclass': "/Status/Smokeping", 'evclasskey': 'smokeping' }

#z = Zenoss('https://zenoss_ip', 'smokeping', 'password')
z = Zenoss('http://zenoss-smokeping.cascadeo.com:8080', 'admin', 'z3n0ss99')
z.create_event_on_device(evdata)
logging.info("Pushed event to Zenoss")
