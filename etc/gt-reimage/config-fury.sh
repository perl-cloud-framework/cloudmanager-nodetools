# Guest configuration directory
GUESTCFGDIR="/etc/xen/auto/"

# Default group
DEFAULT_GROUP='xen'
# Default shell
DEFAULT_SHELL='/usr/bin/xen-shell'

# Disk format
# possible values are: LVM
# Recommendation for AOE: create LVM physical volumes from AoE etherd devices"
# TODO: support flat files, iSCSI, etc..
DISKFMT='LVM'

# Append the following string
# to all swap volume names
GUEST_DISK_SWAPVOL_POSTFIX='swap'

# Volume groups for LVM
GUEST_DISK_DISKGROUP='SanXenDomains'
GUEST_DISK_SWAPGROUP='XenSwap'

# Wipe the block devices after creating them.
# Only executed for *new* block devices (eg. LVM)
# This ensures that if the physical volume
# was used by another customer/user, that
# they cannot perform data analysis.
# Runs as long as below is non-zero.
GUEST_DISK_WIPEFIRST=y

# Device for wiping source.
# /dev/zero is sufficient for most situations where users do
# not have physical access.
# /dev/urandom provides better protection
# if there is physical access.
# /dev/random provides even better protection
# but requires a *LOT* of entropy.
GUEST_DISK_WIPEFIRST_DEV=/dev/zero

# Number of times to wipe the volume
# setting this to 0 should disable disk wiping.
GUEST_DISK_WIPEFIRST_COUNT=1

# Guestname handler
GUESTNAME_HANDLER="/etc/xen/shell/gt-reimage/guestname.d/prompt.sh"

# Plan handler
PLAN_HANDLER="/etc/xen/shell/gt-reimage/plan.d/xml.sh"
#PLAN_HANDLER="/etc/xen/shell/gt-reimage/plan.d/prompt.sh"

# IP Address handler
IPADDRESS_HANDLER="/etc/xen/shell/gt-reimage/ipaddress.d/prompt.sh"
#IPADDRESS_HANDLER="/etc/xen/shell/gt-reimage/ipaddress.d/file-pool.sh"
#IPADDRESS_HANDLER="/etc/xen/shell/gt-reimage/ipaddress.d/sql-pool.sh"

# Username format handler
#USERFMT_HANDLER="/etc/xen/shell/gt-reimage/userfmt.d/guestname.sh"
#USERFMT_HANDLER="/etc/xen/shell/gt-reimage/userfmt.d/prompt.sh"
USERFMT_HANDLER="/etc/xen/shell/gt-reimage/userfmt.d/grokthis.sh"

# Password handler
PASSWD_HANDLER="/etc/xen/shell/gt-reimage/passwd.d/makepasswd.sh"

# Welcome handler
WELCOME_HANDLER="/etc/xen/shell/gt-reimage/welcome.d/file.sh"

# Guest creation handler
GUEST_CREATION_HANDLER="/etc/xen/shell/gt-reimage/guestcfg.d/file.sh"

# GPG Receipient identity for encrypted local-storage of customer passwords
GPG_IDENTITY='admin@localhost'

# Default netmask if only given an IP address
# accepts CIDR values, eg. 8, 16, 20, 24, 27, 29
DEFAULT_NETMASK='24'

##
## TODO: Remove DISKMAP and SWAPMAP
##
# maps ram sizes to disk sizes
# ram is given in megabytes,
# disk MUST have one of
# the following prefixes:
# M(egabytes), G(igabytes), T(erabytes)
DISKMAP=(
	[64]='4G'
	[96]='4G'
	[128]='8G'
	[256]='16G'
	[512]='32G'
	[1024]='64G'
	[2048]='128G'
) 
# maps ram sizes to swap sizes
# given in megabytes
SWAPMAP=(
	[64]=128
	[96]=192
	[128]=256
	[256]=512
	[512]=1024
	[1024]=2048
	[2048]=4096
)

# Post-install scripts for each OS FAMILY
POSTINST=(
	[$UBUNTU]=/etc/xen/shell/gt-reimage/post-inst.d/ubuntu.sh
	[$DEBIAN]=/etc/xen/shell/gt-reimage/post-inst.d/debian.sh
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
	[$FEDORA32]='image2'
	[$FEDORA64]='image2'
	[$FEDORA]='rinse'
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
	[$FEDORA32]="ftp://ftp.grokthis.net/disk_images/"
	[$FEDORA64]="ftp://ftp.grokthis.net/disk_images/"
	[$FEDORA]="null"
	[$CENTOS32]="ftp://ftp.grokthis.net/disk_images/"
	[$CENTOS64]="ftp://ftp.grokthis.net/disk_images/"
	#[$UBUNTU]="http://ftp.grokthis.net/mirrors/ubuntu/"
	[$UBUNTU]="http://us.archive.ubuntu.com/ubuntu/"
	[$GENTOO32]="http://distro.ibiblio.org/pub/linux/distributions/gentoo/releases/x86/2007.0/stages/"
	[$GENTOO64]="ftp://gentoo.mirrors.pair.com/releases/amd64/2007.0/stages/"
)

# Specify file system creation commands
MKFS=(
	[$EXT3]="mkfs.ext3 -m1"
	[$REISERFS]="mkfs.reiserfs"
	[$XFS]="mkfs.xfs -f"
)
