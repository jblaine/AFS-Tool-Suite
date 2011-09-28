import string, re, sys

sitelib = '::LIBDIR::'
sys.path.append(sitelib)
import afs_site, afs_vldb, afs_paths, afs_utils

class VosExamineData:

    def __init__(self, vname):
        """ Represent some 'vos examine' data.

            * vname - A volume name
        """
        self.vname = vname
        self.vldbentry = afs_vldb.VLDBEntry(vname)
        self.maxquota = -1
        self.creationdate = ''
        self.lastupdate = ''
        self.lastday_accesses = -1
        self.state = ''
        self.kused = -1
        self.busy = 0

    def load(self):
        """ Load the data based on the volume name passed to the constructor
            when the object was instantiated.
        """
        data = self._loadraw(self.getVName())
        if not data:
            return 0

        # The next 60 lines of code probably couldn't be anymore inelegant.
        vname_re = re.compile('^[^ ]+\s+\d+\s+R[OW]\s+(\d+)\s+K\s+(.+line)$')
        siteRW_re = re.compile('^\s+server\s+(.+)\s+partition\s+(.+)\s+RW Site')
        siteRO_re = re.compile('^\s+server\s+(.+)\s+partition\s+(.+)\s+RO Site')
        quota_re = re.compile('^\s+MaxQuota\s+(\d+)\s+K')
        creation_re = re.compile('^\s+Creation\s+(.+)$')
        lastup_re = re.compile('^\s+Last Update\s+(.+)$')
        accesses_re = re.compile('^\s+(\d+)\s+accesses in the past.+$')
        busy_re = re.compile('^.+Volume\s+(\d+)\s+is busy')

        # Sigh.  Loop over the returned data once and gather only the
        # returned data we care about because doing a 'vos examine'
        # on a .readonly volume will return information for all of the
        # replicas, etc.  We only care about the data/entry that has the
        # sites listed in a row (resembles a normal 'vos examine' done on
        # a RW volume.
        master_entry_found = 0
        tmplines = []
        for rawline in data:
            if string.find(rawline, 'vsu_ClientInit') == 0:
                continue

            match = vname_re.match(rawline)
            if match != None:
                # We already found our master entry, don't even go on
                if master_entry_found:
                    break
                else:
                    # Reset
                    tmplines = [rawline]
                    continue

            match = siteRW_re.match(rawline)
            if match != None:
                master_entry_found = 1
                tmplines.append(rawline)
                continue

            tmplines.append(rawline)
            
        ve = self.getVLDBEntry()
        for rawline in tmplines:
            if len(string.strip(rawline)) == 0:
                continue

            if string.find(rawline, 'number of sites') >= 0:
                continue

            if string.find(rawline, 'RWrite:') > 0:
                chunks = string.split(rawline)
                idx = 0
                for piece in chunks:
                    if piece == 'RWrite:':
                        ve._setRWID(chunks[idx + 1])
                    elif piece == 'ROnly:':
                        ve._setROID(chunks[idx + 1])
                    elif piece == 'Backup:':
                        ve._setBID(chunks[idx + 1])
                    idx = idx + 1
                continue

            match = busy_re.match(rawline)
            if match != None:
                vid = match.groups()[0]
                self._setBusy(1)
                continue

            match = siteRW_re.match(rawline)
            if match != None:
                (server, partition) = match.groups()
                s = afs_site.Site(server, partition)
                ve._setRWsite(s)
                continue

            match = siteRO_re.match(rawline)
            if match != None:
                (server, partition) = match.groups()
                s = afs_site.Site(server, partition)
                ve.addROsite(s)
                continue

            match = vname_re.match(rawline)
            if match != None:
                (k, s) = match.groups()
                k = long(k)
                self._setKUsed(k)
                self._setState(s)
                continue

            match = quota_re.match(rawline)
            if match != None:
                q = match.groups()[0]
                self._setMaxQuota(q)
                continue

            match = creation_re.match(rawline)
            if match != None:
                c = match.groups()[0]
                self._setCreationDate(c)
                continue

            match = lastup_re.match(rawline)
            if match != None:
                l = match.groups()[0]
                self._setLastUpdate(c)
                continue

            match = accesses_re.match(rawline)
            if match != None:
                a = match.groups()[0]
                self._setLastDayAccesses(a)
                continue

        if (self.getMaxQuota() < 0) or (self.getLastDayAccesses() < 0) or (self.getKUsed() < 0):
            if not self.getBusy() and self.getState():
                print "VosExamineData::load(): Bad data found, internal dumps follow:"
                self.printReport()
                sys.stdout.flush()
                print
                print "Data from 'vos examine' being seen internally:"
                for rawline in data:
                    l = string.rstrip(rawline)
                    print l
                sys.stdout.flush()
                sys.exit(1)

        return 1

    def _loadraw(self, vname):
        """ Call 'vos examine' and actually load the data we need.  Called by
            load().  Do not call this yourself. 

            * vname - A volume name
        """
        cmd = afs_paths.AFS_vosCMD + ' examine ' + vname
        return afs_utils.RunCommandReturnOutput(cmd)

    def printReport(self):
        """ Print an ASCII report to standard output """
        ve = self.getVLDBEntry()
        print 'VolumeName:', ve.getVName()
        print 'Quota:', str(self.getMaxQuota())
        print 'State:', self.getState()
        print 'K_Used:', str(self.getKUsed())
        print 'Created:', self.getCreationDate()
        print 'Last_Updated:', self.getLastUpdate()
        print 'Accesses_In_Last_Day:', self.getLastDayAccesses()
        print 'Busy?:', str(self.getBusy())
        print 'RW_ID:', ve.getRWID()
        print 'RO_ID:', ve.getROID()
        for site in ve.getROsites():
            print 'RO_SITE:', site
        print

    def getVLDBEntry(self):
        return self.vldbentry

    def _setMaxQuota(self, quota):
        self.maxquota = long(quota)

    def getMaxQuota(self):
        return self.maxquota

    def _setCreationDate(self, datestring):
        self.creationdate = datestring

    def getCreationDate(self):
        return self.creationdate

    def _setLastUpdate(self, datestring):
        self.lastupdate = datestring

    def getLastUpdate(self):
        return self.lastupdate

    def _setLastDayAccesses(self, num):
        self.lastday_accesses = num

    def getLastDayAccesses(self):
        return self.lastday_accesses

    def _setState(self, statestring):
        self.state = statestring

    def getState(self):
        """ Get the state of the volume (On-Line or Off-Line) """
        return self.state

    def _setKUsed(self, k):
        self.kused = long(k)

    def getKUsed(self):
        """ Get the number of 1-kilobyte-sized blocks used by this volume """
        return self.kused

    def getVName(self):
        return self.vname

    def _setBusy(self, flag):
        self.busy = flag

    def getBusy(self):
        return self.busy

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
