#!/bin/bash
# requires: xmlstarlet

PLANS_XMLFILE="/etc/xen/shell/gt-reimage/plans.xml"

# Print available plans
plans=($(xmlstarlet sel -t -m '/catalog/group/plan' -v '../@name' -o '-'  -v 'name' -n $PLANS_XMLFILE))

choice=
while [ -z $choice ] || [ $choice == "l" ]; do
	[ -n $2 ] && choice=$2
	[ -z $2 ] &&
		read -p "Plan Choice ('l' to list): " choice

        if [ $choice == "l" ]; then
                echo ${plans[@]}
                continue
        fi

        choice=`echo "$choice" | tr '/[:upper:]/' '/[:lower:]/'`
        for a in ${plans[@]}; do
                # only break if the choice is acceptable
                [ "$a" == "$choice" ] && echo "Choose $a." && dobreak=1
        done
        [ -z $dobreak ] && choice='l' # this is enough to force a re-prompt
done

Group=`echo "$choice" | cut -d- -f1`
Size=`echo "$choice" | cut -d- -f2`

# Get details of selected plan
eval `xmlstarlet sel -t -m "/catalog/group[@name='${Group}']/plan" -i "name='${Size}'" -o 'Memory=' -v 'memory' -n -o 'Disk=' -v 'disk' -n -o 'Swap=' -v 'swap' $PLANS_XMLFILE`

#cat <<EOF
# Plan = ${Group}, ${Size}
# Memory = ${Memory}
# Disk = ${Disk}
# Swap = ${Swap}
#EOF

export Group Size Memory Disk Swap
