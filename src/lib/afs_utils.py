import sys, os, re, string, types, time

sitelib = '::LIBDIR::'
sys.path.append(sitelib)
import afs_site, afs_vldb, afs_vosexamine, afs_voslistvol, afs_paths

try:
    import fcntl
    have_fcntl = 1
except:
    have_fcntl = 0

def GetFileServers(use_cached=1):
    """ Examine the whole VLDB to enumerate the file servers in existence.
        Returns a list of fileserver hostnames.

        * use_cached - A 0 (no) or a 1 (yes) indicating whether or not to
                       use a cached copy of the whole VLDB if one exists.
                       This is OPTIONAL.  The default is 1 (yes).
    """

    if use_cached:
        if afs_vldb.WHOLE_VLDB == None:
            afs_vldb.WHOLE_VLDB = afs_vldb.VLDBData()
            afs_vldb.WHOLE_VLDB.load()
    else:
        afs_vldb.WHOLE_VLDB = afs_vldb.VLDBData()
        afs_vldb.WHOLE_VLDB.load()

    fileservers = {}
    for e in afs_vldb.WHOLE_VLDB.getEntries():
        server = e.getRWsite().getServer()
        fileservers[server] = 1
        for s in e.getROsites():
            server = s.getServer()
            fileservers[server] = 1
    return fileservers.keys()

def CheckQuotas(vldbdata, warn=1, highmark=98):
    """ Check all volumes represented by vldbdata (passed in).  If the
        volume's quota is unlimited, report a warning.  Optionally (see
        argument descriptions below), warn if the percentage quota used
        is over highmark (passed in).

        Not really intended to be used as a utility function...more a
        fully-functioning script that I didn't want to break out into a
        script (as witnessed by the fact that it uses 'print')

        * vldbdata - A VLDBData object instace
        * warn - A flag stating whether you want to warn about volumes that are
                 over a certain percentage of usage.  1 or 0.
        * highmark - Only meaningful if you turned on warnings: The
                     percentage at which to warn about a quota.
                     Volumes that are using more than this percentage
                     of their allocated quota will be flagged for warning.
    """
    vldbdata.load()

    for e in vldbdata.getEntries():
        vname = e.getVName()
        ve = afs_vosexamine.VosExamineData(vname)
        if not ve.load():
            print "Problem with:", vname
        else:
            if ve.getBusy():
                print "Warning: Quota information for %s is currently unavailable because the volume is busy.  Skipping." % vname
                continue
            kused = 0
            mq = ve.getMaxQuota()
            if mq == 0:
                print "Warning:", vname, "has unlimited quota."
            else:
                if warn:
                    kused = ve.getKUsed()
                    perc = int((kused * 100) / mq)
                    if perc > highmark:
                        sys.stdout.write("Warning: %s is using %s%% of its quota (%s).\n" % (vname, str(perc), str(int(mq))))


def VLDB_VosExamine(use_cached=1):
    """
        Run a 'vos examine' on ever entry in the entire VLDB and
        print an error for volumes that could not be examined properly

        Not really intended to be used as a utility function...more a
        fully-functioning script that I didn't want to break out into a
        script (as witnessed by the fact that it uses 'print')

        * use_cached - A 0 (no) or a 1 (yes) indicating whether or not to
                       use a cached copy of the whole VLDB if one exists.
                       This is OPTIONAL.  The default is 1 (yes).
    """
    ret = 0
    data = []

    if use_cached:
        if afs_vldb.WHOLE_VLDB == None:
            afs_vldb.WHOLE_VLDB = afs_vldb.VLDBData()
            if not afs_vldb.WHOLE_VLDB.load():
                print "Problem loading VLDB"
                return
    else:
        afs_vldb.WHOLE_VLDB = afs_vldb.VLDBData()
        if not afs_vldb.WHOLE_VLDB.load():
            print "Problem loading VLDB"
            return

    for e in afs_vldb.WHOLE_VLDB.getEntries():
        vname = e.getVName()
        ve = afs_vosexamine.VosExamineData(vname)
        if not ve.load():
            print "Problem examining", vname
        else:
            if ve.getBusy():
                print "Hmm, %s is currently busy.  May want to check into it." % vname


def VosListvol_VosExamine_Check():
    """
        Report on volumes that exist on disk but not in the VLDB.  Might find
        other problems as well.  Returns nothing.

	Not really intended to be used as a utility function...more a
	fully-functioning script that I didn't want to break out into a
	script (as witnessed by the fact that it uses 'print')
    """
    fileservers = GetFileServers()

    # 1.  Get a list of all file servers
    # 2.  For every file server
    #         Do a vos listvol and collect the data
    #         For every item found in vos listvol
    #             Do a vos examine on the volume
    #             If the vos examine does not work properly, print a warning.
    for fs in fileservers:
        vlvdata = afs_voslistvol.VosListvolData(fs)
        if not vlvdata.load():
            print "Problem loading vos listvol data for:", fs
        for vlve in vlvdata.getEntries():
            ve = afs_vosexamine.VosExamineData(vlve.getVName())
            if not ve.load():
                sys.stdout.write("Problem with %s (%s) on server %s:%s:\n" %
                    (vlve.getVName(), vlve.getVID(), fs,
                    vlve.getSite().getPartition()))
                sys.stdout.flush()

def FullPartitionName(pname):
    """
        Given a partition name of any form, return it as a standard full
        partition name in /vicepNNNN form.

        * pname - A string representing a partition name in some decent form
    """
    pname = string.strip(pname)
    if string.find(pname, '/vice') < 0:
        return '/vicep' + pname
    else:
        return pname

def VosRelease(vname):
    """
        Release a replicated AFS volume

        * vname - The volume to release
    """
    command = afs_paths.AFS_vosCMD + ' release ' + vname
    return RunCommand(command)

def VosRemsite(server, partition, vname):
    """
        Remove a replication site for a volume

        * server - The server where the volume is replicated
        * partition - The partition on server where the volume is replicated
        * vname - The volume name to unreplicate from server:/partition
    """
    command = afs_paths.AFS_vosCMD + ' remsite -server ' + server + \
        ' -partition ' + partition + ' -id ' + vname
    return RunCommand(command)
    
def VolnameFromMountpoint(mpoint):
    """
        Given a path, return either the AFS volume name that is mounted
        at that point or an empty string (which means the mount point is not
        a proper AFS volume mount point)

        * mpoint - A path
    """
    volre = re.compile("^'.+'\s+is a mount point for volume\s+'(.+)'", re.I)
    afscmd = afs_paths.AFS_fsCMD + ' lsmount -dir ' + mpoint
    for line in RunCommandReturnOutput(afscmd):
        if line == '\n':
            continue
        match = volre.search(line)
        if match != None:
            args = match.groups()
            if type(args) is types.StringType:
                vname = args
            elif type(args) is types.TupleType:
                vname = args[0]
            vname = string.replace(vname, '%', '')
            vname = string.replace(vname, '#', '')
            return vname
    return ''

def UnmountVolume(mpoint):
    """
        Unmount a volume and return 0 on failure, or the name of the volume
        unmounted on success

        * mpoint - The path to the volume's mountpoint
    """
    vname = VolnameFromMountpoint(mpoint)
    if not vname:
        # Not even a volume.  Choke
        return 0
    afscmd = afs_paths.AFS_fsCMD + ' rmmount -dir ' + mpoint
    if RunCommand(afscmd):
        return vname
    else:
        return 0

def VosRemove(server, partition, vname):
    """
        Remove a volume from a server and partition

        Returns 0 on failure, 1 on success

        * server - The server where vname resides
        * partition - The partition where vname resides
        * vname - The volume name to remove from server's partition
    """ 
    afscmd = afs_paths.AFS_vosCMD + ' remove -server ' + server + \
        ' -partition ' + partition + ' -id ' + vname
    return RunCommand(afscmd)

def HoursOld(fname):
    """
        Determine (in hours) how old a file is

        Returns the hours (integer) or -1 on failure

        * fname - The path to the file to examine
    """
    if not os.path.isfile(fname):
        return -1
    try:
        # Get the 'seconds since epoch' time of when it was last modified
        secs_mtime = os.path.getmtime(fname)
    except os.error:
        # inaccessible
        return -1
    secs_currtime = int(time.time())
    secs_diff = secs_currtime - secs_mtime
    if secs_diff < 0:
        return -1
    return int(secs_diff / 3600)

def RunCommand(command):
    """
        Run an OS-level command and return 0 on failure, 1 on success

        * command - The command to run
    """
    command = command + ' 2>&1'
    try:
        cmdfd = os.popen(command, 'r')
    except:
        # Caught an internal popen() exception
        return 0
    ret = cmdfd.close()
    # Reverse the results because I like it that way
    if ret:
        return 0
    else:
        return 1

def OutputBasedSuccessRunCommand(command, searchstr):
    """
        Execute an OS-level command with stderr redirected to stdout, and
        return 1 if searchstr is found in the output of command, 0 if not.

        * command - the command to run
        * searchstr - the string to find in the output to generate a
                      successful return code
    """
    command = command + ' 2>&1'
    try:
        cmdfd = os.popen(command, 'r')
    except:
        # Caught an internal popen() exception
        return 0
    for line in cmdfd.readlines():
        if string.find(line, searchstr) > -1:
            cmdfd.close()
            return 1
    cmdfd.close()
    return 0

def RunCommandReturnOutput(command):
    """
        Execute a shell command with stderr redirected to stdout, and
        return all lines of output as a list

        * command - the command to run
    """
    retlines = []
    command = command + ' 2>&1'
    try:
        cmdfd = os.popen(command, 'r')
    except:
        # Caught an internal popen() exception
        return 0
    for line in cmdfd.readlines():
        retlines.append(line)
    cmdfd.close()
    return retlines

def LockFile(descriptor):
    if have_fcntl:
        try:
            fcntl.flock(descriptor.fileno(), fcntl.LOCK_EX)
        except:
            return 0
        else:
            return 1
    else:
        return 0
        
def UnlockFile(descriptor):
    if have_fcntl:
        try:
            fcntl.flock(descriptor.fileno(), fcntl.LOCK_UN)
        except:
            return 0
        else:
            return 1
    else:
        return 0

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
