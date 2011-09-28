::PYTHON::

"""
    Query the AFS partition layout database for information about
    where certain types of volumes should exist and then check to make
    sure that no sites (server:partition) have volumes on them that
    should not be there.  Report if volumes are found out of place.
"""

import sys, string, re, os
sitelib = '::LIBDIR::'
sys.path.append(sitelib)
import afs_vldb, afs_space_usage_db

debugging = 0

#=============================================================================

cfp = afs_space_usage_db.SpaceUsageDatabase()

sites = {}
sitelist = []
allregexps = []
wrongplace = {}
badunknown = {}

script = os.path.basename(sys.argv[0])

def DEBUG(message):
    if debugging:
        sys.stderr.write("DEBUG: " + message + '\n')

# Build our 'sites' dictionary.  The keys are server:partition and the
# values are a list of regexps that should be found on that server:partition.
for section in cfp.getSections():
    regexp = ''
    sitelist = []
    regexp = re.compile(cfp.getRegexp(section))
    sitelist = cfp.getSiteValues(section)
    if not regexp:
        print "%s : Warning - No regexp found for section %s in %s" % (script, section, configfile)
        continue
    for site in sitelist:
        if sites.has_key(site):
            sites[site].append(regexp)
        else:
            sites[site] = []
            sites[site].append(regexp)

    # Keep a list of all regexps we found
    allregexps.append(regexp)

for site in sites.keys():
    (server, partition) = string.split(site, ':')
    vldb = afs_vldb.VLDBData()
    if not vldb.load(server=server, partition=partition):
        print "%s : Problem loading VLDB data for site %s" % (script, site)
        sys.stdout.flush()
        continue
    okay = 0
    wrongflag = 0
    for entry in vldb.getEntries():
        vname = entry.getVName()
        # See if the volume name matches any of the regexps for allowed vols
        # on this site.
        for r in sites[site]:
            match = r.match(vname)
            if match != None:
                okay = 1
        # If we didn't find a match above, it doesn't automatically mean that
        # the volume is in a KNOWN wrong spot, it could just be that the
        # volume has a name that has not been accounted for in the volspot
        # database.  So, we look at ALL volspot-database-defined regexps
        # and if we find a match there, then the volume is in a KNOWN
        # wrong spot, otherwise the volume is just oddly named.
        if not okay:
            for r in allregexps:
                match = r.match(vname)
                if match != None:
                    wrongplace[vname] = site
                    wrongflag = 1
            if not wrongflag:
                badunknown[vname] = site

if len(wrongplace) > 0:
    print
    print "The following volumes were found on the displayed site and"
    print "this is DEFINITELY not where the volume should be."
    print
    for badvol in wrongplace.keys():
        print "     ", badvol, "on", wrongplace[badvol]

if len(badunknown) > 0:
    print
    print "The following volumes were found on the displayed site and"
    print "this is MIGHT NOT be where the volume should be.  They did"
    print "not match any regular expression in", configfile
    print
    for badvol in badunknown.keys():
        print "     ", badvol, "on", badunknown[badvol]

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
