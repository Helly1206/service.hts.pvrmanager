# -*- coding: utf-8 -*-
#########################################################
# SCRIPT  : script.py                                   #
#           Script handling commands for PVR-Manager    #
#           I. Helwegen 2015                            #
#########################################################

####################### IMPORTS #########################
import sys
import xbmc, xbmcaddon
import re

import common
#########################################################

####################### GLOBALS #########################
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('id')
__LS__ = __addon__.getLocalizedString
__counter__ = int(re.match('\d+', __addon__.getSetting('notification_counter')).group())
#########################################################

#########################################################
# Function : setShutdown                                #
#########################################################
def setShutdown(command):
    if common.isPID(False):
        common.setCommand(command)
    else:
        common.writeLog('Service not running, performing normal shutdown action ...')
        common.notifyOSD(__LS__(30008),__LS__(30025),common.IconError)
        if command == common.CMD_SHUTDOWN:
            xbmc.shutdown()
        elif command == common.CMD_SUSPEND:
            xbmc.suspend()
        elif command == common.CMD_HIBERNATE:
            xbmc.hibernate()
        else:
            common.writeLog('Unable to perform action ...')
#########################################################

#########################################################
######################## MAIN ###########################
#########################################################
if len(sys.argv) > 1:
    s = sys.argv[1].lower()
    if s == 'checkmailsettings':
        common.writeLog('Send test E-Mail')
        setShutdown(common.CMD_SENDMAIL)
    elif s == "shutdown":
        common.writeLog('Powerbutton is pressed')
        setShutdown(common.CMD_SHUTDOWN)
    elif s == "suspend":
        common.writeLog('Powerbutton is pressed')
        setShutdown(common.CMD_SUSPEND)
    elif s == "hibernate":
        common.writeLog('Powerbutton is pressed')
        setShutdown(common.CMD_HIBERNATE)
    else: # remote
        common.writeLog('Powerbutton is pressed')
        setShutdown(common.getShutdownAction())
else:
    common.writeLog('Powerbutton is pressed')
    #Do a countdown with ok and cancel from script ....
    if not common.dialogProgress(__LS__(30008), __LS__(30009), __counter__):
        setShutdown(common.getShutdownAction())
    else:
        common.writeLog('Powerbutton canceled')
#########################################################
