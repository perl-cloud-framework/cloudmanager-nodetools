
# Post-install scripts for each OS FAMILY
POSTINST=(
	[$UBUNTU]=/etc/xen/shell/gt-reimage/post-inst.d/ubuntu.sh
	[$DEBIAN]=/etc/xen/shell/gt-reimage/post-inst.d/debian.sh
	[$TURNKEY32]=/etc/xen/shell/gt-reimage/post-inst.d/turnkey.sh
	[$ANDROID]=etc/xen/shell/gt-reimage/post-inst.d/android.sh
	[$FEDORA32]=/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh
	[$FEDORA64]=/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh
	[$FEDORA]=/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh
	[$RHEL]=/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh
	[$CENTOS32]=/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh
	[$CENTOS64]=/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh
	[$GENTOO32]=/etc/xen/shell/gt-reimage/post-inst.d/gentoo.sh
	[$GENTOO64]=/etc/xen/shell/gt-reimage/post-inst.d/gentoo.sh
	[$URL]=/bin/false
)

# Maps OSFAMILIES to Installation method backends
# methods currently available: debootstrap, image, user-image
# TODO: rpmstrap and virt-install support
METHODS=(
	[$UBUNTU]='udebootstrap'
	[$DEBIAN]='debootstrap'
	[$TURNKEY32]='image2'
	[$FEDORA32]='image2'
	[$FEDORA64]='image2'
	[$SUSE32]='image2'
	[$SUSE64]='image2'
	[$FEDORA]='rinse'
	[$ANDROID]='image2'
	[$RHEL]='image'
	[$CENTOS64]='image2'
	[$CENTOS32]='image2'
	[$URL]='user-image'
	[$GENTOO32]='image2'
	[$GENTOO64]='image2'
)

# Specify which mirrors to download from
MIRRORS=(
	[$DEBIAN]="http://ftp.grokthis.net/mirrors/debian/"
	[$TURNKEY32]="ftp://ftp.grokthis.net/disk_images/"
	[$FEDORA32]="ftp://ftp.grokthis.net/disk_images/"
	[$FEDORA64]="ftp://ftp.grokthis.net/disk_images/"
	[$SUSE32]="ftp://ftp.grokthis.net/disk_images/"
	[$SUSE64]="ftp://ftp.grokthis.net/disk_images/"
	[$ANDROID]="ftp://ftp.grokthis.net/disk_images/"
	[$FEDORA]="null"
	[$CENTOS32]="ftp://ftp.grokthis.net/disk_images/"
	[$CENTOS64]="ftp://ftp.grokthis.net/disk_images/"
	[$UBUNTU]="http://ftp.grokthis.net/mirrors/ubuntu/"
	[$GENTOO32]="http://distro.ibiblio.org/pub/linux/distributions/gentoo/releases/x86/2007.0/stages/"
	[$GENTOO64]="ftp://gentoo.mirrors.pair.com/releases/amd64/2007.0/stages/"
)

