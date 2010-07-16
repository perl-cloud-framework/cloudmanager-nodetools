chroot /mnt/${guestname} /bin/bash <<-EOF
	mkdir /proc
	mkdir /sys
	mkdir /dev/pts

	cd dev
	MAKEDEV console null zero random sda ptmx
	/bin/mknod xvc0 c 204 191

	usermod -p '$PasswdHash' root

	cd /lib/modules
	wget ftp://ftp.grokthis.net/pub/linux/modules/latest-modules-linux-xen.tar.bz2
	tar jxvf latest-modules-linux-xen.tar.bz2
	cd /
EOF
echo "xvc0" >> /mnt/${guestname}/etc/securetty

# Fix the inittab, remove useless gettys
sed '/mingetty tty[2-6]/{ s/^/#/; }' /mnt/${guestname}/etc/inittab > /mnt/${guestname}/etc/inittab.new
sed 's/tty1/xvc0/;' /mnt/${guestname}/etc/inittab.new > /mnt/${guestname}/etc/inittab
chmod 644 /mnt/${guestname}/etc/inittab

