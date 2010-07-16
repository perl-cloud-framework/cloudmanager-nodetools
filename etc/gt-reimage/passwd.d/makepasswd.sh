# Securely generate a password and store it into variables
Passwd=`makepasswd --minchars=7 --maxchars=10 --crypt-md5 | sed 's/ \+/\t/;'`
PasswdHash=`cat <<EOF | cut -f2 
${Passwd}
EOF`
PasswdString=`cat <<EOF | cut -f1
${Passwd}
EOF`
#export PasswdHash PasswdString
