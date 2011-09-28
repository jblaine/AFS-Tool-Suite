::PYTHON::

"""
    Query an "AFS partition usage policy" database for information about
    where (server:/partition) certain types of volumes should exist.

    If requested, report back on only the server and partition
    pairs which have N Kbytes free.  And finally, if specified with
    --randomone, run in CMU "Site" emulation mode and only spit out
    one of the valid sites with N Kbytes free (random pick for
    distributing volumes on a pool of server:/parts).
"""

sitelib = '::LIBDIR::'

# Writable cache location.  Set to '' to disable caching of info.
# We (our group) set cache_dir to an area that is 'rlidwka' by our sysadmin
# team.
cache_dir = '/afs/rcf/admin/temp/quota_partinfo_cache'

# How many hours before we disregard cached info?  Our volume creation
# and deletion frequency is pretty low, so cached data is usually fine
# for 72 hours or so.
cache_threshold_hours = 36

import sys, string, getopt, os
sys.path.append(sitelib)
import afs_space_usage_db

script = os.path.basename(sys.argv[0])

#-----------------------------------------------------------------------------

def Usage(cfp):
    print "Query the AFS partition layout database for information"
    print "about where certain types of volumes should be placed."
    print ""
    print "Arguments/Options:"
    print "   --type=<type>              Required.  Query sites of <type>.  Defined types"
    print "                              are listed below."
    print "   --kneeded=<size-in-K>      Optional.  Show only sites where <size-in-K> is"
    print "                              available."
    print "   --randomone                Optional.  Pick a random matching site and"
    print "                              display it instead of all matching sites."
    print "   --method=<method>          Optional.  Use <method> for free space"
    print "                              calculation.  Valid methods are vospartinfo and"
    print "                              quotapartinfo.  Default is vospartinfo."
    print "   --nocache                  Optional.  Disables cache reading for when"
    print "                              <method> is quotapartinfo."
    print "   --help"
    print ""
    outline = ''
    for s in cfp.getSections():
        if outline:
            outline = outline + ', ' + s
        else:
            outline = s
    print "Where type is one of:", outline
    sys.stdout.flush()
    sys.exit(1)

#-----------------------------------------------------------------------------

cfp = afs_space_usage_db.SpaceUsageDatabase()

category = ''
volsize = 0
randomone = 0
method = ''

# Parse the command-line arguments.  This should ideally use getopt_afs
optlist, args = getopt.getopt(sys.argv[1:], '', ['type=', 'randomone',
    'kneeded=', 'method=', 'nocache', 'help'])
for option, value in optlist:
    if option == '--type':
        if value not in cfp.getSections():
            print "%s: %s is not a defined type." % (script, value)
            sys.exit(1)
        category = value
    elif option == '--randomone':
        randomone = 1
    elif option == '--method':
        method = value
    elif option == '--nocache':
        cache_dir = ''
        cache_threshold_hours = 0
    elif option == '--help':
        Usage(cfp)
    elif option == '--kneeded':
        volsize = value
        try:
            volsize = int(volsize)
        except:
            print "%s: argument to --kneeded must be an integer." % script
            Usage(cfp)

if not category:
    print "%s: --type is a required argument." % script
    Usage(cfp)
if method and not volsize:
    print "%s: --method specified but --kneeded was not.  Makes no sense." % script
    Usage(cfp)
if not method:
    method = 'vospartinfo'
        
sites = []
sites = cfp.getVolspotSites(category, randomone, volsize, method, cache_dir, cache_threshold_hours)
for site in sites:
    print site

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
