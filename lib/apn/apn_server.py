from twisted.spread import pb
from twisted.internet import reactor
import socket, ssl, json, struct
from twisted.enterprise import adbapi
from twisted.internet.task import LoopingCall
from ConfigParser import ConfigParser
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
    
    def remote_sendMessage(self, did, msg):
        ret = self.service.sendMessage(did, msg)
        print did, ret
        return ret
    
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
        self.service = service
        self.clientRef = {}
        pb.PBServerFactory.__init__(self, self.broker(service,self))  

    def start(self, pbport, apnhost, apnport):
        self.service.start(apnhost, apnport)
        reactor.listenTCP(pbport, self)

 
class ApnService():
    
    def __init__(self):
        self.prep = LoopingCall(self.getLowHealth)
        self.dbKA = LoopingCall(self.dbKeepAlive)
        self.dbKA.start(3600)
        self.certFile = 'certPushTapHeroesDev.pem'
        self.ssl_sock = ssl.wrap_socket(
                                socket.socket(
                                              socket.AF_INET,
                                              socket.SOCK_STREAM ),
                                certfile = self.certFile )
        self.shelf = shelve.open("data.apn", writeback=True)
        self.shelf["index"]=list()
        self.prep.start(10, False)
    
    def dbKeepAlive(self):
        msg("Sending DB keepalive")
        dbpool.runOperation("select 1");
        
    def getLowHealth(self):
        def cbRes(result):
            if len(result)>0:
                for res in result:
                    buf=time.gmtime()
                    ind=res[0].__str__()+\
                        buf[0].__str__()+\
                        buf[1].__str__()+\
                        buf[2].__str__()
                    if ind not in self.shelf["index"]:
                        mes = "Your character has low health"
                        try:
                            self.sendMessage(res[0], mes)
                            self.shelf["index"].append(ind)
                        except: pass
        
        def cbErr(result):
            print result
        
        dbpool.runQuery("select token from ho_users where health <=10")\
        .addCallback(cbRes).addErrback(cbErr)
        
            
    def start(self, address, port):
        host = (address, port)
        self.ssl_sock.connect(host)
    
    def sendMessage(self, did, message):
        deviceToken = did.replace(' ','')
        print deviceToken, "DEB" 
        byteToken = deviceToken.decode('hex')
        thePayLoad = {
         'aps': {
              'alert':message,
              'sound':'',
              'badge':0,
              }
         }
        data = json.dumps( thePayLoad )
        print byteToken
        format = '!BH32sH%ds' % len(data)
        notification = struct.pack( format, 0, 32, byteToken, len(data), data )
         
        # Create our connection using the certfile saved locally
         
         
        # Write out our data
        self.ssl_sock.write( notification )
         
        # Close the connection -- apple would prefer that we keep
        # a connection open and push data as needed.
        

token ='69a2848f 5ac92aa4 d80e1c29 5cc30b2f 06b7eaed 0f485e61 90017127 f9dab568'
g = PBServerFactory(ApnService())
g.start(4545,'gateway.sandbox.push.apple.com', 2195)
#g.service.sendMessage(token, "testing")
reactor.run()
