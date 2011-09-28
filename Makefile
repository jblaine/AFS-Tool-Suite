# The full path to your Python interpreter
PYTHON	=	/afs/rcf/lang/bin/python

PREFIX	=	/afs/rcf/admin/utils/ats
# PREFIX	=	/tmp/ats

# Where to store the ats binaries
BINDIR	=	$(PREFIX)/bin

# Where to store the ats libraries
LIBDIR	=	$(PREFIX)/lib

# Where are your AFS binaries?
AFSWS	=	/usr/afsws
VOS	=	$(AFSWS)/etc/vos
FS	=	$(AFSWS)/bin/fs
TOKENS	=	$(AFSWS)/bin/tokens
PTS	=	$(AFSWS)/bin/pts

#-----------------------------------------------------------------------------#
#          END OF CONFIGURATION INFORMATION                                   #
#-----------------------------------------------------------------------------#

PRODUCT	=	ats
VERSION	=	1.4
SRCDIR	=	./src
BINS	=	repcheck.py volsanity.py volspot_check.py volspot.py \
		pts_checker.sh quota_partinfo.py vrm.py \
		gather_committal_stats.py
LIBS	=	afs_utils.py afs_vosexamine.py afs_voslistvol.py \
		afs_site.py afs_vldb.py afs_vospartinfo.py \
		afs_quotapartinfo.py afs_paths.py afs_space_usage_db.py \
		afs_pts.py getopt_afs.py afs_stats.py
MUNGER	=	./mungesrc

MUNGECMD	=	$(PYTHON) $(MUNGER) $(PYTHON) $(LIBDIR) $(VOS) $(FS) $(TOKENS) $(PTS)

all: bin $(BINS) $(LIBS)

install: all
	mkdir -p $(BINDIR) > /dev/null 2>&1
	mkdir -p $(LIBDIR) > /dev/null 2>&1
	cp ./bin/* $(BINDIR)
	chmod 755 $(BINDIR)/*
	cp ./lib/* $(LIBDIR)
	chmod 644 $(LIBDIR)/*

bin:
	mkdir bin > /dev/null 2>&1

lib:
	mkdir lib > /dev/null 2>&1


afs_paths.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_utils.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_vldb.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_vosexamine.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_vospartinfo.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_quotapartinfo.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_voslistvol.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_site.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_space_usage_db.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_pts.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

afs_stats.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@

getopt_afs.py: lib
	$(MUNGECMD) < $(SRCDIR)/lib/$@ > ./lib/$@


vrm.py: bin $(PYTHON)
	$(MUNGECMD) < $(SRCDIR)/$@ > ./bin/vrm

gather_committal_stats.py: bin $(PYTHON)
	$(MUNGECMD) < $(SRCDIR)/$@ > ./bin/gather_committal_stats

repcheck.py: bin $(PYTHON)
	$(MUNGECMD) < $(SRCDIR)/$@ > ./bin/repcheck

volsanity.py: bin $(PYTHON)
	$(MUNGECMD) < $(SRCDIR)/$@ > ./bin/volsanity

volspot_check.py: bin $(PYTHON)
	$(MUNGECMD) < $(SRCDIR)/$@ > ./bin/volspot_check

volspot.py: bin $(PYTHON)
	$(MUNGECMD) < $(SRCDIR)/$@ > ./bin/volspot

quota_partinfo.py: bin $(PYTHON)
	$(MUNGECMD) < $(SRCDIR)/$@ > ./bin/quota_partinfo

# Handled a bit differently
pts_checker.sh: bin
	cp $(SRCDIR)/$@ ./bin/pts_checker

tar: clean
	(cd ..; cp -rp $(PRODUCT)-$(VERSION) /tmp)
	find /tmp/$(PRODUCT)-$(VERSION) -name CVS -print | xargs rm -rf
	cd /tmp; \
	tar cvf $(PRODUCT)-$(VERSION).tar $(PRODUCT)-$(VERSION); \
	gzip $(PRODUCT)-$(VERSION).tar

clean:
	rm -rf ./bin ./lib

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
