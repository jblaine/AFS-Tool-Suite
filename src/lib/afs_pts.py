import string, re, sys

sitelib = '::LIBDIR::'

sys.path.append(sitelib)
import afs_paths, afs_utils

class PTSPrivacyFlags:
    possibleflags = 'SOMARsomar'

    def __init__(self, flagstring=''):
        """ C-struct-like class to hold PTS Privacy Flags

            * flagstring - A 5-character string representing the privacy
              flags (as found in the output of pts examine)
        """
        for i in list(self.possibleflags):
            setattr(self, i, 0)
        if flagstring:
            for flag in list(flagstring):
                if flag == '-':
                    continue
                if hasattr(self, flag):
                    setattr(self, flag, 1)

    def setFlagValue(self, flag, value):
        """
            Set a PTS Privacy flag on or off

            * flag - The single-letter flag to change
            * value - 0 or 1 (off or on respectively)
        """
        if hasattr(self, flag) and ((value == 0) or (value == 1)):
            setattr(self, flag, value)
            return value
        else:
            return -1
        
    def getFlagValue(self, flag):
        """
            Get a flag's current value
        """
        return getattr(self, flag)

    def __repr__(self):
        good = ''
        for f in list(self.possibleflags):
            val = getattr(self, f)
            if val == 1:
                good = good + f
        outlen = len(self.possibleflags) / 2
        diff = outlen - len(good)
        return good + '-' * diff
        
class PTSExamineData:

    def __init__(self, name):
        """ Represent some 'pts examine' data.

            * name - The PTS name to lookup in the PTS database
        """
        # The names of these attributes must be this way.  See load()
        self.name = name
        self.id = 0
        self.owner = ''
        self.creator = ''
        self.membership = 0
        self.flags = None
        self.groupquota = 0

    def load(self):
        """ Load the data based on the PTS name passed to the constructor
            when the object was instantiated.

            Returns 0 on failure, 1 on successful load and parse 
        """

        data = self._loadraw()
        if not data:
            return 0

        for rawline in data:
            if string.find(rawline, 'libprot:') == 0:
                continue
            strippedline = string.strip(rawline)
            linechunks = string.split(strippedline, ',')
            for c in linechunks:
                if len(c) < 3:
                    continue
                (item, value) = string.split(c, ': ')
                value = string.strip(value)
                item = string.replace(item, ' ', '')
                item = string.lower(item)
                if value[-1] == '.':
                    value = value[:-1]
                if hasattr(self, item) and item != 'flags':
                    setattr(self, item, value)
                    continue
                if item == 'flags':
                    self.flags = PTSPrivacyFlags(value)

        return 1

    def _loadraw(self):
        """ Call 'pts examine' and actually load the data we need.  Called by
            load().  Do not call this yourself. 
        """
        cmd = afs_paths.AFS_ptsCMD + ' examine -name ' + self.getName()
        return afs_utils.RunCommandReturnOutput(cmd)

    def printReport(self):
        print "Name:", self.getName()
        print "ID:", self.getID()
        print "Owner:", self.getOwner()
        print "Creator:", self.getCreator()
        print "Flags:", self.getPrivacyFlags()
        print "Membership:", self.getMembership()
        print "Group Creation Quota:", self.getGroupQuota()

    def getName(self):
        return self.name

    def getID(self):
        return self.id

    def getOwner(self):
        return self.owner

    def getCreator(self):
        return self.creator

    def getPrivacyFlags(self):
        return self.flags

    def getMembership(self):
        return self.membership

    def getGroupQuota(self):
        return self.groupquota

if __name__ == '__main__':
    p = PTSExamineData('jblaine')
    p.load()
    p.printReport()

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
