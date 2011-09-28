import string, re, sys

sitelib = '::LIBDIR::'

sys.path.append(sitelib)
import afs_site, afs_paths, afs_utils

class VosListvolEntry:

    def __init__(self, vname, vid, vtype, kused, status, server, partition):
        """ C-struct-like class to hold a single volume's information as seen
            in the output of a 'vos listvol' command.

            * vname - A volume name
            * vid - A volume ID
            * vtype - The volume type (BK/RW/RO)
            * kused - The K used by this volume
            * status - The volume's online status
            * server - A hostname
            * partition - An AFS 'vice' partition name
        """
        self.vname = vname
        self.vid = str(vid)
        self.vtype = vtype
        self.kused = kused
        self.status = status
        self.site = afs_site.Site(server, partition)

    def getKUsed(self):
        return self.kused

    def getVType(self):
        return self.vtype

    def getStatus(self):
        return self.status

    def getSite(self):
        """ Get the Site object associated with this VosListvolEntry """
        return self.site

    def getVName(self):
        """ Get the volume name """
        return self.vname

    def getVID(self):
        """ Get the volume ID """
        return self.vid

class VosListvolData:

    def __init__(self, server, partition=''):
        """ Represent some 'vos listvol' data.

            * server - A hostname
            * partition - An AFS 'vice' partition (optional)
        """
        self._setServer(server)
        self._setPartition(partition)
        self.entries = []
        sys.stdout.flush()
        self.loaded = 0

    def load(self):
        """ Load the data based on the server (and possibly partition) passed
            to the constructor when the object was instantiated.

            Returns 0 on failure, 1 on successful load and parse 
        """
        if self.loaded:
            return 1

        data = self._loadraw()
        if not data:
            return 0

        vname_re = re.compile('^([^ ]+)\s+(\d+)\s+([ROWBK][ROWBK])\s+([0-9]+)\sK\s+(.+ine)$')
        part_re = re.compile("^Total number of volumes on server .+ partition (/vicep.+):\s+\d+")

        partition = self.getPartition()
        if not partition:
            allparts = 1
        else:
            allparts = 0

        for rawline in data:
            if rawline == '\n':
                continue
            if string.find(rawline, 'Total volumes') == 0:
                continue
            if string.find(rawline, 'vsu_ClientInit') == 0:
                continue

            if allparts:
                match = part_re.match(rawline)
                if match != None:
                    partition = match.groups()
                    continue

            match = vname_re.match(rawline)
            if match != None:
                if not partition:
                    return 0
                (v, vid, vtype, kused, status) = match.groups()
                vlve = VosListvolEntry(v, vid, vtype, kused, status,
                    self.getServer(), partition)
                self.addEntry(vlve)
        self.loaded = 1
        return 1

    def _loadraw(self):
        """ Call 'vos listvol' and actually load the data we need.  Called by
            load().  Do not call this yourself. 
        """
        cmd = afs_paths.AFS_vosCMD + ' listvol ' + self.getServer()
        if self.getPartition():
            cmd = cmd + ' ' + self.getPartition()
        return afs_utils.RunCommandReturnOutput(cmd)


    def printReport(self):
        """ Print an ASCII report to standard output """
        for v in self.getVNames():
            print v
        print


    def _setServer(self, server):
        self.server = server

    def getServer(self):
        return self.server


    def _setPartition(self, partition):
        self.partition = partition

    def getPartition(self):
        return self.partition


    def addEntry(self, entry):
        """ Add a VosListvolEntry object to our list.

            * entry - a VosListvolEntry object
        """
        self.entries.append(entry)

    def getEntries(self):
        """ Get a copy of our list of VosListvolEntry objects """
        return self.entries[:]

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
