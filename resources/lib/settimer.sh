#! /bin/sh
#sleep 2
case "$1" in
	ACPI)
		if [ $2 -eq 0 ]; then
			rtcwake -m disable
		else			
			rtcwake -lt$2 -m no
		fi
	;;
	NVRAM)
		nvram-wakeup -C /etc/nvram-wakeup.conf --directisa -s $2
	;;
esac

