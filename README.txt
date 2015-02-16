Installation Notes for PVR-Manager:


  I. NOTE: THIS ADDON USE ACPI-WAKEUP AS DEFAULT. IF YOU WISH TO USE ANOTHER
     METHOD (E.G. NVRAM-WAKEUP) YOU HAVE TO IMPLEMENT/INSTALL THE NEEDED MODULES !!!
     FOR DETAILS LOOK INTO ~/.kodi/addons/service.hts.pvrmanager/resources/lib/settimer.sh

 II. THE (THIS) README USES XBMC AS THE DEFAULT USERNAME. IF XBMC IS RUNNING
     WITH A DIFFERENT USERNAME, CHANGE ALL '/home/xbmc/' TO '/home/<yourusername>/' IN
     PATHNAMES.

III. CREATE A ACCOUNT FOR XBMC IN TVHEADEND WITH FULL ACCESS. USE USERNAME/PASSWORD
     INSIDE THE SETUP OF THIS ADDON.

 IV. Make shure that your mainboard supports ACPI-Wakeup or at least NVRAM-Wakeup
     and set it up properly!
     
1. Install this Addon from ZIP or if this fails copy the unpacked package
   to /home/xbmc/.kodi/addons
2. Change group/owner of settimer.sh and make it executable

[CODE]
	cd /home/xbmc/.kodi/addons/service.hts.pvrmanager/resources/lib/
	sudo chown xbmc settimer.sh
	sudo chgrp xbmc settimer.sh
	sudo chmod 755 settimer.sh
[/CODE]

3. Make possible settimer.sh runs under root/sudo privileges without password

[CODE]
	sudo visudo
[/CODE]

add below:

### XBMC specific configuration ###
# XBMC

[CODE]
	Cmnd_Alias PVR_CMDS = /home/xbmc/.kodi/addons/service.hts.pvrmanager/resources/lib/*.sh
[/CODE]

for XBMCLive (Ubuntu 10.04):

append at last line 'PVR_CMDS' (for example):
[CODE]
	xbmc ALL=NOPASSWD: SHUTDOWN_CMDS, MOUNT_CMDS, PVR_CMDS # XBMC
[/CODE]

for XBMCBuntu (Ubuntu 11.10/12.04) add following line

[CODE]
	xbmc ALL=NOPASSWD: PVR_CMDS
[/CODE]

4. Change your remote.xml to point the pvrmanager-addon when "Power" on remote is pressed.
   If you don't have a remote control you can also define a special key on your keyboard as
   power button (here as example F12)

create a remote.xml if it doesn't exists
[CODE]
	sudo mkdir /home/xbmc/.kodi/userdata/keymaps
	cd /home/xbmc/.kodi/userdata/keymaps
	sudo nano remote.xml
[/CODE]

and copy/paste following into the editor
[CODE]
	<keymap>
	  <global>
        <keyboard>
          <f12>XBMC.RunScript(service.hts.pvrmanager,shutdown)</f12>
        </keyboard>
	    <remote>
	      <power>XBMC.RunScript(service.hts.pvrmanager,shutdown)</power>
	    </remote>
	  </global>
	</keymap>
[/CODE]

5. Enjoy!

Please send Comments and Bugreports to hellyrulez@home.nl

