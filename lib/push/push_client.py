import sys


from lib.perspectiveBroker.pbclient import PBClient
from twisted.spread import pb
from twisted.internet import reactor

class LocalReference(pb.Referenceable):
    def __init__(self, client):
        self.client = client
  
    def remote_ping(self):
        return 'online'

class pushClient(PBClient):
    local_ref = LocalReference
    def __init__(self, name, service):
        PBClient.__init__(self, name, service)
    
    def onInitOk(self):
        print "DEBUG PUSH Start", self.remoteDialback
        self.remoteDialback.callRemote("test", "name")
        self.wait=0 #enable the portal

