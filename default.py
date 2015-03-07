# -*- coding: utf-8 -*-
#########################################################
# SERVICE : default.py                                  #
#           PVR-Manager service                         #
#           I. Helwegen 2015                            #
#########################################################

####################### IMPORTS #########################
import os, platform, subprocess
import socket
import re
import random
import xbmc, xbmcaddon, xbmcgui
import time, datetime
import urllib2
from xml.dom import minidom
import smtplib
from email.message import Message

import common
#########################################################

####################### GLOBALS #########################
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__version__ = __addon__.getAddonInfo('version')
__LS__ = __addon__.getLocalizedString

SETTIMER = xbmc.translatePath(os.path.join(__path__, 'resources', 'lib', 'settimer.sh'))
EXTGRABBER = xbmc.translatePath(os.path.join(__path__, 'resources', 'lib', 'epggrab_ext.sh'))

CYCLE = 15    # polling cycle
IDLECYCLE = 1 # polling cycle when idle
TVHPORT = ':9981/status.xml'

PLATFORM_OE = True if ('OPENELEC' in ', '.join(platform.uname()).upper()) else False
HOST = socket.gethostname()

# binary Flags

isPWR = 0b10000
isNET = 0b01000
isPRG = 0b00100
isREC = 0b00010
isEPG = 0b00001
isUSR = 0b00000
#########################################################    

#########################################################
# Class : Manager                                       #
#########################################################
### MAIN CLASS
class Manager(object):
    def __init__(self):

        self.__conn_established = None
        self.__xml = None
        self.__bState = None
        self.__recTitles = []
        self.__rndProcNum = random.randint(1, 1024)
        self.__wakeUp = None
        self.__wakeUpUT = None
        self.__wakeUpReason = None
        self.__wakeUpMessage = ''
        self.__excluded_ports = ''
        self.__ScreensaverActive = None
        self.__windowID = None

        self.getSettings()
        self.establishConn()

    ### read addon settings

    def getSettings(self):
        self.__prerun = int(re.match('\d+', __addon__.getSetting('margin_start')).group())
        self.__postrun = int(re.match('\d+', __addon__.getSetting('margin_stop')).group())
        self.__wakeup = __addon__.getSetting('wakeup_method')
        self.__counter = int(re.match('\d+', __addon__.getSetting('notification_counter')).group())
        self.__nextsched = True if __addon__.getSetting('next_schedule').upper() == 'TRUE' else False

        # TVHeadend server
        self.__server = __addon__.getSetting('TVH_URL')
        self.__user = __addon__.getSetting('TVH_USER')
        self.__pass = __addon__.getSetting('TVH_PASS')
        self.__maxattempts = int(__addon__.getSetting('conn_attempts'))
	self.__sleepbetweenattempts__ = int(re.match('\d+', __addon__.getSetting('conn_delay')).group()) * 1000

        # check for network activity
        self.__network = True if __addon__.getSetting('network').upper() == 'TRUE' else False

        # calculate exluded ports
        _np = __addon__.getSetting('excluded_ports')
        if _np:
            _np = _np.replace(',', ' ')
            _np = _np.join(' '.join(line.split()) for line in _np.splitlines())
            for line in _np.split(): self.__excluded_ports += (' | grep -v ":%s"' % (line))

        # check for post processors
        self.__pp_enabled = True if __addon__.getSetting('postprocessor_enable').upper() == 'TRUE' else False
        _pp = __addon__.getSetting('processor_list')

        # transform possible userinput from e.g. 'p1, p2,,   p3 p4  '
        # to a list like this: ['p1','p2','p3','p4']
        _pp = _pp.replace(',', ' ')
        _pp = _pp.join(' '.join(line.split()) for line in _pp.splitlines())
        self.__pp_list = _pp.split(' ')

        # mail settings
        self.__notification = True if __addon__.getSetting('smtp_sendmail').upper() == 'TRUE' else False
        self.__smtpserver = __addon__.getSetting('smtp_server')
        self.__smtpuser = __addon__.getSetting('smtp_user')
        self.__smtppass = __addon__.getSetting('smtp_passwd')
        self.__smtpenc = __addon__.getSetting('smtp_encryption')
        self.__smtpfrom = __addon__.getSetting('smtp_from')
        self.__smtpto = __addon__.getSetting('smtp_to')
        self.__charset = __addon__.getSetting('charset')

        # EPG-Wakeup settings
        self.__epg_interval = int(__addon__.getSetting('epgtimer_interval'))
        self.__epg_time = int(__addon__.getSetting('epgtimer_time'))
        self.__epg_duration = int(re.match('\d+', __addon__.getSetting('epgtimer_duration')).group())
        self.__epg_grab_ext = True if __addon__.getSetting('epg_grab_ext').upper() == 'TRUE' else False

    # Connect to TVHeadend and establish connection (log in))

    def establishConn(self):
        self.__conn_established = False
        while self.__maxattempts > 0:
            try:
                pwd_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                pwd_mgr.add_password(None, self.__server + TVHPORT, self.__user, self.__pass)
                handle = urllib2.HTTPBasicAuthHandler(pwd_mgr)
                opener = urllib2.build_opener(handle)
                opener.open(self.__server + TVHPORT)
                urllib2.install_opener(opener)
                self.__conn_established = True
                #common.writeLog('Connection to %s established' % (self.__server))
                break
            except Exception, e:
                common.writeLog('%s' % (e), xbmc.LOGERROR)
                self.__maxattempts -= 1
                common.writeLog('Remaining connection attempts to %s: %s' % (self.__server, self.__maxattempts))
                xbmc.sleep(5000)
                continue

        if not self.__conn_established:
            common.notifyOSD(__LS__(30030), __LS__(30031), common.IconError)
            xbmc.sleep(6000)

    def getShutdown(self,prevmethd=common.CMD_NONE):
        methd = common.getCommand()
        if (methd == common.CMD_SENDMAIL):
            self.sendTestMail()
            self.delShutdown()
            methd = common.CMD_NONE
        else:
	    if (methd != prevmethd) and self.__bState:
                common.writeLog('Powerbutton is pressed but shutdown not allowed now')
                if (self.__bState & isREC):
                    common.notifyOSD(__LS__(30015), __LS__(30020), common.IconStop)  # Notify 'Recording in progress'
                elif (self.__bState & isEPG):
                    common.notifyOSD(__LS__(30015), __LS__(30021), common.IconStop)  # Notify 'EPG-Update'
                elif (self.__bState & isPRG):
                    common.notifyOSD(__LS__(30015), __LS__(30022), common.IconStop)  # Notify 'Postprocessing'
                elif (self.__bState & isNET):
                    common.notifyOSD(__LS__(30015), __LS__(30023), common.IconStop)  # Notify 'Network active'
        return methd

    def delShutdown(self):
        common.setCommand(common.CMD_NONE)

    # send email to user to inform about a successful completition

    def deliverMail(self, message):
        if self.__notification:
            try:
                __port = {'None': 25, 'SSL/TLS': 465, 'STARTTLS': 587}
                __s_msg = Message()
                __s_msg.set_charset(self.__charset)
                __s_msg.set_payload(message, charset=self.__charset)
                __s_msg["Subject"] = __LS__(30046) % (HOST)
                __s_msg["From"] = self.__smtpfrom
                __s_msg["To"] = self.__smtpto

                if self.__smtpenc == 'STARTTLS':
                    __s_conn = smtplib.SMTP(self.__smtpserver, __port[self.__smtpenc])
                    __s_conn.ehlo()
                    __s_conn.starttls()
                elif self.__smtpenc == 'SSL/TLS':
                    __s_conn = smtplib.SMTP_SSL(self.__smtpserver, __port[self.__smtpenc])
                    __s_conn.ehlo()
                else:
                    __s_conn = smtplib.SMTP(self.__smtpserver, __port[self.__smtpenc])
                __s_conn.login(self.__smtpuser, self.__smtppass)
                __s_conn.sendmail(self.__smtpfrom, self.__smtpto, __s_msg.as_string())
                __s_conn.close()
                common.writeLog('Mail delivered to %s.' % (self.__smtpto))
                return True
            except Exception, e:
                common.writeLog('%s' % (e), xbmc.LOGERROR)
                common.writeLog('Mail could not be delivered. Check your settings.', xbmc.LOGERROR)
                return False
        else:
            common.writeLog('"%s" completed, no Mail delivered.' % (message))
            return True

    def sendTestMail(self):
        setup_ok = self.deliverMail(__LS__(30065) % (HOST))
        if setup_ok:
            common.dialogOK(__LS__(30066), __LS__(30068) % (__addon__.getSetting('smtp_to')))
        else:
            common.dialogOK(__LS__(30067), __LS__(30069) % (__addon__.getSetting('smtp_to')))

    def setShutdownNotification(self,methd=common.CMD_NONE):
	if methd == common.CMD_SHUTDOWN: 
		common.notifyOSD(__LS__(30010), __LS__(30012), common.IconSchedule )
		common.writeLog('Shutdown action: %s' % __LS__(30012))
	elif methd == common.CMD_SUSPEND: 
		common.notifyOSD(__LS__(30010), __LS__(30013), common.IconSchedule )
		common.writeLog('Shutdown action: %s' % __LS__(30013))
	elif methd == common.CMD_HIBERNATE: 
		common.notifyOSD(__LS__(30010), __LS__(30014), common.IconSchedule )
		common.writeLog('Shutdown action: %s' % __LS__(30014))

    def readXML(self, xmlnode):
        nodedata = []
        while self.__conn_established:
            try:
                __f = urllib2.urlopen(self.__server + TVHPORT) #, timeout=mytimeout
                __xmlfile = __f.read()
                self.__xml = minidom.parseString(__xmlfile)
                __f.close()
                nodes = self.__xml.getElementsByTagName(xmlnode)
                if nodes:
                    for node in nodes:
                        nodedata.append(node.childNodes[0].data)
                break
            except Exception, e:
                common.writeLog("Could not read from %s" % (self.__server), xbmc.LOGERROR)
                self.establishConn()
        return nodedata

    def getSysState(self, bNet=True):
        self.__bState = isUSR

        # Check for current recordings. If there a 'status' tag,
        # and content is "Recording" current recording is in progress
        nodedata = self.readXML('status')
        if nodedata and 'Recording' in nodedata: self.__bState |= isREC

        # Check for future recordings. If there is a 'next' tag,
        # then a future recording is happening
        nodedata = self.readXML('next')
        if nodedata and int(nodedata[0]) < (self.__prerun + self.__postrun) \
                or (self.__wakeup == "NVRAM" and int(nodedata[0]) < 11): self.__bState |= isREC

        # Check if system started up because of actualizing EPG-Data
        if self.__epg_interval > 0:
            __curTime = datetime.datetime.now()
            __epgTime = (__curTime + datetime.timedelta(days=int(__curTime.strftime('%j')) % self.__epg_interval)).replace(hour=self.__epg_time, minute=0, second=0)
            if __epgTime < __curTime < __epgTime + datetime.timedelta(minutes=self.__epg_duration): self.__bState |= isEPG

        # Check if any postprocess is running
        if self.__pp_enabled:
            for proc in self.__pp_list:
                procpid = common.getProcessPID(proc)
                if procpid: self.__bState |= isPRG

        # Check for active network connection(s)
        if self.__network and bNet:
            nwc = subprocess.Popen('netstat -ano | grep ESTABLISHED | grep -v "127.0.0.1" | grep -v "off" %s' % self.__excluded_ports,
                                   stdout=subprocess.PIPE, shell=True).communicate()
            nwc = nwc[0].strip()
            if nwc and len(nwc.split("\n")) > 0: self.__bState |= isNET

        # Check if screensaver is running
        self.__ScScreensaverActive = xbmc.getCondVisibility('System.ScreenSaverActive')

    def calcNextSched(self):

        __WakeUpUTRec = 0
        __WakeUpUTEpg = 0
        __WakeEPG = 0
        __curTime = datetime.datetime.now()

        nodedata = self.readXML('next')
        if nodedata:
            self.__wakeUp = (__curTime + datetime.timedelta(minutes=int(nodedata[0]) - self.__prerun)).replace(second=0)
            __WakeUpUTRec = int(time.mktime(self.__wakeUp.timetuple()))
        else:
            common.writeLog('No recordings to schedule')

        if self.__epg_interval > 0:
            __WakeEPG = (__curTime + datetime.timedelta(days=int(__curTime.strftime('%j')) % self.__epg_interval)).replace(hour=self.__epg_time, minute=0, second=0)
            if __curTime > __WakeEPG:
                __WakeEPG = (__curTime + datetime.timedelta(days=self.__epg_interval) -
                             datetime.timedelta(days=int(__curTime.strftime('%j')) % self.__epg_interval)).replace(hour=self.__epg_time, minute=0, second=0)
            __WakeUpUTEpg = int(time.mktime(__WakeEPG.timetuple()))

        if __WakeUpUTRec > 0 or __WakeUpUTEpg > 0:

            if __WakeUpUTRec <= __WakeUpUTEpg:
                if __WakeUpUTRec > 0:
                    self.__wakeUpUT = __WakeUpUTRec
                    self.__wakeUpReason = 0
                elif __WakeUpUTEpg > 0:
                    self.__wakeUpUT = __WakeUpUTEpg
                    self.__wakeUp = __WakeEPG
                    self.__wakeUpReason = 1
            elif __WakeUpUTRec > __WakeUpUTEpg:
                if __WakeUpUTEpg > 0:
                    self.__wakeUpUT = __WakeUpUTEpg
                    self.__wakeUp = __WakeEPG
                    self.__wakeUpReason = 1
                elif __WakeUpUTRec > 0:
                    self.__wakeUpUT = __WakeUpUTRec
                    self.__wakeUpReason = 0
            self.__wakeUpMessage = '\n%s %s' % (
                __LS__(30024), __LS__(30018 + self.__wakeUpReason) % (self.__wakeUp.strftime('%d.%m.%Y %H:%M')))
            return True
        else:
            self.__wakeUpUT = 0
            return False

    def setWakeup(self, methd):
        if methd == common.CMD_NONE:
            return False

        if self.calcNextSched():
            __task = ['Recording', 'EPG-Update']
            common.writeLog('Wakeup for %s by %s at %s' % (__task[self.__wakeUpReason], self.__wakeup,  self.__wakeUp.strftime('%d.%m.%y %H:%M')))
            if self.__nextsched:
                common.notifyOSD(__LS__(30017),
                               __LS__(30018 + self.__wakeUpReason) % (self.__wakeUp.strftime('%d.%m.%Y %H:%M')),
                               common.IconSchedule)

        common.writeLog('Instruct the system to shut down')
	self.setShutdownNotification(methd)

        if PLATFORM_OE:
            os.system('%s %s %s' % (SETTIMER, self.__wakeup, self.__wakeUpUT))
        else:
            os.system('sudo %s %s %s' % (SETTIMER, self.__wakeup, self.__wakeUpUT))

        self.delShutdown()

        if methd == common.CMD_SUSPEND:
            xbmc.suspend()
            return False
        elif methd == common.CMD_HIBERNATE:
            xbmc.hibernate()
            return False
        else:
            common.delPID()
            xbmc.shutdown()
            return True

    ####################################### START MAIN SERVICE #####################################

    def start(self):

        if common.isPID():
            common.writeLog('Attempting to start service while service already running, quit ....', xbmc.LOGERROR)
            #common.notifyOSD(__LS__(30030), __LS__(30031), common.IconError)
            return

	common.writeLog('Starting service (%s)' % (self.__rndProcNum))

        self.getSysState(False)

        if self.__bState:
            if (self.__bState & isEPG) and self.__epg_grab_ext and os.path.isfile(EXTGRABBER):
                common.writeLog('Starting script for grabbing external EPG')
                #
                # ToDo: implement startup of external script (epg grabbing)
                #
                try:
                    os.system(EXTGRABBER)
                except Exception, e:
                    common.writeLog('Could not start external EPG-Grabber', xbmc.LOGERROR)
             
        bKillMain = False           
        bBtnElse = False
        bBtnPwr = common.CMD_NONE
        bWasInBusyLoop = False
        idle = xbmc.getGlobalIdleTime()
        counter = 0
        counts = CYCLE/IDLECYCLE

        ### START MAIN LOOP ###
        while (not xbmc.abortRequested) and (not bKillMain):
            time.sleep(IDLECYCLE)
            #idle += IDLECYCLE

            #check timeout possibilities !!!!, do this once in 15 loops !!!!!!!!!!
            if (counter >= counts):
                self.getSysState()
                counter = 0
            else:
                counter += 1

            # Check for power button
            bBtnPwr = self.getShutdown(bBtnPwr)
            #common.writeLog("Button %d" % (bBtnPwr))

            xbmcIdle = xbmc.getGlobalIdleTime()
            idle = xbmcIdle

            ### START BUSY LOOP ###
            while (not xbmc.abortRequested and self.__bState): # and not self.__bBtnElse):
                bWasInBusyLoop = True
                time.sleep(CYCLE)
                idle += CYCLE
                
                xbmcIdle = xbmc.getGlobalIdleTime()

                if idle - xbmcIdle > CYCLE:
                    # Button pressed
                    if (not bBtnElse): common.writeLog('User activity detected')
                    bBtnElse = True
                    #break

                # check outdated recordings
                nodedata = self.readXML('title')
                for item in nodedata:
                    if not item in self.__recTitles:
                        self.__recTitles.append(item)
                        common.writeLog('Recording of "%s" is/ becomes active' % (item))
                for item in self.__recTitles:
                    if not item in nodedata:
                        self.__recTitles.remove(item)
                        common.writeLog('Recording of "%s" has finished' % (item))
                        if not self.__recTitles: self.calcNextSched()
                        if not bBtnPwr:
                            self.deliverMail(__LS__(30047) % (HOST, item) + self.__wakeUpMessage)
                
                self.getSysState()
                bBtnPwr = self.getShutdown(bBtnPwr)

                if not self.__ScreensaverActive: self.__windowID = xbmcgui.getCurrentWindowId()

                common.writeLog('Service polling Net/Post/Rec/EPG: {0:04b}'.format(self.__bState))

            ### END BUSY LOOP ###

            if bWasInBusyLoop:
                bWasInBusyLoop = False
                if not self.__bState and (bBtnPwr != common.CMD_NONE):
                    common.writeLog('Display countdown message for %s secs' % (self.__counter))
                    # deactivate screensaver (if running), set progressbar and notify
                    if self.__ScreensaverActive and self.__windowID: xbmc.executebuiltin('ActivateWindow(%s)') % self.__windowID
                    if not common.dialogProgress(__LS__(30010), __LS__(30011), self.__counter):
                        bKillMain = self.setWakeup(bBtnPwr)
                    else:
                        common.writeLog('Countdown aborted by user')
                elif not self.__bState and (bBtnPwr == common.CMD_NONE) and not bBtnElse:
                    common.writeLog('Service(%s) was running without any user activity' % (self.__rndProcNum))
                    bKillMain = self.setWakeup(common.getShutdownAction())
            else: # Was not in busy loop
                if (bBtnPwr != common.CMD_NONE): bKillMain = self.setWakeup(bBtnPwr)

        ### END MAIN LOOP ###

        common.delPID()
        common.writeLog('Service(%s) finished' % (self.__rndProcNum))

        ##################################### END OF MAIN SERVICE #####################################
#########################################################

#########################################################
######################## MAIN ###########################
#########################################################
TVHMan = Manager()

#always check if manager is not already running, otherwise start manager
if not common.isPID(False):
    TVHMan.start()

    __p = platform.uname()

    common.writeLog('<<<')
    common.writeLog('              _\|:|/_        BYE BYE')
    common.writeLog('               (o -)')
    common.writeLog('------------ooO-(_)-Ooo----- V.%s on %s --' % (__version__, __p[1]))
    common.writeLog('<<<\n')
else:
    common.writeLog('Attempting to start service while service already running')

del TVHMan
#########################################################
