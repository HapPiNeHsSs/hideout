from twisted.spread import pb
from twisted.internet import reactor
import socket, ssl, json, struct
from twisted.enterprise import adbapi
from ConfigParser import ConfigParser
from twisted.internet.task import LoopingCall
from twisted.python.log import msg
import shelve
import time
#Read Config File
config = ConfigParser()
config.read("../../etc/hideout.conf")

dbpool = adbapi.ConnectionPool("MySQLdb",\
                                user=config.get("db", "user"),\
                                passwd=config.get("db", "passwd"),\
                                host=config.get("db", "host"),\
                                db=config.get("db", "dbname"))

class LocalReference(pb.Referenceable):
    """
      Reference sent to clients as dial-back
    """
    def __init__(self, name, peer, service):
        self.name = name
        self.peer = peer
        self.service = service

    def __str__(self):
        return self.name
    
    def remote_test(self, name):
        print name
        return name
    
    def remote_invite(self, _from, fbfrom, _to):
        self.service.invite(_from, fbfrom, _to)
    
    def remote_list(self, _from, fb):
        self.service.list(_from, fb)
    
    def remote_accept(self, _from, fbfrom, fb):
        self.service.accept(_from, fbfrom, fb)
    
class PBBroker(pb.Root):
    """
      Root reference to invoke initialisation on
    """
    local_ref = LocalReference
    
    def __init__(self, service, factory):
        self.service = service
        self.factory = factory
    
    def remote_init(self, name, peer):
        ref = self.local_ref(name, peer, self.service)
        self.factory.clientRef[name] = peer
        peer.callRemote("ping")
        return ref

class PBServerFactory(pb.PBServerFactory):
    broker = PBBroker
    def __init__(self, service):
        self.clientRef = {}
        self.service = service(self) 
        pb.PBServerFactory.__init__(self, self.broker(self.service,self))
         

    def start(self, pbport):
        reactor.listenTCP(pbport, self)
    
    def reply(self, payload):
        pass
 
class FbService():
    def __init__(self, factory):
        print factory.clientRef
        self.dbKA = LoopingCall(self.dbKeepAlive)
        self.dbKA.start(3600)
        self.peer = factory.clientRef

            
    def start(self, address, port):
        host = (address, port)
        self.ssl_sock.connect(host)
    
    def dbKeepAlive(self):
        msg("Sending DB keepalive")
        dbpool.runOperation("select 1");
    
    def invite(self, _from, fbfrom, _to):
        print dbpool.runOperation("insert into fbinvite set `from`=%s,\
            `fbfrom`=%s, `to`=%s", (_from, fbfrom, _to))
        self.peer["FB"].callRemote("fbinviteResponse", _from)
    
    def list(self, _from, fb):
        def cbRes(result):
            if len(result) == 0 or result == "None":
                self.peer["FB"].callRemote("fbinviteListResponse", _from, 0)
            else:
                new_res = []
                for row in result:
                    new_res.append((row[0], row[1]))
                print new_res
                self.peer["FB"].callRemote("fbinviteListResponse", _from, new_res)
        def cbErr(result):
            print result
        dbpool.runQuery("select `from`, `fbfrom` from fbinvite where `to`=%s\
                        and `accepted`=0",\
                (fb)).addCallback(cbRes).addErrback(cbErr)
    
    def accept(self, _from, fbfrom, _to):
        dbpool.runOperation("update fbinvite set `accepted`=1 where\
                `from`=%s and `to`=%s",(fbfrom, _to))
        #dbpool.runOperation("delete from fbinvite where `accepted`=0 and \
        #`to`=%s ",( _to))
        
        self.peer["FB"].callRemote("fbinviteAcceptResponse", fbfrom, _from)
g = PBServerFactory(FbService)
g.start(4546)
#g.service.sendMessage(token, "testing")
reactor.run()
