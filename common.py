# -*- coding: utf-8 -*-
#########################################################
# SCRIPT  : common.py                                   #
#           Common functions for PVR-Manager            #
#           I. Helwegen 2015                            #
#########################################################

####################### IMPORTS #########################
from __future__ import division
from builtins import str
from past.utils import old_div
import os, subprocess
import xbmc, xbmcaddon, xbmcgui
import time, datetime
#########################################################

####################### GLOBALS #########################
# shutdown methods
CMD_NONE      = 0
CMD_SHUTDOWN  = 1
CMD_SUSPEND   = 2
CMD_HIBERNATE = 3 
CMD_SENDMAIL  = 4

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__datapath__ = xbmc.translatePath(os.path.join('special://temp/', __addonname__))
__logfile__ = os.path.join(__datapath__, __addonname__ + '.log')
__shutdownaction__ = __addon__.getSetting('shutdown_action')

IconStop = xbmc.translatePath(os.path.join(__path__, 'resources', 'media', 'stop.png'))
IconError = xbmc.translatePath(os.path.join(__path__, 'resources', 'media', 'error.png'))
IconSchedule = xbmc.translatePath(os.path.join(__path__, 'resources', 'media', 'schedule.png'))

# parameters
PID = 'pid'
CMD = 'cmd'
MSG = 'message'
MSGCNT = 'mescount'

OSD = xbmcgui.Dialog()

__parameterwindow__ = 10000
#########################################################

#########################################################
# Functions : Local                                     #
#########################################################
def num(s):
    try:
        return int(s)
    except ValueError:
        return 0

def setParam(param, value):
    xbmcgui.Window(__parameterwindow__).setProperty(__addonname__ + '_' + param, value)

def getParam(param):
    return xbmcgui.Window(__parameterwindow__).getProperty(__addonname__ + '_' + param)

def clearParam(param):
    xbmcgui.Window(__parameterwindow__).clearProperty(__addonname__ + '_' + param)

def incParam(param):
    val = num(getParam(param))
    val += 1
    setParam(param,str(val))
#########################################################

#########################################################
# Functions : Global                                    #
#########################################################
def getProcessPID(process):
    _syscmd = subprocess.Popen(['pidof','-x', process], stdout=subprocess.PIPE)
    PID = _syscmd.stdout.read().strip()
    return PID if PID > 0 else False

# check for PID, if no PID available, user or system has
# powered on the system at first time (_isPID = false)
def isPID(setPIDparam=True):
    _isPID = False
    pidofXBMC = str(getProcessPID('kodi.bin'))
    # KODI
    if not pidofXBMC: pidofXBMC = str(getProcessPID('xbmc.bin'))
    if num(getParam(PID)) == 0:
        if setPIDparam:
            setParam(PID,pidofXBMC)
    else:
        pidofVar = getParam(PID)
        if pidofVar == pidofXBMC:
            _isPID = True
        elif setPIDparam:
            setParam(PID,pidofXBMC)
    return _isPID

def delPID():
    clearParam(PID)

def getCommand():
    return num(getParam(CMD))

def setCommand(methd):
    if methd == CMD_NONE:
        clearParam(CMD)
    else:
        setParam(CMD,str(methd))

def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO):
    OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon)

def dialogOK(header, message):
    OSD.ok(header.encode('utf-8'), message.encode('utf-8'))

# Change this one later to include ok button
def dialogProgress(title, message, duration):
    __bar = 0
    __percent = 0

    pb = xbmcgui.DialogProgress()
    pb.create(title, message % (duration))
    pb.update(__percent)

    # actualize progressbar
    while __bar < duration and not pb.iscanceled():
        __bar += 1
        __percent = int(old_div(__bar * 100, duration))
        pb.update(__percent, message % (duration - __bar))
        xbmc.sleep(1000)
    pb.close()
    return pb.iscanceled()

def writeLog(message, level=xbmc.LOGNOTICE, forcePrint=False):
    if getParam(MSG) == message and not forcePrint:
        incParam(MSGCNT)
        return
    else:
        try:
            if not os.path.exists(__datapath__): os.makedirs(__datapath__)
            if not os.path.isfile(__logfile__):
                __f = open(__logfile__, 'w')
            else:
                __f = open(__logfile__, 'a')
            if num(getParam(MSGCNT)) > 0:
                __f.write('%s: >>> Last message repeated %s time(s)\n' % (
                    datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'), num(getParam(MSGCNT))))
            setParam(MSG, message)
            clearParam(MSGCNT)
            __f.write('%s: %s\n' % (datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'), message.encode('utf-8')))
            __f.close()
        except Exception as e:
            xbmc.log('%s: %s' % (__addonname__, e), xbmc.LOGERROR)
        xbmc.log('%s: %s' % (__addonname__, message.encode('utf-8')), level)    

def getShutdownAction():
    methd = CMD_SHUTDOWN # default shutdown
    if __shutdownaction__ == "Suspend": methd = CMD_SUSPEND
    if __shutdownaction__ == "Hibernate": methd = CMD_HIBERNATE
    return methd
#########################################################
