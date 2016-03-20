#
# pbserver.py
#

from twisted.spread import pb

class LocalReference(pb.Referenceable):
    """
    Reference sent to clients as dial-back
    """
    def __init__(self, name, service, peer):
        self.name = name
        self.service = service
        self.peer = peer

    def __str__(self):
        return self.name
    

class Broker(pb.Root):
    """
    Root reference to invoke initialisation on
    """
    local_ref = LocalReference
    
    def __init__(self, service):
        self.service = service

    def remote_init(self, name, peer):
        ref = self.local_ref(name, self.service, peer)
        return ref
    

class PBServerFactory(pb.PBServerFactory):
    broker = Broker
    
    def __init__(self, service):
        self.service = service
        pb.PBServerFactory.__init__(self, self.broker(service))
