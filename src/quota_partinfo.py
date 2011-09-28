::PYTHON::

"""
    Quota-committal-based version of 'vos partinfo'

    This tool displays output similar to the output of 'vos partinfo'
    but instead of showing 'K free' on a partition, it shows the number
    of K uncommitted quota-wise.  That is, when volumes are created,
    they are assigned a quota, and as such, that space should be technically
    marked as unavailable space, even if the volume is not full of data.
    This tool will show you how much space is "truly" free for your
    committal to a new or different volume on the same partition.
"""

sitelib = '::LIBDIR::'

# Writable cache location.  Set to '' to disable ALL caching operations.
# We (our group) set cache_dir to an area that is 'rlidwka' by our sysadmin
# team's PTS group.
cache_dir = '/afs/rcf/admin/temp/quota_partinfo_cache'

# How many hours before we disregard cached info?  Our volume creation
# and deletion frequency is pretty low, so cached data is usually fine
# for several days for us.
cache_threshold_hours = 36

import sys, re
sys.path.append(sitelib)

try:
    import afs_quotapartinfo, afs_site, getopt_afs
except ImportError:
    print "Failed to import AFS Tool Suite libraries from", sitelib
    sys.exit(1)

def Usage():
    print "Usage: quota_partinfo [options]"
    print ""
    print "           -server <server>         (required)"
    print "           -partition <partition>   (optional)"
    print "           -nocache                 (optional, disable cache reading)"
    print "           -verbose                 (optional, label cached results as such)"
    print "           -syslog                  (optional, syslog results)"
    print "           -help                    ..."
    print ""
    sys.exit(1)

verboseflag = 0
syslogflag = 0

server = ''
partition = ''

opts = ['server+', 'partition=', 'nocache', 'verbose', 'help', 'syslog']
try:
    (pairs, restargs) = getopt_afs.getopt(sys.argv[1:], opts)
except getopt_afs.error:
    Usage()
for pair in pairs:
    (option, argument) = pair
    if option == '-server':
        server = argument
    elif option == '-partition':
        partition = argument
    elif option == '-nocache':
        cache_threshold_hours = 0
    elif option == '-verbose':
        verboseflag = 1
    elif option == '-syslog':
        syslogflag = 1
    elif option == '-help':
        Usage()

qpidata = afs_quotapartinfo.QuotaPartinfoData(server, partition)
if qpidata.load(cache_dir, cache_threshold_hours):
    if syslogflag:
        qpidata.printSyslogReport(verboseflag)
    else:
        qpidata.printReport(verboseflag)
else:
    print "ERROR: Could not load/gather data."
    sys.exit(1)

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
