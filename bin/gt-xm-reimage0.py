#!/usr/bin/env python2.6
# gt-xm-reimage0.py - uid0 reimaging script 
# refactored from original gt-xm-reimage0 shell script
# Copyright (C) 2006-2010 Eric Windisch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import subprocess
import shutil
import os
import signal
import stat
import time

# required for iscsi
import json
import urllib2

import logging
LOG_FILENAME = '/tmp/logging_example.out'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

class LogDevice():
    def write(str):
        print >>sys.stdout, str
        logging.debug(str)
#sys.stderr=LogDevice()

## Block Ctrl-C and other naughty signals - All resistence is futile!
#signal.signal(1,None)
#signal.signal(2,None)
#signal.signal(15,None)

def fail(msg):
    print >>sys.stderr, msg
    print >>sys.stderr, "\n"
    sys.exit(1)

# import args from bash script frontend...
# TODO: undo/fix this!
guestname=os.environ['guestname']
partchoice=os.environ['partchoice']
sizemem=os.environ['sizemem']
OSARCH=os.environ['OSARCH']
VERSION=os.environ['VERSION']
MIRROR=os.environ['MIRROR']
METHOD=os.environ['METHOD']
IPADDRESS=os.environ['IPADDRESS'],
IPGATEWAY=os.environ['IPGATEWAY'],
IPNETMASK=os.environ['IPNETMASK'],
PasswdHash=os.environ['PasswdHash'],
fschoice=os.environ['fschoice']
DISTRO=os.environ['distro']
OSFAMILY=os.environ['OSFAMILY']
IMGF=None
# For some reason(???), has_key might succeed
# but os.environ['IMGF'] won't... so we 'try' it
try:
    #print >>sys.stderr, os.environ
    if os.environ.has_key('IMGF'):
        #print "Has key IMGF"
        IMGF=os.environ['IMGF']
        #print "IMGF={0}".format(IMGF)
except:
    pass
useracct=os.environ['useracct']

# REMOVE THESE GLOBALS!

DISKMAP={
	'64':'4G',
	'96':'4G',
	'128':'8G',
	'192':'8G',
	'256':'16G',
	'320':'16G',
	'512':'16G',
	'768':'32G',
	'1024':'32G',
	'2048':'64G',
	'4096':'128G'
}

# Each takes one argument via format, {0} containing the 
# device
MKFS={
    'ext3': ('mkfs.ext3','-F','-q','{device}'),
    'reiserfs': ('mkfs.reiserfs','{device}'),
    'xfs': ('mkfs.xfs','-f','{device}'),
    'swap': ('mkswap','{device}'),
    'keep': ('true','{device}')
}

POSTINST={
    'UBUNTU':'/etc/xen/shell/gt-reimage/post-inst.d/ubuntu.sh',
    'DEBIAN':'/etc/xen/shell/gt-reimage/post-inst.d/debian.sh',
    'TURNKEY32':'/etc/xen/shell/gt-reimage/post-inst.d/turnkey.sh',
    'ANDROID':'etc/xen/shell/gt-reimage/post-inst.d/android.sh',
    'FEDORA32':'/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh',
    'FEDORA64':'/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh',
    'FEDORA':'/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh',
    'RHEL':'/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh',
    'CENTOS32':'/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh',
    'CENTOS64':'/etc/xen/shell/gt-reimage/post-inst.d/redhat.sh',
    'GENTOO32':'/etc/xen/shell/gt-reimage/post-inst.d/gentoo.sh',
    'GENTOO64':'/etc/xen/shell/gt-reimage/post-inst.d/gentoo.sh',
    'URL':'/bin/false'
}

# Or-Die (do or die!)
# Execute arguments. Take last argument as error string
def ordie (*args):
    try:
        return submodule.check_call(args[:-1])
    except:
        return fail (args[-1])

# wstring simply writes a string to new file
def wstring(string,filename):
    # Right teh filez LOL -LOLCATZ
    tehfile=open(filename,'w')
    tehfile.write(string)
    tehfile.close()

# wstring writes a string to file
def astring(string,filename):
    # Right teh filez LOL -LOLCATZ
    tehfile=open(filename,'a')
    # Pydocs say both that this should be a no-op
    # BUT also say that some systems will not seek on their own?
    # we're just being careful here...
    tehfile.seek(0,os.SEEK_END)
    tehfile.write(string)
    tehfile.close()

# Sets class variables by args
def cvarargs (cls,cvars,**kwargs):
    for key in kwargs:
        if cvars.count(key) > 0:
            # Assign variable to key where key is an
            # allowed class variable
            print("cls.{0}=kwargs[key] ({1})".format(key,kwargs[key]))
            eval("cls.{0} = kwargs[key]".format(key))
    pass

class Disk:
    def __init__(self,**kwargs):
        # Allowed class variables
        data=kwargs
        #        cvarargs(self,[
        #            'size',
        #            'location',
        #            'mntpnt',
        #            'format',
        #            'wipe',
        #            'volname',
        #            'wipesrc',
        #            'method'
        #        ],**kwargs)
        self.size=data['size']
        self.location=data['location']
        self.mntpnt=data['mntpnt']
        self.ftype=data['ftype']
        self.wipe=data['wipe']
        self.volname=data['volname']
        self.wipesrc=data['wipesrc']
        self.method=data['method']
        self.partition=data['partition']
        self.domount=data['mount']
        self.guestdev=data['dev']
        self.mountoptions=data['options']
        self.dpathsuffix=None
        self._devpath=None
        pass

    def fstab(self):
        mntcnt=0
        if self.domount:
            mntcnt=1

        line="{0}\t{1}\t{2}\t{3}\t{4}\t{5}".format(
            self.guestdev,
            self.mntpnt,
            self.ftype,
            self.mountoptions,
            0,
            mntcnt
        )
        return line

    def devpath(self):
        if self._devpath:
            return self._devpath

        dpath=''
        if self.method=='LVM':
            dpath="/dev/mapper/{0}-{1}".format(self.location,self.volname)
        elif self.method=='iSCSI':
            req=urllib2.urlopen("http://{0}:8080/iscsitadm/target/array002/{1}".format(self.location,self.volname)).read()
            diskinfo=json.loads(req)

            if type(diskinfo) is dict:
                iqn=diskinfo['array002/{0}'.format(self.volname)]['iSCSI Name']
                if not iqn:
                    return None
                dpath="/dev/disk/by-path/ip-{0}:3260-iscsi-{1}-lun-0".format(self.location,iqn)
                if os.path.islink(dpath):
                    # Lets get rid of the symlinks and
                    # pretty up the display of the path we churn out
                    dpath=os.path.abspath(os.path.join(os.path.dirname(dpath), os.readlink(dpath)))
                    print >>sys.stderr, "Checking path: {0}".format(dpath)

                if not self.check_exists(dpath):
                    print >>sys.stderr, "Scanning iSCSI"
                    # init the device...
                    #subprocess.call(('iscsiadm','-m','discovery','-t','sendtargets','-p',self.location))
                    #subprocess.call(('iscsiadm','-m','node','-l','-T',iqn,'-p',"{0}:3260".format(self.location)))
                    sp1=subprocess.Popen(('iscsiadm','-m','discovery','-t','sendtargets','-p',self.location),stderr=subprocess.PIPE,stdout=subprocess.PIPE)
                    sp1.wait()
                    sp2=subprocess.Popen(('iscsiadm','-m','node','-l','-T',iqn,'-p',"{0}:3260".format(self.location)),stderr=subprocess.PIPE,stdout=subprocess.PIPE)
                    sp2.wait()

                    print "Waiting for disk to initialize..."
                    time.sleep(5)
            else:
                return None
                #"/dev/disk-not-found"
                #dpath="/dev/disk-not-found"
        else:
            return fail("Disk method invalid")
        if self.dpathsuffix:
            dpath="{0}{1}".format(dpath,self.dpathsuffix)
        if not self.check_exists(dpath):
            return None
        self._devpath=dpath
        return dpath

    def check_exists(self,path):
        if os.path.islink(path):
            path=os.path.join(os.path.dirname(path), os.readlink(path))
        try:
            si=os.stat(path)
        except OSError:
            print >>sys.stderr, "Stat failed for path: {0}".format(path)
            return False

        # si[0] should contain st_mode, required by S_ISBLK
        if not stat.S_ISBLK(si[0]):
            print >>sys.stderr, "Is not a block device: {0}".format(si[0])
            return False
            fail ('Block device does not exist')
        return True

    def create(disk):
        if not disk.devpath():
            # Create disks.
            try:
                print "Creating disk.\n"
                ex=('/etc/xen/shell/gt-reimage/disk.d/{0}'.format(disk.method),
                    disk.size,
                    disk.volname,
                    disk.location )
                #print >>sys.stderr, "Calling '{3}'\n".format(ex)
                sp=subprocess.Popen(ex, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
                soo=sp.communicate()
                sp.wait()
                print >>sys.stderr, "Created disk. \nSTDOUT:\n({0})\nSTDERR:\n{1}\n".format(soo[0],soo[1])
            except:
                #CalledProcessError:
                fail ("Could not create disk.")

            if not disk.devpath():
                fail ("Disk does not exist. Cannot continue.")

            # Wiping is provided as a security measure to prevent
            # data exposure.  Simply zero'ing blocks is sufficient
            # unless users have physical access to the device.

            if disk.wipe > 0:
                print "Wiping block device (may take a while)\n"
                sp0=subprocess.Popen(('dd',"if={0}".format(disk.wipesrc),'bs=8M'),stdout=subprocess.PIPE,stderr=sys.stdout)
                sp1=subprocess.Popen(('pv'),stdin=sp0.stdout,stdout=subprocess.PIPE,stderr=sys.stdout)
                sp2=subprocess.Popen(('dd','of={0}'.format(disk.devpath()),'bs=8M'),stdin=sp1.stdout,stderr=sys.stdout)
                sp0.wait()
                sp1.wait()
                sp2.wait()
                disk.wipe-=1

    def format(disk):
        devpath=disk.devpath()
        if not devpath:
            disk.create()
            devpath=disk.devpath()
        subprocess.call(('umount',"/mnt/{0}".format(disk.volname)))

        if not disk.partition:
            disk.partition='N'
        if disk.partition.upper() is not 'Y':
            print >>sys.stderr, "Will not partition disk."
        else:
            # make partition
            ordie(("parted","-s",devpath,"mklabel","msdos"),"Mklabel failed")
            ordie(("parted","-s",devpath,"mkpart","primary","0",disk.partition),"Mkpart failed")

            # toss it into the device manager (multipath required)
            ordie(("kpartx","-a","{0}p1".format(devpath)),"Kpartx failed")

            # change the device path
            disk.dpathsuffix="p1"

        if not MKFS[disk.ftype]:
            fail ('Filesystem choice invalid.')

        print "Building filesystem."
        fscmd=map(lambda x: x.format(device=devpath), MKFS[disk.ftype])
        print >>sys.stderr,"mkfs, cmd: {0}".format(" ".join(fscmd))
        sp=subprocess.Popen(fscmd,stdout=sys.stdout)
        # Block return until format complete 
        sp.wait()

    # Optionally accept parent argument to mount under a sub-dir.
    def mount(self,mntpnt=None,parent=None):
        if not self.domount:
            return None

        devpath=self.devpath()
        if not self.check_exists(devpath):
            fail ("Disk does not exist. Cannot continue.")

        if mntpnt is None:
            mntpnt=self.mntpnt
        if parent is None:
            parent=os.path.join("/mnt/",self.volname.strip('/'))
        mntpnt=os.path.join(parent,mntpnt.strip('/'))
        # mkdir
        try:
            os.mkdir(mntpnt,750)
        except OSError:
            pass

        # mount
        ex=("mount",devpath,mntpnt)
        #"{0}/{1}".format(parent,self.volname))
        print >>sys.stderr, "Mount, cmd: {0}".format(" ".join(ex))
        sp=subprocess.Popen(("mount",devpath,mntpnt),stdout=sys.stdout,stderr=sys.stderr)
        if sp.wait() != 0:
            fail ("Mount fail.")

# My shift from a struct to a class-based system...
dsklst=[
    Disk(
        method='iSCSI',
        size= DISKMAP[sizemem],
        location= '10.1.0.1',
        mntpnt= '/',
        mount=True,
        ftype= fschoice.lower(),
        wipe= 0,
        volname= guestname,
        wipesrc= '/dev/zero',
        partition= partchoice,
        dev="/dev/sda1",
        options="defaults,noatime"
    ),
    Disk(
        method='LVM',
        size= '{0}M'.format(int(sizemem)*2),
        location= 'XenSwap',
        mntpnt= 'none',
        mount=False,
        ftype= 'swap',
        wipe= 0,
        volname= "{0}swap".format(guestname),
        wipesrc= '/dev/zero',
        partition = False,
        dev="/dev/sdb1",
        options="defaults"
    )
]

# Sanity checks...
if guestname.find("..") != -1:
    fail ("Guest '{0}' specified is invalid".format(guestname))
if guestname.find("/") != -1:
    fail ("Guest '{0}' specified is invalid".format(guestname))

if not DISKMAP[sizemem]:
    fail ("Memory size unknown in configuration. {0}, {1}.".format(sizemem, DISKMAP[sizemem]))

instdir=os.path.join("/mnt/",guestname)
rootmounted=False

# Format and mount disks
for disk in dsklst:
    print "Formatting filesystem.\n"
    disk.format()

    print "format complete."

    if disk.domount:
        print >>sys.stderr, "Mounting filesystem at instdir ({0})".format(instdir)
        disk.mount(parent=instdir)

    if disk.mntpnt == '/':
        rootmounted=True

if not rootmounted:
    fail ("New root filesystem not found.")

# CH DIR to the guest dir
print >>sys.stderr, "Changing directory: {0}".format(instdir)
os.chdir(instdir)

#if not OSFAMILY:
#    fail ('OS not defined.')

print "Beginning installation."
print >>sys.stderr, "Install begin for User: {guestname}".format(guestname=guestname)
#, OS: {OSFAMILY}-{VERSION} ({DISTRO}) via {METHOD} from {MIRROR}".format(guestname=guestname, OSFAMILY=OSFAMILY, VERSION=VERSION, DISTRO=DISTRO, METHOD=METHOD, MIRROR=MIRROR)
sp=None
if METHOD=='debootstrap':
    print >>sys.stderr, "Executing debootstrap (--arch $OSARCH $VERSION /mnt/${guestname} $MIRROR)"
    subprocess.call(('debootstrap','--arch',OSARCH,VERSION,instdir,MIRROR),stdout=sys.stdout)
elif METHOD=='udebootstrap':
    print >>sys.stderr, "Executing debootstrap (--arch $OSARCH $VERSION /mnt/${guestname} $MIRROR)"
    subprocess.call(('debootstrap','--no-resolve-deps','--exclude=console-setup','--arch',OSARCH,VERSION,instdir,MIRROR),stdout=sys.stdout)
elif METHOD=='rinse':
    print >>sys.stderr, "Executing rinse ($OSARCH $VERSION /mnt/${guestname} $MIRROR)"
    subprocess.call(('rinse','--arch',OSARCH,'--distribution',"fedora-core-{0}".format(VERSION),"--directory {0}".format(instdir)),stdout=sys.stdout)
elif METHOD=='image':
    print >>sys.stderr, "Fetching Image: $MIRROR/$distro-$OSARCH.tar.bz2"
    sp0=subprocess.Popen(('wget','-O','-',"{0}/{1}-{2}.tar.bz2".format(MIRROR,DISTRO,OSARCH)),stdout=subprocess.PIPE)
    sp=subprocess.Popen(('tar','jx'),stdin=sp0.stdout,stdout=sys.stdout)
    sp.wait()
elif METHOD=='image2':
    #	for a in ${distributions[@]}; do
    #		print "Checking $a for $distro"
    #		# only break if the choice is acceptable
    #		if [ "${a:0:${#distro}}" == "$distro" ]; then
    #		IMGF=`print "$a" | cut -d- -f3-`
    if not IMGF:
        fail("Image file unknown.")

    print "Fetching Image: {0}/{1}".format(MIRROR,IMGF)
    TYPE=None
    if IMGF.endswith("bz2"):
        TYPE='j'
    elif IMGF.endswith("gz"):
        TYPE='z'
    if not TYPE:
        fail ("Unknown image type")

    sp0=subprocess.Popen(("wget","-O","-","{0}/{1}".format(MIRROR,IMGF)),stdout=subprocess.PIPE)
    sp1=subprocess.Popen(("tar","{0}x".format(TYPE)),stdin=sp0.stdout,stdout=sys.stdout)
    sp0.wait()
    sp1.wait()
elif METHOD=='user-image':
    print "Attempting to fetch: {0}".format(MIRROR)

    TYPE=None
    if MIRROR.endswith("bz2"):
        TYPE='j'
    elif MIRROR.endswith("gz"):
        TYPE='z'
    if not TYPE:
        fail ("Unknown image type")
        #sys.exit(1)

    sp0=subprocess.Popen(("wget","-O","-","{0}".format(MIRROR)),stdout=subprocess.PIPE)
    sp1=subprocess.Popen(("tar","{0}xUv".format(TYPE)),stdin=sp0.stdout,stderr=sys.stdout)
    sp0.wait()
    sp1.wait()

if os.path.islink(os.path.join(instdir,"etc/hostname")):
    fail("hostname file is a symlink in guest image.");
if os.path.islink(os.path.join(instdir,"etc/fstab")):
    fail("fstab file is a symlink in guest image.");
if os.path.islink(os.path.join(instdir,"etc/host")):
    fail("host file is a symlink in guest image.");
if os.path.islink(os.path.join(instdir,"etc/resolv.conf")):
    fail("resolv.conf file is a symlink in guest image.");
if os.path.islink(os.path.join(instdir,"dev/xvc")):
    fail("xvc device is a symlink in guest image.");

wstring(guestname, os.path.join(instdir,"etc/hostname"))

# Open template...
TTfstabFH=open('/etc/xen/shell/gt-reimage/fstab.template')
# Read template, should be a small file, so in-memory is okay...
TTfstab=TTfstabFH.readlines()
TTfstabFH.close()
# Write fstab file, replacing $storage with 
# with each disk's fstab line, joined by newlines
#for x in map(lambda x: x.fstab(),dsklst):
for line in [ x.fstab() for x in dsklst ]:
    TTfstab.append(line)
wstring('\n'.join(TTfstab), os.path.join(instdir,"etc/fstab"))

wstring("127.0.0.1 localhost {0}".format(guestname),os.path.join(instdir,"etc/hosts"))

#cp /root/skel/fstab "/mnt/${guestname}/etc/"
#cp /root/skel/resolv.conf "/mnt/${guestname}/etc/"
shutil.copy2("/root/skel/resolv.conf",os.path.join(instdir,"etc/resolv.conf"))

# Make proc and sys directories, lets assume this is good, not evil!?!
try:
    os.mkdir(os.path.join(instdir,"proc"),755)
    os.mkdir(os.path.join(instdir,"sys"),755)
except:
    pass

# If we can't beat them, join them!
# We won't offer customers a tty1 device as normal, so make it a xvc0 device for real!
try:
    os.unlink(os.path.join(instdir,"dev/tty1"))
    subprocess.Popen("/bin/mknod",os.path.join(instdir,"dev/tty1"),"c","204","191").wait()
    os.unlink(os.path.join(instdir,"dev/xvc0"))
    subprocess.Popen("/bin/mknod",os.path.join(instdir,"dev/xvc0"),"c","204","191").wait()
except:
    pass

DISTRO=DISTRO.split('-',1)[0].upper()
if not POSTINST.has_key(DISTRO):
    print >>sys.stderr, "Post-install script not found.\n"
    #fail ('Post-install script not found.')
else:
    env={
        'guestname':guestname,
        'IPADDRESS':IPADDRESS,
        'IPGATEWAY':IPGATEWAY,
        'IPNETMASK':IPNETMASK,
        'PasswdHash':PasswdHash,
        'PATH':"/bin:/sbin:/usr/bin:/usr/sbin" }
    # I haven't figured out why these variables
    # are turning into tuples, but I suspect there might be newlines
    # in the raw environment variables causing it?? - ERICW
    # this fixes the environment variables...
    for k,v in env.items():
        if type(v) is tuple:
            env[k]=v[0]
    # Run the post-inst script, further-cleaning ENV
    sp=subprocess.Popen(POSTINST[DISTRO], env=env)
    sp.wait()

print "Unmounting filesystem"
os.chdir("/tmp")
subprocess.call(("fuser","-k","-9","-c",instdir))
subprocess.check_call(("sync"))
subprocess.check_call(("sync"))

subprocess.call(("umount",instdir))

print "Installation complete."
sys.exit(0)
