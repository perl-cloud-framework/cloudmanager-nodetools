[ -n $3 ] && IPAddress=$3
[ -z $3 ] &&
	read -p "IP Address: " IPAddress 
[ -z "$IPAddress" ] && exit 1

[ -n $4 ] && IPCIDR=$4
[ -z $4 ] &&
	read -p "IP Address Netmask: " IPCIDR
[ -z "$IPCIDR" ] && exit 1

[ -n $5 ] && IPGWAddress=$5
[ -z $5 ] &&
	read -p "IP Gateway Address: " IPGWAddress 
[ -z "$IPGWAddress" ] && exit 1
