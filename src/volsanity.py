::PYTHON::

"""
    WARNING: This stuff called in this code does a very brute-force iterative
             examination of your VLDB and your volumes on disk.  This
             script isn't something you want to be running everyday.
"""

sitelib = '::LIBDIR::'

import sys
sys.path.append(sitelib)
import afs_vldb, afs_utils

vldbdata = afs_vldb.VLDBData()
print "Checking quotas..."
print
afs_utils.CheckQuotas(vldbdata)
print
print "Examining every volume in VLDB for inconsistency..."
print
afs_utils.VLDB_VosExamine()
print
print "Searching for volumes which exist on disk but not in VLDB..."
print
afs_utils.VosListvol_VosExamine_Check()

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
