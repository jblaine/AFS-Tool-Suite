import string, re, sys

sitelib = '::LIBDIR::'

sys.path.append(sitelib)
import afs_site, afs_paths, afs_utils

# For storing a cached copy of a VLDBData object containing the whole VLDB
WHOLE_VLDB = None

class VLDBEntry:

    def __init__(self, vname):
        """ C-struct-like class to hold the volume information available
            from a 'vos listvldb -name VOLNAME' call.

            * vname - A volume name
        """
        self.vname = vname
        self.ROsites = []    # List of refs to Site objects
        self.RWsite = None   # A single Site object
        self.ROID = ''       # The RO volume ID
        self.RWID = ''       # The RW volume ID
        self.BID = ''        # The backup volume ID

    def _setRWsite(self, site):
        """ Set the read-write site for this volume

            * site - A Site object
        """
        self.RWsite = site

    def getRWsite(self):
        return self.RWsite

    def addROsite(self, site):
        """ Add a read-only site to our list of read-only sites for this volume

            * site - A Site object
        """
        self.ROsites.append(site)

    def getROsites(self):
        """ Get the list of read-only sites for this volume """
        return self.ROsites

    def _setROID(self, id):
        """ Set the read-only volume ID

            * id - The volume's read-only volume ID
        """
        self.ROID = id

    def getROID(self):
        return self.ROID

    def _setRWID(self, id):
        """ Set the read-write volume ID

            * id - The volume's read-write volume ID
        """
        self.RWID = id

    def getRWID(self):
        return self.RWID

    def _setBID(self, id):
        """ Set the backup volume ID

            * id - The volume's backup volume ID
        """
        self.BID = id

    def getBID(self):
        return self.BID

    def getVName(self):
        return self.vname

    def printReport(self):
        pass


class VLDBData:

    def __init__(self):
        """ Represent some VLDB (Volume Location Database) data.
        """
        self.entries = []
        self.data = []
        self.loaded = 0

    def load(self, **kwargs):
        """ Load some VLDB information via 'vos listvldb'

            * kwargs - Keyword arguments in the form needed to be passed to the
              'vos listvldb' command.  For example, calling 
              VLDBData.load(server='foo', partition='c') will gather the
              VLDB data for all volumes on server 'foo' partition 'c'.  See
              the AFS 'vos' command for more information.

            Returns 0 on failure, 1 on successful load and parse
        """
        if self.loaded:
            return 1

        data = self._loadraw(kwargs)
        if not data:
            return 0

        newvol_re = re.compile('^([^ ]+)')
        siteRW_re = re.compile('^\s+server\s+(.+)\s+partition\s+(.+)\s+RW Site')
        siteRO_re = re.compile('^\s+server\s+(.+)\s+partition\s+(.+)\s+RO Site')
        RWline_re = re.compile('^\s+RWrite:\s+\d+\s+')

        curr = None
        for rawline in data:
            if string.find(rawline, 'VLDB entries') == 0:
                continue
            if string.find(rawline, 'vsu_ClientInit') == 0:
                continue
            if string.find(rawline, 'Total entries') == 0:
                continue
            if string.find(rawline, 'number of sites') >= 0:
                continue
            if len(string.strip(rawline)) <= 0:
                continue

            match = newvol_re.match(rawline)
            if match != None:
                # We found a new volume entry
                v = match.groups()[0]
                # Just do a quick check on the one we finished up...
                if curr != None:
                    if not curr.getRWsite():
                        print "Warning: Error parsing VLDB entry for %s" % \
                            curr.getVName()
                        sys.stdout.flush()
                curr = VLDBEntry(v)
                self.addEntry(curr)
                continue
            else:
                if curr:
                    match = RWline_re.match(rawline)
                    if match != None:
                        chunks = string.split(rawline)
                        for idx in range(len(chunks)):
                            piece = chunks[idx]
                            if piece == 'RWrite:':
                                curr._setRWID(chunks[idx + 1])
                            elif piece == 'ROnly:':
                                curr._setROID(chunks[idx + 1])
                            elif piece == 'Backup:':
                                curr._setBID(chunks[idx + 1])
                        continue
                    match = siteRW_re.match(rawline)
                    if match != None:
                        (server, partition) = match.groups()
                        s = afs_site.Site(server, partition)
                        curr._setRWsite(s)
                        continue
                    match = siteRO_re.match(rawline)
                    if match != None:
                        (server, partition) = match.groups()
                        s = afs_site.Site(server, partition)
                        curr.addROsite(s)

        self.loaded = 1
        return 1

    def _loadraw(self, kwargs):
        """ Call 'vos listvldb' and actually load the data we need.  Called
            by load().  Do not call this yourself.
        """
        cmd = afs_paths.AFS_vosCMD + ' listvldb '
        # Handy little trick courtesy of Justin Sheehy's brain
        for key in kwargs.keys():
            cmd = "%s -%s %s" % (cmd, key, kwargs[key])
        return afs_utils.RunCommandReturnOutput(cmd)


    def addEntry(self, entry):
        """ Add a VLDBEntry object to our list.

            * entry - a VLDBEntry object
        """
        self.entries.append(entry)

    def getEntries(self):
        """ Get a copy of our list of VLDBEntry objects """
        return self.entries[:]


    def printReport(self):
        """ Print an ASCII report of our data """
        for entry in self.getEntries():
            print 'VolumeName:', entry.getVName()
            print 'RW_ID:', entry.getRWID()
            print 'RO_ID:', entry.getROID()
            for site in entry.getROsites():
                print 'RO_SITE:', site
            print

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
