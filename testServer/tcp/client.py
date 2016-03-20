#!/usr/bin/env python

# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys
import json

class EchoClient(LineReceiver):
    def connectionMade(self):
        reactor.callLater(3, self.mov)
        pass
    
    def lineReceived(self, line):
        print "receive:", line
        mes = json.loads(line)
        if mes.has_key("pos_upd"):
            pos_upd = mes["pos_upd"]
            if pos_upd.has_key("receiver"):
                dat = {"pos_upd":{"receiver":pos_upd['receiver'],"pos":[30,50]}}
                self.sendLine(json.dumps(dat))
    
    def mov(self):
        dat = {"mov":{"dest":[24,1]}}
        self.sendLine(json.dumps(dat))
        
class EchoClientFactory(ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()
        reactor.stop()

def main():
    factory = EchoClientFactory()
    reactor.connectTCP('localhost', 8000, factory)
    reactor.run()

if __name__ == '__main__':
    main()
