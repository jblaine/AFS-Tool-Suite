::PYTHON::

# Report on per-partition stats for every file server.  Ideally meant to
# be used via cron and dumped into a unique (dated makes sense) filename
# for later use as you see fit (generating graphs for capacity planning, etc)
#
# Lines are of the form:
#
#    server   partition   ktotaldisk   kfree   kuncommitted  %committed
#
# WARNING: This will iteratively 'vos examine' every volume you have on
#          every AFS file server in your cell.  In other words, you
#          probably only want to run it once a week maximum, and perhaps
#          early in morning.

# Writable cache location.  Set to '' to disable ALL caching operations.
# We (our group) set cache_dir to an area that is 'rlidwka' by our sysadmin
# team's PTS group.
cache_dir = '/afs/rcf/admin/temp/quota_partinfo_cache'

# How many hours before we disregard cached info?  For this script, you
# will want a LOW setting here, even 0 might make sense...  You're trying
# to gather accurate up-to-date stats, not data that's 4 days old.
cache_threshold_hours = 72

sitelib = '::LIBDIR::'

import sys
sys.path.append(sitelib)
import afs_utils, afs_quotapartinfo

serverlist = afs_utils.GetFileServers()

for server in serverlist:
    qpi = afs_quotapartinfo.QuotaPartinfoData(server)
    if not qpi.load(cache_dir, cache_threshold_hours):
        sys.stderr.write("ERROR: Could not gather data for %s" % server)
        continue
    for entry in qpi.getEntries():
        kcommitted = entry.getKTotalDisk() - entry.getKUncommitted()
        perccommitted = (kcommitted * 100) / entry.getKTotalDisk()
        print "%s %s %d %d %d" % (server, entry.getPartition(), 
            entry.getKTotalDisk(), entry.getKFree(), perccommitted)
