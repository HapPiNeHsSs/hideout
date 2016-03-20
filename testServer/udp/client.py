from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import json

class Helloer(DatagramProtocol):
    id = "d"

    def startProtocol(self):
        self.transport.connect("127.0.0.1", 8005)
        dat = {"connect":{"id":self.id}}
        self.transport.write(json.dumps(dat))
        reactor.callLater(3, self.mov)
    
    def datagramReceived(self, data, (host, port)):
        print "received %r from %s:%d" % (data, host, port)
        try:
            mes = json.loads(data)
            if mes.has_key("pos_upd"):
                pos_upd = mes["pos_upd"]
                if pos_upd.has_key("receiver"):
                    dat = {"pos_upd":{"id":self.id,"receiver":pos_upd['receiver'],"pos":[30,50]}}
                    print dat
                    self.transport.write(json.dumps(dat))
            elif mes.has_key("heartbeat"):
                hb = {"heartbeat":{"id":self.id}}
                self.transport.write(json.dumps(hb))
                
        except: pass
    
    def mov(self):
        dat = {"mov":{"id":self.id,"dest":[24,1]}}
        self.transport.write(json.dumps(dat))
    
    def dc(self):
        dat = {"disconnect":{"id":self.id}}
        self.transport.write(json.dumps(dat))
    # Possibly invoked if there is no server listening on the
    # address to which we are sending.
    def connectionRefused(self):
        print "No one listening"

# 0 means any port, we don't care in this case
reactor.listenUDP(0, Helloer())
reactor.run()
