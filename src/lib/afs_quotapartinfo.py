import string, re, sys, os
import syslog

sitelib = '::LIBDIR::'
sys.path.append(sitelib)
import afs_utils
import afs_voslistvol, afs_vosexamine, afs_paths, afs_utils, afs_vospartinfo

class QuotaPartinfoEntry:

    def __init__(self, partition, kfree, ktotaldisk, kuncommitted):
        self.partition = partition
        self.kfree = long(kfree)
        self.ktotaldisk = long(ktotaldisk)
        self.kuncommitted = long(kuncommitted)
        self.cached = 0

    def getKFree(self):
        return self.kfree

    def getPartition(self):
        return self.partition

    def getKUncommitted(self):
        return self.kuncommitted

    def getKTotalDisk(self):
        return self.ktotaldisk

    def setCached(self, value=1):
        self.cached = value

    def isCached(self):
        return self.cached

class QuotaPartinfoData:

    def __init__(self, server, partition=''):
        """ Represent something like 'vos partinfo' but show K uncommitted
            instead of K free on disk.

            * server - An AFS file server hostname
            * partition - A partition on server (optional)
        """
        self.server = server
        self.partition = partition
        self.entries = []

    def load(self, cache_dir=None, cache_threshold_hours=0):
        """ Load the data based on the info passed to the constructor
            when the object was instantiated.  If cache_dir is specified,
            then try to read data from cache and use it if it exists and
            is not more than cache_threshold_hours old.  Also, if cache_dir
            is specified and the cache was not used, cache the new data
            when done.

            Returns 0 on failure, 1 on successful load and parse
        """

        #----------------------------------------------------------------
        # I apologize if you have to look at this code below at all.
        #----------------------------------------------------------------

        do_cache = 0 # Do cache reading or not?
        cache_loaded = 0 # Did we do it successfully?

        if self.getPartition():
            partonly = 1
        else:
            partonly = 0

        if cache_dir != None and cache_dir != '':
            if os.path.isdir(cache_dir):
                cache_file = cache_dir + '/' + self.getServer()
                if os.path.exists(cache_file):
                    hours_old = afs_utils.HoursOld(cache_file)
                    if hours_old > -1 and hours_old < cache_threshold_hours:
                        # We're committed.  We have a cache and we want it.
                        do_cache = 1

        if do_cache:
            cache_loaded = self.loadFromCache(cache_file)

        if cache_loaded:
            return 1
        else:
            # Call vos partinfo to get a starting point
            cmd = afs_paths.AFS_vosCMD + ' partinfo ' + self.getServer()
            if partonly:
                cmd = cmd + ' ' + self.getPartition()
            data = afs_utils.RunCommandReturnOutput(cmd)

            if not data:
                return 0

            whole_re = re.compile('^Free space on partition\s+(.+):\s+(\d+) K blocks out of total\s+(\d+)')

            for rawline in data:
                if string.find(rawline, 'vsu_ClientInit') == 0:
                    # Ignore permission warnings from 'vos partinfo'
                    continue

                if rawline == '\n':
                    continue

                match = whole_re.match(rawline)
                if match != None:
                    (part, kfree, ktotal) = match.groups()
                    kfree = long(kfree)
                    ktotal = long(ktotal)

                    # Now compute the K committed by getting a list of volume
                    # data from 'vos listvol', then looping over that
                    rwvolnames = [] # A list of the RW volume names
                    vlvdata = afs_voslistvol.VosListvolData(self.getServer(), part)
                    vlvdata.load()
                    kcommitted = 0L
                    for entry in vlvdata.getEntries():
                        if entry.getVType() == "RW":
                            rwvolnames.append(entry.getVName())
                    for entry in vlvdata.getEntries():
                        # Only add up RO and RW vols as BK vols take little
                        # space.  NOTE: This is kind of inaccurate, as I
                        # believe RO vols for a corresponding RW on the same
                        # partition do not take up the same amount of space
                        # again as the RW
                        if (entry.getVType() == "RW") or (entry.getVType() == 'RO'):
                            vname = entry.getVName()
                            if entry.getVType() == "RO":
                                tmp = string.replace(vname, '.readonly', '')
                                if tmp in rwvolnames:
                                    # Skip it, it's a RO with RW on same part.
                                    continue
                            vedata = afs_vosexamine.VosExamineData(vname)
                            vedata.load()
                            if vedata.getBusy():
                                print "Warning: Quota information for %s is unavailable because the volume is busy.  Calculated uncommitted space may not be precise." % vname
                                continue
                            q = vedata.getMaxQuota()
                            if not q:
                                # If a volume has no quota (yuck), then use the
                                # entire part. size as the quota for that vol
                                q = ktotal
                                print "Warning: volume %s has unlimited quota and is being counted as a %dK volume quota." % (vname, ktotal)
                            kcommitted = kcommitted + q
                    kuncommitted = ktotal - kcommitted
                    entry = QuotaPartinfoEntry(part, kfree, ktotal, kuncommitted)
                    self.addEntry(entry)
                    continue

            if len(self.getEntries()) <= 0:
                return 0
            if cache_dir != None and cache_dir != '':
                if os.path.isdir(cache_dir):
                    cache_file = cache_dir + '/' + self.getServer()
                    retval = self.writeCache(cache_file)
            return 1

    def printReport(self, verbose=0):
        """ Print an ASCII report to standard output """
        for e in self.getEntries():
            partition = afs_utils.FullPartitionName(e.getPartition())
            if verbose:
                if e.isCached():
                    cached_message = ' [CACHED]'
                else:
                    cached_message = ''
                print "Uncommitted space on partition %s%s: %d K blocks out of total %d" % (partition, cached_message, e.getKUncommitted(), e.getKTotalDisk())
            else:
                print "Uncommitted space on partition %s: %d K blocks out of total %d" % (partition, e.getKUncommitted(), e.getKTotalDisk())

    def printSyslogReport(self, verbose=0, logfacility=syslog.LOG_KERN, logpri=syslog.LOG_INFO):
        """ Print an ASCII report to syslog """
        for e in self.getEntries():
            partition = afs_utils.FullPartitionName(e.getPartition())
            syslog.openlog('afsquotaspace', 0, logfacility)
            if verbose:
                if e.isCached():
                    cached_message = ' [CACHED]'
                else:
                    cached_message = ''
                syslog.syslog(logpri, "%s - Uncommitted space on partition %s%s: %d K blocks out of total %d" % (self.getServer(), partition, cached_message, e.getKUncommitted(), e.getKTotalDisk()))
            else:
                syslog.syslog(logpri, "%s - Uncommitted space on partition %s: %d K blocks out of total %d" % (self.getServer(), partition, e.getKUncommitted(), e.getKTotalDisk()))


    def getServer(self):
        return self.server

    def getPartition(self):
        return self.partition


    def addEntry(self, entry):
        self.entries.append(entry)

    def getEntries(self):
        return self.entries

    def loadFromCache(self, cache_file):
        # First build up a list of all partitions that the server in
        # question actually has.
        vpidata = afs_vospartinfo.VosPartinfoData(self.getServer())
        vpidata.load()
        allpartitions = []
        for e in vpidata.getEntries():
            allpartitions.append(e.getPartition())

        # Now see what the cache file has
        cfile = open(cache_file, 'r')
        afs_utils.LockFile(cfile)
        cfileparts = 0
        for i in cfile.readlines():
            cfileparts = cfileparts + 1
        if cfileparts < len(allpartitions):
            # For now, don't deal with partial cache files
            return 0
        cfile.close()
        afs_utils.UnlockFile(cfile)

        cfile = open(cache_file, 'r')
        afs_utils.LockFile(cfile)
        asked_partition = ''
        if self.getPartition():
            asked_partition = afs_utils.FullPartitionName(self.getPartition())
        for cfileline in cfile.readlines():
            try:
                (part, kfree, ktotal, kuncommitted) = string.split(cfileline)
            except:
                # Corrupt cache data
                afs_utils.UnlockFile(cfile)
                cfile.close()
                return 0
            entry = QuotaPartinfoEntry(part, kfree, ktotal, kuncommitted)
            if asked_partition:
                if part == asked_partition:
                    entry.setCached(1)
                    self.addEntry(entry)
                    break
            else:
                entry.setCached(1)
                self.addEntry(entry)
        cfile.close()
        afs_utils.UnlockFile(cfile)
        return 1

    def writeCache(self, cache_file):
        outlines = []
        asked_partition = ''

        if self.getPartition():
            theentry = self.getEntries()[0]
            asked_partition = afs_utils.FullPartitionName(self.getPartition())
            # Read the whole cache file in and replace the one line that needs
            # updating in the cache
            try:
                foundpart = 0
                cfile = open(cache_file, 'r')
                afs_utils.LockFile(cfile)
                for cfl in cfile.readlines():
                    (part, kfree, ktotal, kuncommitted) = string.split(cfl)
                    if part == asked_partition:
                        foundpart = 1
                        outline = "%s %d %d %d\n" % (asked_partition,
                            theentry.getKFree(),
                            theentry.getKTotalDisk(),
                            theentry.getKUncommitted())
                    else:
                        outline = cfl
                    outlines.append(outline)
                cfile.close()
                afs_utils.UnlockFile(cfile)
                if not foundpart:
                    outline = "%s %d %d %d\n" % (asked_partition,
                        theentry.getKFree(),
                        theentry.getKTotalDisk(),
                        theentry.getKUncommitted())
                    outlines.append(outline)
            except IOError:
                # We have no file to read and substitute, so our data to write
                # will be one line, the new one.
                outline = "%s %d %d %d\n" % (asked_partition,
                    theentry.getKFree(), theentry.getKTotalDisk(),
                    theentry.getKUncommitted())
                outlines.append(outline)
        else:
            try:
                os.unlink(cache_file)
            except:
                pass
            for e in self.getEntries():
                part = afs_utils.FullPartitionName(e.getPartition())
                outline = "%s %d %d %d\n" % (part, e.getKFree(), e.getKTotalDisk(), e.getKUncommitted())
                outlines.append(outline)

        # Write the data
        try:
            cfile = open(cache_file, 'w')
        except:
            return 0
        afs_utils.LockFile(cfile)
        for l in outlines:
            cfile.write(l)
        cfile.close()
        afs_utils.UnlockFile(cfile)
        return 1

if __name__ == '__main__':
    qpidata = QuotaPartinfoData('bunky', 'c')
    if qpidata.load():
        qpidata.printReport()
    else:
        print "ERROR: Test failed."

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#

