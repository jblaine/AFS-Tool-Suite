class Site:

    def __init__(self, server, partition):
        """ C-struct-like class to represent what makes up an AFS 'site'

            * server - A hostname
            * partition - An AFS 'vice' partition name
        """
        self.server = server
        self.partition = partition

    def getServer(self):
        return self.server

    def getPartition(self):
        return self.partition

    def __repr__(self):
        r = self.getServer() + ':' + self.getPartition()
        return r

#-----------------------------------------------------------------------------#
#                (c) Copyright 2000 The MITRE Corporation                     #
#-----------------------------------------------------------------------------#
