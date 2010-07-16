sed 's/http:\/\/ftp.debian.org/ftp:\/\/ftp.grokthis.net\/mirrors/g' \
	/mnt/${guestname}/etc/apt/sources.list > \
	/mnt/${guestname}/etc/apt/sources.list.new

echo 'deb ftp://security.ubuntu.com/ubuntu hardy-security main restricted' >> \
	/mnt/${guestname}/etc/apt/sources.list.new

mv /mnt/${guestname}/etc/apt/sources.list.new \
	/mnt/${guestname}/etc/apt/sources.list

echo "xvc0" >> /mnt/${guestname}/etc/securetty
cp /root/skel/inittab /mnt/${guestname}/etc/

sed "s/%{IPADDRESS}/$IPADDRESS/g; \
	s/%{IPNETMASK}/$IPNETMASK/g; \
	s/%{IPGATEWAY}/$IPGATEWAY/g; \
	" /root/skel/interfaces > \
	/mnt/${guestname}/etc/network/interfaces	

test -f /mnt/${guestname}/etc/event.d/tty1 &&
sed 's/tty1/xvc0/' /mnt/${guestname}/etc/event.d/tty1 > /mnt/${guestname}/etc/event.d/xvc0 &&
rm -f /mnt/${guestname}/etc/event.d/tty*

#cp /root/skel/interfaces /mnt/${guestname}/etc/network/
#vim /mnt/${guestname}/etc/network/interfaces

cat <<EOF > /mnt/${guestname}/etc/init.d/gt-firstboot
	export DEBIAN_FRONTEND="noninteractive"
	apt-get update
	dpkg-reconfigure -a --default-priority -f noninteractive
	apt-get -f install
	apt-get -f -y install ssh wget bzip2 patch
	apt-get -f -y install language-pack-en-base
	apt-get -f -y install udev
	apt-get -f -y install ssh-server

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

	# By now, we should have booted already.
	rm -rf /etc/rc3.d/S10gtfirstboot
EOF
chmod 755 /mnt/${guestname}/etc/init.d/gt-firstboot

cat <<EOF > /etc/rc.local
	# Remove udev net rules *important*
	rm -rf /etc/udev/rules.d/*net*
	exit 0
EOF

export PasswdHash
chroot /mnt/${guestname} /bin/bash <<-EOF
	cd /dev
	/bin/mknod xvc0 c 204 191

	ln -s /etc/init.d/gt-firstboot /etc/rc3.d/S10gtfirstboot

	shadowconfig on
#	export DEBIAN_FRONTEND="noninteractive"
#	apt-get update
#	dpkg-reconfigure -a --default-priority -f noninteractive
#	apt-get -f -y install ssh wget bzip2 patch
#	apt-get -f -y install language-pack-en-base
#	apt-get -f -y install udev
#
#	# Install modules
#	cd /lib/modules
#	#wget ftp://ftp.grokthis.net/pub/linux/modules/latest-modules-linux-xen.tar.bz2
#	#tar Cjxf /lib/modules/ latest-modules-linux-xen.tar.bz2
#	kernelrel=\$(uname -r)
#	( file /sbin/init | grep 32-bit ) && ARCH="i386" || ARCH="amd64"
#	wget -O - \
#		ftp://ftp.grokthis.net/pub/linux/modules/modules-\${kernelrel}-\${ARCH}.tar.bz2 |
#		tar jCx /lib/modules/ &&
#		echo "Modules Installed." ||
#		echo "Module installation failed."
#
#
#	# Fix swap *hack-workaround*, regarding:
#	# http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=464418
#	cd /
#	wget -O - ftp://ftp.grokthis.net/pub/misc/patches/swapfix.patch | patch -p0 -N
#
#	# Remove udev net rules *important*
#	rm -rf /etc/udev/rules.d/*net*

	/usr/sbin/usermod -p '$PasswdHash' root

	# Stop daemons
	/etc/init.d/ssh stop
	/etc/init.d/cron stop
EOF
