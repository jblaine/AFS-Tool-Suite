::PYTHON::

"""
    Script to make sure things are replicated that need to be.  This is
    not a library to be imported.

"""

# Where can we find the ATS libs?
sitelib = '::LIBDIR::'

import sys, re
sys.path.append(sitelib)
import afs_vldb, afs_paths, afs_space_usage_db

# Open up our AFS Space Usage Database.  For every section in it, see if
# the volume type is set as replicated.  If it is, take note of the volume
# name regexp/pattern
cfp = afs_space_usage_db.SpaceUsageDatabase()
crexps = []
for s in cfp.getSections():
    if cfp.isReplicated(s):
        r = cfp.getRegexp(s)
        crexps.append(re.compile(r))

v = afs_vldb.VLDBData()
v.load()

# For every VLDB entry, get the volume name and see if it matches one of our
# regexps from above.  If it does, then examine the number of sites the
# VLDB entry has and report if needed.
for e in v.getEntries():
    vname = e.getVName()
    for c in crexps:
        match = c.match(vname)
        if match != None:
            numsites = len(e.getROsites())
            if numsites < 1:
                print vname, "is not replicated and MIGHT need to be."

# For every VLDB entry, if the volume is replicated, make sure there is a
# RO on the same site as the RW!
for e in v.getEntries():
    good = 0
    if e.getROsites():
        rwsite = e.getRWsite()
        for rosite in e.getROsites():
            if repr(rwsite) == repr(rosite):
                good = 1
        if not good:
            print e.getVName(), "is not replicated on its RW site!"

for e in v.getEntries():
    good = 0
    rwsite = e.getRWsite()
    rw_server = rwsite.getServer()
    rw_partition = rwsite.getPartition()
    if e.getROsites():
        seen = []
        for rosite in e.getROsites():
            ro_server = rosite.getServer()
            if ro_server in seen:
                print "Whoa!  Multiple replicas for %s on same server!  Fix this." % e.getVName()
            else:
                seen.append(ro_server)
#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
