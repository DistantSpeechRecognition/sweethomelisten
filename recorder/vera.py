import webbrowser
import sys

import httplib
import urllib
import re
def vera(command):

  #command= 0
  print command
  if command == 1:
    #Turn on a light:
    url= "http://192.168.81.1:3480/data_request?id=action&output_format=xml&DeviceNum=6&serviceId=urn:upnp-org:serviceId:SwitchPower1&action=SetTarget&newTargetValue=1"
  elif command == 2:
    #Turn off a light:
    url= "http://192.168.81.1:3480/data_request?id=action&output_format=xml&DeviceNum=6&serviceId=urn:upnp-org:serviceId:SwitchPower1&action=SetTarget&newTargetValue=0"
  elif command == 3:
    #Set a dimmable light to a higher level%:
    urlstatus= "http://192.168.81.1:3480/data_request?id=sdata&DeviceNum=7"
    status= urllib.urlopen(urlstatus)
    status= status.read()
    levelindex= status.find("level")
    temp= status[levelindex:levelindex+13]

    s = re.search("\d+", temp)
    level = s.group(0)
    if level=='':
        level=0
    print "temp="+temp
    print "level="+level

    newlevel= min(100, int(level) + 40)
    #print(newlevel)
    # url= "http://192.168.81.1:3480/data_request?id=action&output_format=json&DeviceNum=7&serviceId=urn:upnp-org:serviceId:Dimming1&action=SetLoadLevelTarget&newLoadLevelTarget=30"
    url= "http://192.168.81.1:3480/data_request?id=lu_action&DeviceNum=7&serviceId=urn:upnp-org:serviceId:Dimming1&action=SetLoadLevelTarget&newLoadlevelTarget=" + `newlevel`
  elif command == 4:
    #Set a dimmable light to a lower level%:
    urlstatus= "http://192.168.81.1:3480/data_request?id=sdata&DeviceNum=7"
    status= urllib.urlopen(urlstatus)
    status= status.read()
    levelindex= status.find("level")
    temp= status[levelindex:levelindex+13]

    s = re.search("\d+", temp)
    level = s.group(0)
    print "temp="+temp
    print "level="+level
    if level=='':
        level=100

    newlevel= max(0, int(level) - 40)
    #print(newlevel)
    # url= "http://192.168.81.1:3480/data_request?id=action&output_format=json&DeviceNum=7&serviceId=urn:upnp-org:serviceId:Dimming1&action=SetLoadLevelTarget&newLoadLevelTarget=30"
    url= "http://192.168.81.1:3480/data_request?id=lu_action&DeviceNum=7&serviceId=urn:upnp-org:serviceId:Dimming1&action=SetLoadLevelTarget&newLoadlevelTarget=" + `newlevel`
  elif command == 5:
    #anavei entelws to fws
    url= "http://192.168.81.1:3480/data_request?id=lu_action&DeviceNum=7&serviceId=urn:upnp-org:serviceId:Dimming1&action=SetLoadLevelTarget&newLoadlevelTarget=100"
  elif command == 6:
    #svinei ntip entelws to fws
    url= "http://192.168.81.1:3480/data_request?id=lu_action&DeviceNum=7&serviceId=urn:upnp-org:serviceId:Dimming1&action=SetLoadLevelTarget&newLoadlevelTarget=0"
  else:
    url= "http://www.gmail.com"

  #webbrowser.open(url)
  print url
  urllib.urlopen(url)

  #status of a specific device
 # http://192.168.81.1:3480/data_request?id=sdata&output_format=xml&DeviceNum=7
