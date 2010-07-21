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
# Use simplejson or Python 2.6 json, prefer simplejson.
try:
    import simplejson as json
except ImportError:
    import json
import urllib2
import ftplib
import mimetypes
import bz2
import tarfile

# used for random filenames...
import random
import base64

# FilePath abstraction
from twisted.python.filepath import FilePath

import logging
LOG_FILENAME = '/tmp/'+os.path.basename(sys.argv[0])+'.log'
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

# REMOVE THESE GLOBALS!

# Each takes one argument via format, {0} containing the 
# device
MKFS={
    'ext3': ('mkfs.ext3','-F','-q','{device}'),
    'reiserfs': ('mkfs.reiserfs','{device}'),
    'xfs': ('mkfs.xfs','-f','{device}'),
    'swap': ('mkswap','{device}'),
    'keep': ('true','{device}')
}

def fail(msg):
    print >>sys.stderr, msg
    print >>sys.stderr, "\n"
    sys.exit(1)


# Or-Die (do or die!)
# Execute arguments. Take last argument as error string
def ordie (*args):
    try:
        return submodule.check_call(args[:-1])
    except:
        return fail (args[-1])

# wstring simply writes a string to new file
def wstring(string,filename):
    # Right teh filez LOL -KTHXBYE, LOLCATZ
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
        self.ftype=data.has_key('ftype') and data['ftype'] or None
        self.wipe=data['wipe']
        self.volname=data['volname']
        self.wipesrc=data['wipesrc']
        self.method=data['method']
        self.partition=data.has_key('partition') and data['partition'] or None
        self.domount=data['mount']
        self.guestdev=data['dev']
        self.mountoptions=data['options']
        self.guest_name=data['guest_name']
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
                    #print >>sys.stderr, "Checking path: {0}".format(dpath)

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
            #print >>sys.stderr, "Stat failed for path: {0}".format(path)
            return False

        # si[0] should contain st_mode, required by S_ISBLK
        if not stat.S_ISBLK(si[0]):
            #print >>sys.stderr, "Is not a block device: {0}".format(si[0])
            return False
            fail ('Block device does not exist')
        return True

    def create(disk):
        if disk.devpath():
            return False

        # Create disks.
        try:
            print "Creating disk.\n"
            ex=('/etc/xen/shell/gt-reimage/disk.d/{0}'.format(disk.method),
                disk.size,
                disk.volname,
                disk.location )
            sp=subprocess.Popen(ex, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            soo=sp.communicate()
            sp.wait()
            #print >>sys.stderr, "Created disk. \nSTDOUT:\n({0})\nSTDERR:\n{1}\n".format(soo[0],soo[1])
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

    def set_partitioned(disk):
        devpath=disk.devpath()
        if not devpath:
            disk.create()
            devpath=disk.devpath()

        # toss it into the device manager (multipath required)
        ordie(("kpartx","-a","{0}p1".format(devpath)),"Kpartx failed")

        # change the device path
        disk.dpathsuffix="p1"

    def format(disk):
        if disk.is_mounted():
            return False

        devpath=disk.devpath()
        if not devpath:
            disk.create()
            devpath=disk.devpath()
        subprocess.call(('umount',"/mnt/{0}".format(disk.volname)))

        if not disk.partition:
            disk.partition='N'
        if disk.partition.upper() is not 'Y':
            #print >>sys.stderr, "Will not partition disk."
            pass
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

    def is_mounted(self,mntpnt=None):
        mntpnt=mntpnt or self.real_mountpoint(mntpnt,parent)

        if os.path.ismount(mntpnt):
            # Already mounted
            return mntpnt
        else:
            return False

    def real_mountpoint(self,mntpnt=None,parent=None):
        if self.real_mntpnt:
            return self.real_mntpnt

        if mntpnt is None:
            mntpnt=self.mntpnt
        if parent is None:
            parent=os.path.join("/mnt/",self.volname.strip('/'))
        mntpnt=os.path.join(parent,mntpnt.strip('/'))

        self.real_mntpnt = mntpnt
        return mntpnt

    # Optionally accept parent argument to mount under a sub-dir.
    def mount(self,mntpnt=None,parent=None):
        if not self.domount:
            return None

        devpath=self.devpath()
        if not self.check_exists(devpath):
            fail ("Disk does not exist. Cannot continue.")

        mntpnt=self.real_mountpoint(mntpnt,parent)

        if self.ismounted():
            # Already mounted
            return mntpnt

        sp0=subprocess.Popen(("xm","list",self.guest_name))
        if sp0.wait() == 0:
            fail ("Xen guest running.")

        # mkdir
        try:
            os.mkdir(mntpnt,750)
        except OSError:
            pass

        # mount
        ex=("mount",devpath,mntpnt)
        #"{0}/{1}".format(parent,self.volname))
        #print >>sys.stderr, "Mount, cmd: {0}".format(" ".join(ex))
        sp=subprocess.Popen(("mount",devpath,mntpnt),stdout=sys.stdout,stderr=sys.stderr)
        if sp.wait() != 0:
            fail ("Mount fail.")

        return mntpnt

    def umount(self,mntpnt=None,parent=None):
        if not self.is_mounted():
            return False

        mntpnt=self.real_mountpoint(mntpnt,parent)

        sp=subprocess.Popen(("umount",mntpnt),stdout=sys.stdout,stderr=sys.stderr)
        if sp.wait() != 0:
            # if failure, we kill processes and try again.
            # we don't want to kill processes if at all possible,
            # so this is only done as a last-resort

            # Must chdir out of the mntpnt, if necessary...
            os.chdir("/tmp")
            subprocess.call(("fuser","-k","-9","-c",mntpnt))
            subprocess.check_call(("sync"))
            subprocess.check_call(("sync"))
            subprocess.call(("umount",mntpnt))

            # Second time a charm
            sp=subprocess.Popen(("umount",mntpnt),stdout=sys.stdout,stderr=sys.stderr)
            if sp.wait() != 0:
                print "Mount error."
                raise

        return True

# Basic Time class
class Time(object):
    def seconds(cnt):
        return cnt
    def minutes(cnt):
        return 60*cnt
    def hours(cnt):
        return minutes(1)*60*cnt
    def hour():
        return hours(1)
    def days(cnt):
        return hours(1)*24*cnt
    def months(cnt):
        return int(days(1)*30.5*cnt)
    def years(cnt):
        return months(1)*cnt

import traceback
import pickle

# Define a forker!
# A good plan when doing a chroot or such...
class Fork(object):
    def __init__ (self, timeout=None):
        self.timeout = timeout

    def __call__(self,f):
        def fork_wrapper(*args):
            def timeout(signum,frame):
                raise IOError('Took longer than {0} seconds!'.format(self.timeout))

            # Yes, the variable names are cute, but shouldn't be
            # distracting...
            #  fifo is a fifo, jack is our pid,
            #  fee is the client's fifo-fh.
            #  fum is the server's fifo-fh.

            rnd=base64.urlsafe_b64encode(str(random.getrandbits(16)))
            filename='/tmp/'+os.path.basename(sys.argv[0])+'.'+rnd+'.ipc'
            fifo=os.mkfifo(filename)

            jack=os.fork()
            if jack == 0:
                try:
                    fee=open(filename,'wb')
                    result=f(*args)
                    # pickle arg[2] is negative, for highest version
                    # otherwise get version 0 & unicode error
                    pickle.dump(result,fee,-1)
                    fee.flush()
                    fee.close()
                except:
                    traceback.print_exc()
                    os._exit(1)
                os._exit(0)

            if self.timeout:
                signal.signal(signal.SIGALRM, timeout)
                signal.alarm(self.timeout)

            fum=open(filename, 'rb')
            jackret=fum.read()

            cexit=os.waitpid(jack,0)

            if self.timeout:
                signal.alarm(0)

            os.unlink(filename)

            if len(jackret) == 0:
                return True if cexit == 0 else False
            else:
                return pickle.loads(jackret)

        return fork_wrapper

def do_format(fschoice):
    global dsklst
    rootmounted=False
    # Format and mount disks
    for mntpnt,disk in dsklst.items():
        if not disk.ftype:
            disk.ftype = fschoice
        print "Formatting filesystem.\n"
        disk.format()

        #print "format complete."

        if disk.domount:
            print >>sys.stderr, "Mounting filesystem at instdir ({0})".format(instdir)
            disk.mount(parent=instdir)

        if disk.mntpnt == '/':
            rootmounted=True

    if not rootmounted:
        fail ("Instance root filesystem not found.")


@Fork(timeout=3600)
def do_debootstrap(suite,distro=None,arch=None,mirror=None):
    arch = arch or 'amd64'
    distro = distro or {
        'lenny': 'debian',
        'etch': 'debian',
        'jaunty': 'ubuntu',
        'karmic': 'ubuntu',
        'lucid': 'ubuntu',
    }[suite]
    mirror = mirror or {
        'debian': 'ftp://ftp.grokthis.net/debian',
        'ubuntu': 'ftp://ftp.grokthis.net/ubuntu',
    }[distro]

    if distro=='debian':
        subprocess.call(('debootstrap','--arch',arch,suite,mntpnt,mirror),stdout=sys.stdout)
    elif distro=='ubuntu':
        subprocess.call(('debootstrap','--no-resolve-deps','--exclude=console-setup','--arch',arch,suite,mntpnt,mirror),stdout=sys.stdout)
    else:
        fail("Unknown distribution. Pass 'distro' option to debootstrap")

def do_fstab(part=None):
    global dsklst
    if part:
        return dsklst[part].fstab()

    return [ dsklst[x].fstab() for x in dsklst ]
        
@Fork(timeout=1800)
def do_extract(dest, file):
    # Extract a tarball
    #mntpnt=dsklst['/'].mount()
    #os.chdir(mntpnt)
    #os.chroot(mntpnt)

    uh=open(file)
    tf=tarfile.open(mode='r|*',fileobj=uh)
    tf.extractall()

@Fork(timeout=1800)
def do_urlextract(dest, url):
    dest=FilePath(dest)

    # Don't do this if not mounted!
    mntpnt=dsklst['/'].real_mountpoint()
    if not os.path.ismount(mntpnt):
        return False

    if not dest.isdir():
        return False
    #os.chdir(dest.dirname()+dest.basename())
    #os.chroot(mntpnt)
   
    try:
        uh=urllib2.urlopen(url)
        tf=tarfile.open(mode='r|*',fileobj=uh)
        os.chroot(mntpnt)
        os.chdir(dest.dirname()+dest.basename())
        tf.extractall()
    except:
        traceback.print_exc()
    os.chdir('/')

@Fork(timeout=1800)
def do_rawriteurl(url):
    global dsklst

    # Don't do this if mounted!
    mntpnt=dsklst['/'].real_mountpoint()
    if os.path.ismount(mntpnt):
        return False
    
    ddof=open(dsklst['/'].devpath(),'w+b')

    #mntpnt=dsklst['/'].mount()
    #os.chdir(mntpnt)
    #os.chroot(mntpnt)

    uh=urllib2.urlopen(url)
    tf=tarfile.open(mode='r|*',fileobj=uh)
    ddif=tf.extractfile(tf.next)
    for buf in ddif.read(4096):
        ddof.write(buf)
        ddof.flush()
    ddof.clone()

@Fork(timeout=1800)
def do_mount(path):
    global dsklst
    dsklst[path].mount()

@Fork(timeout=1800)
def do_umount(path):
    global dsklst
    dsklst[path].umount()

@Fork(timeout=1800)
def do_peekfs(cmd,path,*args):
    global dsklst
    # wstring simply writes a string to new file
    #    def _wstring(filename,string):
    #        # Right teh filez LOL -KTHXBYE, LOLCATZ
    #        tehfile=path.open('w')
    #        tehfile.write(string)
    #        tehfile.close()

    def _wget(fp):
        def _wrap(path,url):
            req=urllib2.urlopen(url).read()
            tehfile=path.open('wb')
            tehfile.write(req)
            tehfile.close()
        return lambda *args: _wrap(fp,*args)

    # wstring writes a string to file
    def _astring(fp):
        def _wrap(path,string):
            tehfile=path.open('a')
            # Pydocs say both that this should be a no-op
            # BUT also say that some systems will not seek on their own?
            # we're just being careful here...
            tehfile.seek(0,os.SEEK_END)
            tehfile.write(string)
            tehfile.close()
        return lambda *args: _wrap(fp,*args)

    # Templating engine
    def _template(fp):
        def _wrap(path,**template):
            scratchfile=path.dirname()+"."+path.basename()+".tmp"
            fh=path.open('r')

            sfp=FilePath(scratchfile)
            sfh=sfp.open('w')
            seeklast=0
            for buffer in fh.readlines():
                for line in buffer:
                    sfh.write(line.format(**template))
            sfh.flush()
            sfh.close()
            fh.close()

            sfp.moveTo(path.realpath())
        return lambda *args: _wrap(fp,*args)

    def _urlextract(fp):
        return lambda url: do_urlextract(fp,url)

    def _extract(fp):
        return lambda *args: do_extract(fp,*args)

    def _moveTo(fp):
        return lambda path: fp.moveTo(FilePath(path))

    def _copyTo(fp):
        return lambda path: fp.copyTo(FilePath(path))

    def _ls(fp):
        def _wrap(fp,glob="*"):
            map (lambda f: f.basename(), fp.globChildren(glob))
        return lambda *args: _wrap(fp,*args)

    def _b64get(fp):
        return lambda: base64.b64encode(fp.getContent())

    def _b64put(fp):
        return lambda content: fp.setContent(base64.b64decode(content))

    mntpnt=dsklst['/'].real_mountpoint()

    # Make sure the user mounts us, don't auto-mount
    if not os.path.ismount(mntpnt):
        return False

    os.chdir(mntpnt)
    os.chroot(mntpnt)

    pp=FilePath('/')
    # We're safe /w preauthChild since we're chroot'ed
    fp=pp.preauthChild(path)

    """
    Mapping the t.p.f.FilePath methods
    which we will allow, to human-names
    we can accessed via cmd arg
    """
    return {
        'chmod': fp.chmod,
        'getsize': fp.getsize,
        'exists': fp.exists,
        'isdir': fp.isdir,
        'isfile': fp.isfile,
        'islink': fp.islink,
        'isabs': fp.isabs,
        #'listdir': fp.listdir,
        'ls': fp.listdir,
        'dir': fp.listdir,
        'splitext': fp.splitext,
        'touch': fp.touch,
        'rm': fp.remove,
        'makedirs': fp.makedirs,
        'basename': fp.basename,
        'dirname': fp.dirname,
        'parent': fp.parent,
        'mkdir': fp.createDirectory,
        'cp': _copyTo(fp),
        'mv': _moveTo(fp),
        'append': _astring(fp),
        'apply_template': _template(fp),
        #'wget': _wget(fp),
        #'urlextract': _urlextract(fp),
        #'extract': _extract(fp),
        'get': fp.getContent,
        'b64get': _b64get(fp),
        'b64put': _b64put(fp),
        #'ls': _ls(fp),
        #'mknod': _mknod(fp)
    }[cmd](*args)

dsklst={}

def main(argv=None):
    argv = argv or sys.argv
    global dsklst

    # Arguments
    #guestname=sys.argv[1]
    #user=guestname
    #command=sys.argv[2]
    #cmdargs=sys.argv[3:]

    # Receive input via stdin & json
    jsonargs=json.load(sys.stdin)

    client=jsonargs['client']
    cmdargs=jsonargs['cmd']
    cmd=cmdargs.pop(0)

    # My shift from a struct to a class-based system...
    dsklst={
        '/': Disk(
            method='iSCSI',
            size=client['block_storage'],
            location= '10.1.0.1',
            mntpnt= '/',
            mount=True,
            #ftype= fschoice.lower(),
            wipe= 0,
            volname= client['username'],
            wipesrc= '/dev/zero',
            #partition= partchoice,
            dev="/dev/"+client['disk_namespace']+"a1",
            options="defaults,noatime",
            guest_name= client['username'],
        ),
        'swap': Disk(
            method='LVM',
            size= '{0}M'.format(int(client['memory'])*2),
            location= 'XenSwap',
            mntpnt= 'none',
            mount=False,
            ftype= 'swap',
            wipe= 0,
            volname= "{0}swap".format(client['username']),
            wipesrc= '/dev/zero',
            partition = False,
            dev="/dev/"+client['disk_namespace']+"b1",
            options="defaults",
            guest_name= client['username'],
        )
    }


    cmdtable={
        #'putf': wstring,
        #'appendf': astring,
        #'extract': do_extract,
        'fstab': do_fstab,
        'urlextract': do_urlextract,
        'rawrite': do_rawriteurl,
        'mkfs': do_format,
        'debootstrap': do_debootstrap,
        'peekfs': do_peekfs,
        'mount': do_mount,
        'umount': do_umount,
    }


    # Sanity checks...
    if client['username'].find("..") != -1:
        fail ("Guest '{0}' specified is invalid".format(client['username']))
    if client['username'].find("/") != -1:
        fail ("Guest '{0}' specified is invalid".format(client['username']))

    instdir=os.path.join("/mnt/",client['username'])

    # Call given command & print json out
    json.dump(cmdtable[cmd](*cmdargs),sys.stdout)
    sys.exit(0)

if __name__ == "__main__":
    sys.exit(main())
