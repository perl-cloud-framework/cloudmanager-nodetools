#
#  Only used to build distribution tarballs.
#
DIST_PREFIX = ${TMP}
VERSION     = 0.1.0
BASE        = gt-xmc


all:
	@echo " "
	@echo "Usage:"
	@echo " "
	@echo " make clean   = Clean this directory recursively"
	@echo " make diff    = Run a 'cvs diff'."
	@echo " make install = Install the software to /usr/local"
	@echo " make remove  = Uninstall"
	@echo " make release = Make a release tarball"
	@echo " make update  = Update from the CVS repository."
	@echo " "


clean:
	@find . -name '*~' -exec rm -f \{\} \;
	@if [ -e build-stamp ]; then rm -f build-stamp ; fi
	@if [ -e configure-stamp ]; then rm -f configure-stamp ; fi
	@if [ -d debian/xen-shell ]; then rm -rf debian/xen-shell ; fi


diff:
	cvs diff --unified 2>/dev/null


#
#  Install into /usr/bin, then remove the old install from /usr/local/bin
#
install:
	cp -a skel /root/
	mkdir /etc/xen/shell 2>&1 >/dev/null || echo "/etc/xen/shell Exists"
	cp -a etc/gt-reimage /etc/xen/shell/
	cp bin/* /usr/bin

manpages:
	for i in man/*.man; do file=`basename $$i .man` ; cp $$i /usr/share/man/man1/$$file.1; done
	for i in /usr/share/man/man1/*.1; do gzip -f -9 $$i; done
	rm /usr/share/man/man1/xen-add-user.1.gz

#
#  Make a new release tarball.
#
release: clean
	rm -rf $(DIST_PREFIX)/$(BASE)-$(VERSION)
	rm -f $(DIST_PREFIX)/$(BASE)-$(VERSION).tar.gz
	cp -R . $(DIST_PREFIX)/$(BASE)-$(VERSION)
	find  $(DIST_PREFIX)/$(BASE)-$(VERSION) -name "CVS" -print | xargs rm -rf
	rm -rf $(DIST_PREFIX)/$(BASE)-$(VERSION)/debian
	cd $(DIST_PREFIX) && tar --exclude=.cvsignore -cvf $(DIST_PREFIX)/$(BASE)-$(VERSION).tar $(BASE)-$(VERSION)/
	gzip $(DIST_PREFIX)/$(BASE)-$(VERSION).tar
	mv $(DIST_PREFIX)/$(BASE)-$(VERSION).tar.gz .
	rm -rf $(DIST_PREFIX)/$(BASE)-$(VERSION)
	gpg --armour --detach-sign $(BASE)-$(VERSION).tar.gz


#
#  Reove the software
#
remove:
	rm /usr/bin/xen-shell
	rm /usr/bin/xen-login-shell
	rm /usr/bin/xm-reimage
	rm /etc/xen-shell/_screenrc
	-rmdir /etc/xen-shell


#
#  Run the test suite.
#
test:
	prove --shuffle tests/


#
#  Run the test suite verbosely.
#
test-verbose:
	prove --shuffle --verbose tests/


#
#  Update from CVS repository
#
update: 
	cvs -z3 update -A -P -d 2>/dev/null

