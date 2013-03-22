import Globals
import os.path
from Products.ZenModel.ZenPack import ZenPackBase
from Products.CMFCore.DirectoryView import registerDirectory

skinsDir = os.path.join(os.path.dirname(__file__), 'skins')
if os.path.isdir(skinsDir):
    registerDirectory(skinsDir, globals())


from copy import copy
from Products.ZenModel.Device import Device
from Products.ZenModel.ZenossSecurity import ZEN_VIEW

class ZenPack(ZenPackBase):
    """ Smokeping loader
    """
    packZProperties = [
	('zSmokepingPrivateUrl', 'http://zenoss-smokeping.cascadeo.com/smokeping/', 'string'),
        ('zSmokepingPublicUrl', 'http://zenoss-smokeping.cascadeo.com/smokeping/', 'string'),
	('zSmokepingTarget', '', 'string'),
        ]
    
    def install(self, app):
        ZenPackBase.install(self, app)

# Get a copy of the device tab definitions.
custom_actions = []
custom_actions.extend(Device.factory_type_information[0]['actions'])

# Add our custom "MyTab" in position 4. This is right before Events.
custom_actions.insert(5, dict(
    id="smokepingGraphs",
    name="Smokeping Graphs",
    action="smokepingGraphs",
    permissions=(ZEN_VIEW,),
    ))

# Set the device tab definitions to our custom set.
Device.factory_type_information[0]['actions'] = custom_actions

# Make a copy of the original method so we can augment it.
original_zentinelTabs = copy(Device.zentinelTabs)

# Create a new zentinelTabs method that filters out our tab for non-servers.
def new_zentinelTabs(self, templateName):
    tabs = super(Device, self).zentinelTabs(templateName)
    return tabs

# Replace the zentinelTabs method with our own.
Device.zentinelTabs = new_zentinelTabs


#### New Page ###
import urllib2, StringIO, cgi, datetime
from AccessControl import getSecurityManager,Unauthorized

def updateSPDevice(self, url, sizelimit=None, REQUEST=None):
    """
    Trigger smokeping to recreate images
    """
    user = getSecurityManager().getUser().getUserName()
    if user == 'Anonymous User':
        raise Unauthorized("Unauthorized")
    
    try:
        site = urllib2.urlopen(url)
    except urllib2.HTTPError:
        return False

    return str(datetime.datetime.now())

def fetchImage(self, url, sizelimit=None, REQUEST=None):
    """
    fetch images
    """
    # temporary - Josephson
    import os
    user = getSecurityManager().getUser().getUserName()
    os.system("echo \"user: %s\" >> /usr/local/zenoss/zenoss/log/event.log" % user)
    # temporary - Josephson

    if user == 'Anonymous User':
        raise Unauthorized("Unauthorized")

    # temporary - Josephson
    # to accomodate Smokeping auth - Josephson
    os.system("echo \"URL IS: %s\" >> /usr/local/zenoss/zenoss/log/event.log" % url)
    import re
    smokeping_user = 'zenoss'
    smokeping_pword = 'z3n0ss99'
    url_m1 = re.search('http:', url)
    if url_m1:
        new_url = url[0:7] + smokeping_user + ':' + smokeping_pword + '@' + url[7:]
    else:
        url_m2 = re.search('https:', url)
        if url_m2:
            new_url = url[0:8] + smokeping_user + ':' + smokeping_pword + '@' + url[8:]

    site = urllib2.urlopen(url)
    text = site.read( )
    if not sizelimit: sizelimit = len(text)

    REQUEST.RESPONSE.setHeader('Content-Type','image/png')
    return text[:sizelimit]

def createSPDashboard(self, REQUEST=None):
    """
    Quick implementation of Smokeping Dashboard
    """
    user = getSecurityManager().getUser().getUserName()
    if user == 'Anonymous User':
        raise Unauthorized("Unauthorized")


    html = ""

    # Get urls of target dashboard
    devices = self.dmd.Devices.getSubDevices()
    urls = {}
    for d in devices:
        if d.zSmokepingTarget == "":
            continue

        url = d.zSmokepingPrivateUrl + 'smokeping.cgi?target='
        targets = d.zSmokepingTarget.split('/')
        for t in targets:
            if t == targets[-1]:
                break
            url += t + '.'
            urls[url] = 1

    # Fetch target dashboard webpage to trigger smokeping to create latest images
    # temporary - Josephson
    # to accomodate Smokeping auth - Josephson
    import os
    for url in urls.keys():
        # temporary - Josephson
        # to accomodate Smokeping auth - Josephson
        os.system("echo \".urllib2.urlopen(\"%s\")\" >> /usr/local/zenoss/zenoss/log/event.log" % url)
        site = urllib2.urlopen(url)
            
    # Generate Dasboard for Zenoss
    html += "<html><body><div id=\"zensmokeping_dashboard\"><ul>"
#    # sort the devices
#    sorted_devices = sorted(devices, key=lambda dv: dv.getProperty('cSmokepingGroup'))
#    # for d in devices:
#    prev_smokeping_group = "" #sorted_devices[0].getProperty('cSmokepingGroup')
#    for d in sorted_devices:
#        if d.zSmokepingTarget != "":
#            isNewGroup = d.getProperty('cSmokepingGroup') != prev_smokeping_group
#            if isNewGroup:
#                if prev_smokeping_group != "":
#                    html += "</ul></li>"
#                html += "<li><strong>" + d.getProperty('cSmokepingGroup') + "</strong><ul>"
#
#            html += "<li>"
#            html += "<a target='_blank' href='" + d.zSmokepingPublicUrl + "smokeping.cgi?target="
#            html += d.zSmokepingTarget.replace('/', '.') + "'>" + d.getDeviceName() + "</a>"
#            html += "<img width='95%' src='/zport/fetchImage?url=" + d.zSmokepingPrivateUrl
#            html += "images/" + d.zSmokepingTarget + "_mini.png'/>"
#            html += "</li>"
#
#
#            prev_smokeping_group = d.getProperty('cSmokepingGroup')

    orgs = sorted(self.dmd.Groups.Smokeping.getSubOrganizers(), key=lambda o:(o.id).upper())
    o = None
    for o in orgs:
      if o != None:
        html += "</ul></li>"
      org_name = "/%s/%s" %(o.__primary_parent__.id, o.id)
      html += "<li><strong>" + org_name + "</strong><ul>"

      dvs = sorted(o.getSubDevices(), key=lambda d:d.id)
      for d in dvs:
            html += "<li>"
            html += "<a target='_blank' href='" + d.zSmokepingPublicUrl + "smokeping.cgi?target="
            html += d.zSmokepingTarget.replace('/', '.') + "'>" + d.getDeviceName() + "</a>"
            html += "<img width='95%' src='/zport/fetchImage?url=" + d.zSmokepingPrivateUrl
            html += "images/" + d.zSmokepingTarget + "_mini.png'/>"
            html += "</li>"

    html += "</ul></div></body></html>"

    REQUEST.RESPONSE.setHeader('Content-Type','text/html')
    return html

def createSample(self, REQUEST=None):
    user = getSecurityManager().getUser().getUserName()
    if user == 'Anonymous User':
        raise Unauthorized("Unauthorized")

    html = "<html><body>Hello world ok? from sampleSample</body></html>"
    REQUEST.RESPONSE.setHeader('Content-Type','text/html')
    return html

from Products.ZenModel.ZentinelPortal import ZentinelPortal
ZentinelPortal.fetchImage = fetchImage
ZentinelPortal.createSPDashboard = createSPDashboard
ZentinelPortal.updateSPDevice = updateSPDevice
ZentinelPortal.createSample = createSample
