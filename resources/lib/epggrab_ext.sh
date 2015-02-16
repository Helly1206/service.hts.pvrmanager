#! /bin/sh
#
# Please place your command line for grabbing epg-data from external provider here
# Make sure all grabbers are configured properly and choose the appropriate socket
# of tvheadend!
#
# More information about XMLTV: http://wiki.xmltv.org/index.php/Main_Page
# XMLTV Project Page: http://sourceforge.net/projects/xmltv/files/
#
# Provider: epgdata.com
#tv_grab_eu_epgdata --days=4 | nc -w 5 -U /home/kodi/.hts/tvheadend/epggrab/pyepg.sock &
#
# Provider: Egon zappt (german)
#tv_grab_eu_egon --days=4 | nc -w 5 -U /home/kodi/.hts/tvheadend/epggrab/pyepg.sock &
exit 0
