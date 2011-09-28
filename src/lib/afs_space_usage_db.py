::PYTHON::

# This can be overridden with the constructor for SpaceUsageDatabase()
configfile = '/afs/rcf/admin/etc/afs_layout.txt'

sitelib = '::LIBDIR::'

import sys, ConfigParser, string
sys.path.append(sitelib)
from afs_vospartinfo import VosPartinfoData

class SpaceUsageDatabase:
    """
        Actions and data associated with a ConfigParser format file set up
        to act as our AFS Space Usage Policy Database.
    """
    def __init__(self, configfilename=configfile):
        self.cfp = ConfigParser.ConfigParser()
        self.cfp.read(configfile)
        self.internal_options = ['__name__', 'regexp', 'replicated']

    def isReplicated(self, category):
        """
            Find out whether or not a certain category of volume is supposed
            to be replicated or not.  Returns 1 if replicated, 0 if not.
        """
        for o in self.getOptions(category):
            if o == 'replicated':
                val = self.getValue(category, o)
                if val == 'yes':
                    return 1
                elif val == 'YES':
                    return 1
                elif val == 'Yes':
                    return 1
                elif val == 'Y':
                    return 1
                elif val == 'y':
                    return 1
        return 0
        
    def getSiteValues(self, category):
        """
            Get all non internal option values and return a list of them
        """
        good = []
        for o in self.getOptions(category):
            if o not in self.internal_options:
                good.append(self.getValue(category, o))
        return good

    def getRegexp(self, category):
        """
            Get the regexp value for a given category of volume.  Returns
            a string.
        """
        for o in self.getOptions(category):
            if o == 'regexp':
                return self.getValue(category, o)
        return ''

    def getSections(self):
        """
            Return a list of category names found
        """
        return self.cfp.sections()

    def getOptions(self, category):
        """
            Return a list of option names for the specified category
        """
        return self.cfp.options(category)

    def getValue(self, category, option):
        """
            Fetch a value for the option specified in category
        """
        return self.cfp.get(category, option)

    def getVolspotSites(self, category, randomone, size, method='vospartinfo', cache_dir=None, cache_threshold_hours=0):
        """
            Query the AFS Usage Policy Database in volspot-fashion

            * category - The type of volume to look up
            * randomone - A boolean flag stating whether or not a single site
              should be returned (pass in 1 for randomone) or not (pass in 0)
            * size - The amount of space needed.  Pass in 0 if you want all
              sites returned, regardless of free space.
            * method - The means by which free space is calculated.  Can be one
              of two strings: 'vospartinfo' or 'quotapartinfo'.  Specifying
              'vospartinfo' will use a simple 'vos partinfo' command to see how
              much free space is on the site.  Specifying 'quotapartinfo' will
              use the actual uncommitted space (quota-wise) as free space.
            * cache_dir - The cache directory to use for quotapartinfo data
            * cache_threshold_hours - The number of hours before the cache
              files are not used.
        """
        allvalues = []
        allvalues = self.getSiteValues(category)
        allvalues.sort()

        if not size and not randomone:
            # No size required, return all of them
            return allvalues
        elif not size and randomone:
            # No size required, but we need a random one (ala CMU Site)
            import random
            choice = random.choice(allvalues)
            return [choice]
        elif size:
            goodones = []
            quotagoodones = []

            # We need to check size.
            for v in allvalues:
                (server, partition) = string.split(v, ':')
                if not partition:
                    print "afs_space_usage_db::getVolspotSites() : Failure - partition not set.  Could be a bad config file.  Line in config file was: %s" % v
                    sys.exit(1)
                # Always do this, even if the user requested quotapartinfo.
                # Running 'vos partinfo' is faster, and if you don't have the
                # actual free space on the disk, then you sure don't have it
                # quota-non-committal-wise.  So we do this to filter out and
                # only have to get QuotaPartinfoData for minimal sites.
                vpi = VosPartinfoData(server, partition)
                if vpi.load() == 0:
                    continue
                entry = vpi.getEntries()[0]
                if int(entry.getKFree()) > size:
                    goodones.append(v)

            if method == 'vospartinfo':
                if randomone:
                    import random
                    return [random.choice(goodones)]
                else:
                    return goodones
            elif method == 'quotapartinfo':
                from afs_quotapartinfo import QuotaPartinfoData
                for g in goodones:
                    (server, partition) = string.split(g, ':')
                    qpi = QuotaPartinfoData(server, partition)
                    qpi.load(cache_dir, cache_threshold_hours)
                    entry = qpi.getEntries()[0]
                    if int(entry.getKUncommitted()) > size:
                        quotagoodones.append(g)
                if randomone:
                    import random
                    choice = random.choice(quotagoodones)
                    return [choice]
                else:
                    return quotagoodones
            else:
                print "afs_space_usage_db:getVolspotSites() : Failure - invalid free space calculation method specified: %s" % method
                sys.exit(1)

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
