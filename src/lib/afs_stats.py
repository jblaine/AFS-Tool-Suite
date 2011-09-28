#-----------------------------------------------------------------------------
#
# Data files should be in gather_committal_stats format:
#
# SERVER  PARTITION  K_DISK_SIZE  K_FREE  UNCOMMITTED_K_FREE  PERCENT_COMMITTED
#
# (the amount of whitespace between columns does not matter)
#
#-----------------------------------------------------------------------------

import os, sys, string, glob

debugging = 0

def DEBUG(message):
    if debugging:
        sys.stderr.write(message + '\n')
        sys.stderr.flush()

# A struct-like thing to represent a line of data, timestamped
class Entry:

    def __init__(self, YYYYMMDD, server, partition, kdisksize, kfree, perccomm):
        self.YYYYMMDD = YYYYMMDD
        self.server = server 
        self.partition = partition
        self.kdisksize = kdisksize
        self.kfree = kfree
        self.perccomm = perccomm


class ReportGenerator:
    """ Interface class (should only be sub-classed and never instantiated).
        Constructor expects the following args:
        * statsroot: the top-level stats directory
        * server: the server whose stats we are reporting on
        * files_glob: the shell pattern (glob) to match when figuring out
                      which files to incorporate into this report.  This
                      should be relative to statsroot, so should not
                      look anything like a full pathname with /'s.
    """

    def __init__(self, statsroot, server, files_glob):
        self.setStatsRoot(statsroot)
        self.setServer(server)
        self.setFilesGlob(files_glob)
        self.initData()

    def initData(self):
        self.data = []

    def setData(self, data):
        self.data = data

    def getData(self):
        return self.data

    def setStatsRoot(self, statsroot):
        self.statsroot = statsroot

    def getStatsRoot(self):
        return self.statsroot

    def setServer(self, server):
        self.server = server

    def getServer(self):
        return self.server

    def setFilesGlob(self, files_glob):
        self.files_glob = files_glob

    def getFilesGlob(self):
        return self.files_glob

    def loadData(self):
        curd = os.getcwd()
        DEBUG("Saved directory: %s" % curd)
        try:
            os.chdir(self.getStatsRoot())
        except os.error, msg:
            (code, message) = msg
            sys.stderr.write('Failed to chdir to ' + direc + ': ' + \
                message + '\n')
            sys.stderr.flush()
            os.chdir(curd)
            return 0
        DEBUG("In directory: %s" % os.getcwd())
        entries = []
        fileglob = self.getFilesGlob()
        filelist = glob.glob(fileglob)
        filelist.sort()
        if not filelist:
            sys.stderr.write('No files matched: ' + fileglob + '\n')
            sys.stderr.flush()
            os.chdir(curd)
            DEBUG("Changed to directory: %s" % os.getcwd())
            return 0
        for file in filelist:
            if not os.path.isfile(file):
                DEBUG("Not a file - skipping: %s" % file)
                continue
            else:
                entries = entries + self.loadFile(file)
                self.setData(entries)
        os.chdir(curd)
        DEBUG("Changed to directory leaving loadData(): %s" % os.getcwd())
        return len(entries)
            
    def loadFile(self, file):
        entries = [] # list of Entry objects
        try:
            fd = open(file, 'r')
        except IOError, msg:
            (code, message) = msg
            sys.stderr.write('Failed to load ' + file + ': ' + message + '\n')
            sys.stderr.flush()
            return 0
        for line in fd.readlines():
            if string.find(line, '#') == 0:
                continue # ignore comment lines
            chunks = string.split(line)
            if chunks[0] != self.getServer():
                continue
            if len(chunks) != 5:
                sys.stderr.write('Ignoring bad line in file ' + file + ': ' + \
                    line + '\n')
                sys.stderr.flush()
            else:
                entry = Entry(file, chunks[0], chunks[1], chunks[2], \
                    chunks[3],  chunks[4])
                entries.append(entry)
        DEBUG("%d entries loaded from %s" % (len(entries), file))
        return entries

    # OVERRIDE THIS
    def printData(self):
        pass


class GIFReport(ReportGenerator):
    """ Generate a GIF report for a partition on a server.  If no output file
        name is set with the setOutFilename() method before calling printData(),
        the output will go to a file named <server>-<partition>.gif. Constructor
        expects the following args:
        * statsroot: the top-level directory containing server-named subdirs
        * server: the server whose stats we are reporting on
        * partition: the server's partition whose stats we are reporting on
        * files_glob: the shell pattern (glob) to match when figuring out
                      wfiles to incorporate into this report.  This
                      should be relative to statsroot/server, so should not
                      look anything like a full pathname with /'s.
        * gnuplot: the full path to gnuplot
        * outfile: the filename (full path okay) to store the output GIF in

        REQUIRES: gnuplot
    """

    def __init__(self, statsroot, server, partition, files_glob, gnuplot='/usr/local/bin/gnuplot', outfile=None):
        ReportGenerator.__init__(self, statsroot, server, files_glob)
        self.setPartition(partition)
        self.setGnuplot(gnuplot)
        if outfile == None:
            partition = string.replace(partition, '/', '')
            outfile = server + '-' + partition + '.gif'
        self.setOutFilename(outfile)

    def setGnuplot(self, gplocation):
        self.gnuplot = gplocation

    def getGnuplot(self):
        return self.gnuplot

    def setOutFilename(self, fname):
        self.outfilename = fname

    def getOutFilename(self):
        return self.outfilename

    def setPartition(self, partition):
        self.partition = partition

    def getPartition(self):
        return self.partition

    def printData(self):
        entries = self.getData()
        DEBUG("printData has %d entries" % len(entries))
        ylargest = 0
        ysmallest = 30000000
        for entry in entries:
            s = string.atoi(entry.YYYYMMDD)
            if s < 1:
                DEBUG("YIKES: %d found as a YYYYMMDD date." % s)
            if s > ylargest:
                ylargest = s
            if s < ysmallest:
                ysmallest = s
        print self.getOutFilename()
        DEBUG("Y min %d, Y max %d" % (ysmallest, ylargest))
        ylargest = ylargest + 1
        ysmallest = ysmallest - 1
        gnuplot = os.popen(self.getGnuplot(), 'w')
        gnuplot.write('set terminal gif\n')
        gnuplot.write('set output "' + self.getOutFilename() + '"\n')
        gnuplot.flush()
        gnuplot.write('set xlabel "Date"\n')
        gnuplot.write('set ylabel "Percent Committed"\n')
        gnuplot.write('set format "%.0f"\n')
        gnuplot.write('set xrange [' + str(ysmallest) + ':' + str(ylargest) + \
            ']\n')
        gnuplot.write('set yrange [0:200]\n')
        gnuplot.flush()
        part = self.getPartition() # Store this for use in loop below
        tmppart = string.replace(part, '/', '')
        tmpfilename = '/tmp/tmp' + self.getServer() + tmppart
        tmpfd = open(tmpfilename, 'w')
        for entry in entries:
            if entry.partition == part:
                tmpfd.write(entry.YYYYMMDD + ' ' + entry.perccomm + '\n')
        tmpfd.close()
        gnuplot.write('plot "' + tmpfilename + '" with lines\n')
        gnuplot.flush()
        gnuplot.close()
        os.unlink(tmpfilename)
        if os.path.isfile(self.getOutFilename()):
            return 1
        else:
            return 0

class MostRecentASCIIReport(ReportGenerator):
    """ Generate an ASCII text report from the most recent stats.  Constructor
        expects the following args:
        * ofd: output file descriptor
        * statsroot: the top-level directory containing server-named subdirs
        * server: the server whose stats we are reporting on
        * files_glob: the shell pattern (glob) to match when figuring out
                      which files to incorporate into this report.  This
                      should be relative to statsroot/server, so should not
                      look anything like a full pathname with /'s.
    """

    def __init__(self, statsroot, server, files_glob, ofd=None):
        ReportGenerator.__init__(self, statsroot, server, files_glob)
        if ofd == None:
            ofd = sys.stdout
        self.setOutputFD(ofd)
        self.KFreeThreshold = 48000 # Warn if less than 48MB on partition
        self.PercentCommittedThreshold = 120.00 # Warn if over 120% committed

    def setPercentCommittedThreshold(self, perccom):
        self.PercentCommittedThreshold = perccom

    def getPercentCommittedThreshold(self):
        return(self.PercentCommittedThreshold)

    def setKFreeThreshold(self, kb):
        self.KFreeThreshold = kb

    def getKFreeThreshold(self):
        return(self.KFreeThreshold)

    def setOutputFD(self, ofd):
        self.outputfd = ofd

    def getOutputFD(self):
        return self.outputfd

    def printData(self):
        fd = self.getOutputFD()
        entries = self.getData()
        mostrecent = None
        largest = 0
        for entry in entries:
            datestring = entry.YYYYMMDD
            dateint = string.atoi(datestring)
            if dateint > largest:
                largest = dateint
        fd.write(self.getServer() + ' -- ' + str(largest) + '\n')
        print "Partition    K_DiskSize       K_Free   %_Committed"
        for entry in entries:
            if string.atoi(entry.YYYYMMDD) == largest:
                partstring = string.rjust(entry.partition, 9)
                kdiskstring = string.rjust(entry.kdisksize, 12)
                kfreestring = string.rjust(entry.kfree, 12)
                kfreeint = string.atoi(kfreestring)
                try:
                    floater = string.atof(entry.perccomm)
                except:
                    pass
                if floater > self.getPercentCommittedThreshold() or kfreeint < self.getKFreeThreshold():
                    WarnString = '*** WARNING! ***'
                else:
                    WarnString = ''
                perccommstring = str('%.2f' % floater)
                perccommstring = string.rjust(perccommstring, 10)
                print partstring, kdiskstring, kfreestring, perccommstring, WarnString
