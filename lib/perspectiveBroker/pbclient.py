from collections import deque
from twisted.internet import reactor
from twisted.spread import pb
from twisted.python import log

class DefinedError(pb.Error):
    pass

class LocalReference(pb.Referenceable):
    def __init__(self, client):
        self.client = client

class PBClient():
    """
    a PB client. For now, we only connect to one PB server. If we have to
    connect to several servers then we have to track which local reference are
    we sending and which dial-back we are receiving.
    
    """
    reconnect_timeout = 3
    max_reconnect = 100
    max_request_queue = 18000    # tps_ave * ( 300 secs / reconnect_timeout )
    local_ref = LocalReference
    
    def __init__(self, name, service):
        self.name = name
        self.service = service
        self.remoteDialback = None
        self.factory = None
        
        self._reconnect = True
        self._host = None
        self._port = None
        self._reqq = deque()
        
    def __str__(self):
        return self.name
        
    def connectTCP(self, host=None, port=None):
        self._reconnect = True
        if self._host == None:
            self._host = host
        if self._port == None:
            self._port = port
        if not self.factory:
            self.factory = pb.PBClientFactory()
            self.factory.clientConnectionFailed = self._onConnectionFailed
            self.factory.clientConnectionLost = self._onConnectionLost
        reactor.connectTCP(self._host, self._port, self.factory)
        self.factory.getRootObject().addCallbacks(self.connected, self.onError)
    connect = connectTCP

    def connectUNIX(self, sock_path):
        if not self.factory:
            self.factory = pb.PBClientFactory()
            self.factory.clientConnectionFailed = self._onConnectionFailed
            self.factory.clientConnectionLost = self._onConnectionLost
        reactor.connectUNIX(sock_path)
        self.factory.getRootObject().addCallbacks(self.connected, self.onError)
        
    def connected(self, ref):
        log.msg("Connected to %s:%s, got peer %s" %\
                (self._host, self._port, ref))
        ref.callRemote("init", self.name, self.local_ref(self))\
            .addCallbacks(self._onInitOk, self.onError)
        
    def onError(self, error):
        t = error.trap(DefinedError)
        print "error received:", t
    
    def _onConnectionFailed(self, connector, reason):
        log.msg("[%s:%s] Connection failed: %s" %\
                (connector.host, connector.port, reason))
        if self._reconnect:
            reactor.callLater(int(self.reconnect_timeout), connector.connect)
        self.onConnectionFailed()
        
    def onConnectionFailed(self):
        """
        Implement this method to handle connection failure
        """
        pass

    def _onConnectionLost(self, connector, reason):
        log.msg("Disconnected from %s:%s, got error: %s" %\
                (self._host, self._port, reason))
        if self._reconnect:
            pb.PBClientFactory.clientConnectionLost\
                (self.factory, connector, reason, reconnecting=1)
            self.remoteDialback = None
            reactor.callLater(int(self.reconnect_timeout), connector.connect)
            self.factory.getRootObject()\
                .addCallbacks(self.connected, self.onError)
        self.onConnectionLost()

    def onConnectionLost(self):
        """
        Implement this method to handle client disconnection.
        """
        pass
    
    def _onInitOk(self, remoteDialback):
        log.msg("[%s] Got ref: %s" % (self, remoteDialback))
        self.remoteDialback = remoteDialback
        self.onInitOk()

    def onInitOk(self):
        """
        Extend this method to handle initialization success
        """
        #if self.on_init_action:
        while len(self._reqq) > 0:
            self.onInitAction(*self._reqq.popleft())
                
    def onInitAction(self, *args):
        pass

    def disconnect(self):
        self._reconnect = False
        self.factory.disconnect()

    def queueRequest(self, req):
        if len(self._reqq) < self.max_request_queue:
            self._reqq.append(req)
        else:
            self._reqq.popleft()
            self._reqq.append(req)