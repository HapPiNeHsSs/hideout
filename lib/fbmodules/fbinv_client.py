import sys


from lib.perspectiveBroker.pbclient import PBClient
from twisted.spread import pb
from twisted.internet import reactor

class LocalReference(pb.Referenceable):
    def __init__(self, client):
        self.client = client
  
    def remote_ping(self):
        return 'online'
    
    def remote_fbinviteResponse(self, _from):
        self.client.service.fbinviteResponse(_from)
    
    def remote_fbinviteAcceptResponse(self, _from, _to):
        self.client.service.fbinviteAcceptResponse(_from, _to)
        
    def remote_fbinviteListResponse(self, user, list):
        self.client.service.fbinviteListResponse(user, list)

class fbinvClient(PBClient):
    local_ref = LocalReference
    def __init__(self, name, service):
        PBClient.__init__(self, name, service)
    
    def onInitOk(self):
        print "lala";
        self.remoteDialback.callRemote("test", "name")
        self.wait=0 #enable the portal

