#! /bin/sh
#sleep 2
case "$1" in
	ACPI)
		if [ $2 -eq 0 ]; then
			rtcwake -m disable
		else	
			if [ -z $3 ]; then
				Clk="LOCAL"
			else
				Clk=$3
			fi
			case "$Clk" in
				LOCAL)		
					rtcwake -lt$2 -m no
				;;
				UTC)
					rtcwake -ut$2 -m no
				;;
			esac
		fi
	;;
	NVRAM)
		nvram-wakeup -C /etc/nvram-wakeup.conf --directisa -s $2
	;;
esac

