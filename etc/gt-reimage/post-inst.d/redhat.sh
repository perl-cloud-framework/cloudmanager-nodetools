chroot /mnt/${guestname} /bin/bash <<-EOF
	mkdir /proc
	mkdir /sys
	mkdir /dev/pts

	cd dev
	MAKEDEV console null zero random sda ptmx
	/bin/mknod xvc0 c 204 191

	usermod -p '$PasswdHash' root

	# Generate unique host keys
	ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key
	ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key

        # Install modules
        cd /lib/modules
        #wget ftp://ftp.grokthis.net/pub/linux/modules/latest-modules-linux-xen.tar.bz2
        #tar Cjxf /lib/modules/ latest-modules-linux-xen.tar.bz2
        kernelrel=\$(uname -r)
        ( file /sbin/init | grep 32-bit ) && ARCH="i386" || ARCH="amd64"
        wget -O - \
                ftp://ftp.grokthis.net/pub/linux/modules/modules-\${kernelrel}-\${ARCH}.tar.bz2 |
                tar jCx /lib/modules/ &&
                echo "Modules Installed." ||
                echo "Module installation failed."

	# Disable unnecessary default services
	for service in \$(cat <<EOF
	smartd
	atd
	acpid
	sendmail
	autofs
	pcscd
	messagebus
	mdmonitor
	mcstrans
	irqbalance
	cpuspeed
	netfs
	anacron
	gpm
	bluetooth
	sendmail
	rpcbind
	haldaemon
	nfslock
	rpcidmapd
	rpcgssd
	yum-updatesd
	EOF); do echo "Disabling service \$service"; /sbin/chkconfig --level 3 \$service off; done

	/usr/bin/yum -y install udev &
	sleep 30
	kill -9 %1
EOF
cp /root/skel/ifcfg-eth0 /mnt/${guestname}/etc/sysconfig/network-scripts/
echo "xvc0" >> /mnt/${guestname}/etc/securetty

sed "s/%{IPADDRESS}/$IPADDRESS/g; \
	s/%{IPNETMASK}/$IPNETMASK/g; \
	s/%{IPGATEWAY}/$IPGATEWAY/g; \
	" /root/skel/ifcfg-eth0 > \
	/mnt/${guestname}/etc/sysconfig/network-scripts/ifcfg-eth0

cp /mnt/${guestname}/etc/selinux/config /mnt/${guestname}/etc/selinux/config~
sed "s/SELINUX=enabled/SELINUX=disabled/" /mnt/${guestname}/etc/selinux/config~ > /mnt/${guestname}/etc/selinux/config

#vim /mnt/${guestname}/etc/sysconfig/network-scripts/ifcfg-eth0
chattr +i /mnt/${guestname}/etc/sysconfig/network-scripts/ifcfg-eth0

# Fix the inittab, remove useless gettys
sed '/mingetty tty[2-6]/{ s/^/#/; }' /mnt/${guestname}/etc/inittab > /mnt/${guestname}/etc/inittab.new
sed 's/tty1/xvc0/;' /mnt/${guestname}/etc/inittab.new > /mnt/${guestname}/etc/inittab
chmod 644 /mnt/${guestname}/etc/inittab

