#!/afs/rcf/lang/bin/python

"""
    Script to remove an AFS volume from its server and partition and its 
    mount point given just the path to the mount point.  This is not a
    library to be imported.
"""

#----------------------------------------------------------------------------

import os, string, re, sys, types

sitelib = '::LIBDIR::'
sys.path.append(sitelib)
import afs_utils, afs_paths, afs_vosexamine

def UsageExit():
    """
        Display usage information and exit with code 1
    """
    print "Usage: %s <mountpoint1 ... mountpointN>" % script
    print ""
    sys.exit(1)

def DestroyVolume(mpath):
    vname = afs_utils.UnmountVolume(mpath)
    if not vname:
        print "%s: Couldn't unmount %s." % (script, mpath)
        sys.exit(1)
    else:
        print "%s: Unmounted %s from %s." % (script, vname, mpath)

    vedata = afs_vosexamine.VosExamineData(vname)
    vedata.load()
    vldbe = vedata.getVLDBEntry()

    replicated = 0

    ROID = vldbe.getROID()
    for site in vldbe.getROsites():
        server = site.getServer()
        partition = site.getPartition()
        if not afs_utils.VosRemove(server, partition, ROID):
            print '%s: Could not remove %s from %s:%s.' % (script, ROID,
                server, partition)
        else:
            print '%s: Removed %s from %s:%s.' % (script, ROID,
                server, partition)
            replicated = 1

    # if replicated:
    #     if not afs_utils.VosRelease(vname):
    #         print '%s: Could not release %s.' % (script, vname)

    # Now remove the RW volume
    RWsite = vldbe.getRWsite()
    server = RWsite.getServer()
    partition = RWsite.getPartition()
    if not afs_utils.VosRemove(server, partition, vname):
        print '%s: Could not remove %s from %s:%s.' % (script, vname,
            server, partition)
    else:
        print '%s: Removed %s from %s:%s.' % (script, vname,
            server, partition)

    afscmd = afs_paths.AFS_vosCMD + ' examine -id ' + vname
    if afs_utils.RunCommand(afscmd):
        # If the vol still exists, barf
        return 0
    return 1

#----------------------------------------------------------------------------
# Main logic
#----------------------------------------------------------------------------
script = os.path.basename(sys.argv[0])

# Main
if len(sys.argv) < 2:
    UsageExit()
if not afs_utils.OutputBasedSuccessRunCommand(afs_paths.AFS_tokensCMD, '(AFS ID 1)'):
    print "%s: User not authenticated properly." % script
    sys.exit(1)
else:
    dirs = sys.argv[1:]
for mountpoint in dirs:
    # Yank off any trailing / from shells that file complete that way
    if len(mountpoint) > 1 and mountpoint[-1:] == '/':
        mp = mountpoint[:-1]
    else:
        mp = mountpoint
    DestroyVolume(mp)

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
