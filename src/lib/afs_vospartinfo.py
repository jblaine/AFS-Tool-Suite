import string, re, sys

sitelib = '::LIBDIR::'
sys.path.append(sitelib)
import afs_paths, afs_utils

class VosPartinfoEntry:

    def __init__(self, part, kfree, ktotaldisk):
        self.partition = part
        self.kfree = long(kfree)
        self.ktotaldisk = long(ktotaldisk)

    def getPartition(self):
        return self.partition

    def getKFree(self):
        return self.kfree

    def getKTotalDisk(self):
        return self.ktotaldisk


class VosPartinfoData:

    def __init__(self, server, partition=''):
        """ Represent some 'vos partinfo' data.

            * server - An AFS file server hostname
            * partition - A partition on server (optional)
        """
        self.server = server
        self.partition = partition
        self.entries = []

    def load(self):
        """ Load the data based on the info passed to the constructor
            when the object was instantiated.

            Returns 0 on failure, 1 on successful load and parse
        """
        data = self._loadraw()
        if not data:
            return 0

        whole_re = re.compile('^Free space on partition\s+(.+):\s+(\d+) K blocks out of total\s+(\d+)')
        found = 0
        for rawline in data:
            if string.find(rawline, 'vsu_ClientInit') == 0:
                continue

            if rawline == '\n':
                continue
            match = whole_re.match(rawline)
            if match != None:
                (part, kfree, ktotal) = match.groups()
                entry = VosPartinfoEntry(part, kfree, ktotal)
                self.addEntry(entry)
                found = 1
                continue

        return found

    def _loadraw(self):
        """ Call 'vos partinfo' and actually load the data we need.  Called by
            load().  Do not call this yourself. 
        """
        cmd = afs_paths.AFS_vosCMD + ' partinfo -server ' + self.getServer()
        if self.getPartition():
            cmd = cmd + ' -partition ' + self.getPartition()
        return afs_utils.RunCommandReturnOutput(cmd)

    def printReport(self):
        """ Print an ASCII report to standard output """
        for e in self.getEntries():
            partition = afs_utils.FullPartitionName(e.getPartition())
            print "Free space on partition %s: %d K blocks out of total %d" \
                % (partition, e.getKFree(), e.getKTotalDisk())


    def getServer(self):
        return self.server

    def getPartition(self):
        return self.partition


    def addEntry(self, entry):
        self.entries.append(entry)

    def getEntries(self):
        return self.entries

if __name__ == '__main__':
    vpidata = VosPartinfoData('bunky')
    vpidata.load()
    vpidata.printReport()

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
