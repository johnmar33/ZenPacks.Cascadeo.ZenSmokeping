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
    user = getSecurityManager().getUser().getUserName()

    if user == 'Anonymous User':
        raise Unauthorized("Unauthorized")

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
    outfile = open('/usr/local/zenoss/zenoss/log/event.log', 'a')
    outfile.write("%s and %s\n" %(url, new_url))
    outfile.close()

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


    # 04/02/2013 - temporary
    import os
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

    # temporary - josephson (05/20/2013)
    outfile = open('/usr/local/zenoss/zenoss/log/event.log', 'a')
    outfile.write(str(urls.keys()))
    outfile.close()
    # Fetch target dashboard webpage to trigger smokeping to create latest images
    for url in urls.keys():
        site = urllib2.urlopen(url)
            
    # Generate Dasboard for Zenoss
    html = html + "<html>"
    html = html + "<script type=\"text/javascript\" src=\"zport/jsDashboard\"></script>"
    html = html + "<body>"

    html = html + "<div id=\"zensmokeping_filter\">"
    html = html + "<input id=\"device_name\" name=\"device_name\" maxlength=\"32\" />"
    html = html + ("<button name=\"filter_device_btn\" id=\"filter_device_btn\" onclick=\"filter_device();\">Filter</button>")
    html = html + "</div>"
    html = html + "<div id=\"zensmokeping_dashboard\"><ul>"

    orgs = sorted(self.dmd.Groups.Smokeping.getSubOrganizers(), key=lambda o:(o.id).upper())
    o = None
    for o in orgs:
      # 04/02/2013 - get sub-devices first to prevent "blank" Smokeping Groups from being displayed
      dvs = sorted(o.getSubDevices(), key=lambda d:d.id)

      if len(dvs) > 0:
        if o != None:
          html += "</ul></li>"
        org_name = "/%s/%s" %(o.__primary_parent__.id, o.id)
        html += "<li><strong>" + org_name + "</strong><ul>"
  
        # replace spaces (trailing/leading/gitna)
        for d in dvs:
              html += "<li>"
              html += "<a target='_blank' href='" + d.zSmokepingPublicUrl.replace(' ', '') + "smokeping.cgi?target="
              html += d.zSmokepingTarget.replace('/', '.').replace(' ', '') + "'>" + d.getDeviceName() + "</a>"
              html += "<img width='95%' src='/zport/fetchImage?url=" + d.zSmokepingPrivateUrl.replace(' ', '')
              html += "images/" + d.zSmokepingTarget.replace(' ', '') + "_mini.png'/>"
              html += "</li>"
  
    html += "</ul></div></body></html>"

    REQUEST.RESPONSE.setHeader('Content-Type','text/html')
    return html

def createSample(self, REQUEST=None):
    """
    sample new zensmokeping ZenPack page
    """
    user = getSecurityManager().getUser().getUserName()
    if user == 'Anonymous User':
        raise Unauthorized("Unauthorized")

    html = "<html><body>Hello world ok? from createSample</body></html>"
    REQUEST.RESPONSE.setHeader('Content-Type','text/html')
    return html

def filterDevice(self, dev='/', REQUEST=None):
    """
    For device filtering
    """
    json_rs = {}
    rs = self.dmd.Devices._findDevice("*%s*" %(dev))
    if len(rs) == 0:
        json_rs = {'results': "NO RESULTS"}
    else:
        orgs = sorted(self.dmd.Groups.Smokeping.getSubOrganizers(), key=lambda o:(o.id).upper())
        o = None
        json_rs = {'results': [], 'groups': [] }
        # get organizers as well
        for o in orgs:
            row = {'parent_group': o.__primary_parent__.id, 'group': o.id, 'group_name': "/%s/%s" %(o.__primary_parent__.id, o.id)}
            json_rs['groups'].append(row)
        row = None
        for d in rs:
            if len(d.getObject().groups()) > 0:
              smokeping_group = "/%s/%s" %(d.getObject().groups()[0].__primary_parent__.id, d.getObject().groups()[0].id)
              row = {'device_id': d.getObject().id, 'device_name': d.getObject().getDeviceName(), 'zSmokepingTarget': d.getObject().zSmokepingTarget, 'zSmokepingPublicUrl': d.getObject().zSmokepingPublicUrl, 'zSmokepingPrivateUrl': d.getObject().zSmokepingPrivateUrl, 'smokeping_group': smokeping_group}
              json_rs['results'].append(row)

        json_rs['results'] = sorted(json_rs['results'], key=lambda o:o['smokeping_group'].upper())
    import json
    return json.dumps(json_rs)

def jsDashboard(self, REQUEST=None):
    """
    JS for the createSPDashboard Portlet
    """
    js_code = "function filter_device() {\n" \
    "var xmlHttp;\n" \
    "dev = document.getElementById('device_name').value; \n" \
    "url = \"zport/filterDevice?dev=\"+dev; \n" \
    "if (window.XMLHttpRequest) { \n" \
    "xmlHttp = new XMLHttpRequest(); \n" \
    "} else { \n" \
    "xmlHttp = new ActiveXObject(\"Microsoft.XMLHTTP\"); \n" \
    "} \n" \
    "xmlHttp.open(\"GET\", url, true); \n" \
    "xmlHttp.send(); \n" \
    "xmlHttp.onreadystatechange = function() { \n" \
    "\tif (xmlHttp.readyState == 4 && xmlHttp.status == 200) { \n" \
    "\t\tvar json = eval('(' + xmlHttp.responseText + ')'); \n" \
    "\t\tdashboard_div = document.getElementById('zensmokeping_dashboard'); \n" \
    "\t\tdashboard_div.innerHTML = \"\"; \n" \
    "\t\tcontent = \"\"; \n" \
    "\t\tprev_group = \"\"; // previous smokeping group handler \n" \
    "\t\tif (json.results.length > 0) content = content + \"<ul>\"; \n" \
    "\t\tfor (i = 0; i < json.results.length; i++) {\n" \
    "\t\t\tif(json.results[i].smokeping_group != prev_group) { \n" \
    "\t\t\t\tprev_group = json.results[i].smokeping_group; \n" \
    "\t\t\t\tif (prev_group != \"\") content = content + \"</ul>\"; \n" \
    "\t\t\t\tcontent = content + \"<li><strong>\" + json.results[i].smokeping_group + \"</strong></li><ul>\"; \n" \
    "\t\t\t} \n" \
    "\t\t\tcontent = content + \"<li><a target='_blank' href='\" + json.results[i].zSmokepingPublicUrl + \"smokeping.cgi?target=\" + json.results[i].zSmokepingTarget + \"'>\" + json.results[i].device_name + \"</a>\";  \n" \
    "\t\t\tcontent = content + \"<img width='95%' src='/zport/fetchImage?url=\" + json.results[i].zSmokepingPrivateUrl + \"images/\" + json.results[i].zSmokepingTarget + \"_mini.png' /></li>\"; \n" \
    "\t\t} \n" \
    "\t\tif (json.results.length > 0) content = content + \"</ul>\"; \n" \
    "\t\tdashboard_div.innerHTML += content; \n" \
    "\t} \n" \
    "} \n" \
    "}\n"
    return js_code

from Products.ZenModel.ZentinelPortal import ZentinelPortal
ZentinelPortal.fetchImage = fetchImage
ZentinelPortal.createSPDashboard = createSPDashboard
ZentinelPortal.updateSPDevice = updateSPDevice
ZentinelPortal.createSample = createSample
ZentinelPortal.filterDevice = filterDevice
ZentinelPortal.jsDashboard = jsDashboard
