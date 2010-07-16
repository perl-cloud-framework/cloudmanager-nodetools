# Lets find out what the end-user wants..
[ -n $1 ] && Guestname=$1
[ -z $Guestname ] &&
	read -p "Guest Name: " Guestname
[ -z "$Guestname" ] && exit 1
