#!/usr/bin/env python

# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from base64 import b64encode
import sys
import json

class EchoClient(LineReceiver):
    id = "tester"
    print id
    def connectionMade(self):
        #self.transport.connect("69.194.160.210", 8005)
        auth = b64encode(self.id)
        #auth = b64encode("123")
        #auth = "MDAwMDAwMDAtMDAwMC0xMDAwLTgwMDAtMDAxQjYzMzU0MjNC"
        #print auth
        #dat = {"create":{"username":"test13",
        #                 "device_id":"1d1234",
        #                 "attributes":"test"}}
        dat = {"connect":auth}
        #self.sendLine("Asdfasdf")
        self.sendLine(json.dumps(dat))
        #reactor.callLater(0, self.chatPlayer, "tester", "test")
        #reactor.callLater(0.5, self.questHelpAccept, "q1", "tester")
        #reactor.callLater(0.5, self.fbinvite, "fbeejayx", "fbnew")
        #reactor.callLater(0.7, self.fbinviteList, "fbnew")
        """
        reactor.callLater(0.5, self.list)
        reactor.callLater(1, self.join, "Gotham")
        reactor.callLater(1.5, self.list)
        reactor.callLater(2, self.join, "Back alley")
        reactor.callLater(2.5, self.list)
        reactor.callLater(3, self.join, "1")
        reactor.callLater(4, self.chatRoom, "Hello!")
        #xxx='{"create":{"username":"tester44","device_id":"123","attributes":{"others":[],"wall":{"id":"1","xPos":"0","yPos":"0"},"floor":{"id":"0","xPos":"0","yPos":"0"}}}}'
        #xxx='{"sethome":{"from":"tester","val":{"others":[],"wall":{"id":"1","xPos":"0","yPos":"0"},"floor":{"id":"0","xPos":"0","yPos":"0"}}}}'
        #print json.loads(xxx)
        #self.sendLine(xxx)
        
        #reactor.callLater(0.3, self.setHome, '{"others":[],"wall":{"id":"1","xPos":"0","yPos":"0"},"floor":{"id":"0","xPos":"0","yPos":"0"}}')
        reactor.callLater(0, self.chatPlayer, "tester1", "test")
        #reactor.callLater(0.6, self.getHome)
        #reactor.callLater(0.3, self.setItem, "usa", 3, 876)
        #reactor.callLater(0.3, self.setToken, "asdflkhasldkjfa")
        
        #reactor.callLater(0.6, self.chatPlayer, "tester", "test4")
        #reactor.callLater(0, self.getFriends)
        #reactor.callLater(0.5, self.levelNotify, 2)
        #reactor.callLater(0.5, self.setQflag, "q2")
        #reactor.callLater(0.6, self.addFame, 300, "tester", 1)
        
                reactor.callLater(0, self.getFriends)
        reactor.callLater(1, self.delFriend, "tester3")
         reactor.callLater(0, self.chatPlayer, "tester1", "test")
        reactor.callLater(1, self.blockFriend, "tester")
        #reactor.callLater(1.5, self.delFriend, "tester3")
        reactor.callLater(2, self.getFriends)
        #reactor.callLater(2.5, self.unblockFriend, "tester2")
        reactor.callLater(3, self.getFriends)
        #reactor.callLater(3, self.blockFriend, "tester2")
        reactor.callLater(0, self.chatPlayer, "tester1", "test")
        reactor.callLater(0.1, self.chatPlayer, "tester1", "test2")
        reactor.callLater(0.2, self.chatPlayer, "tester1", "test3")
        reactor.callLater(0.3, self.chatPlayer, "tester1", "test4")
        reactor.callLater(0.6, self.getHome, "tester")
        
        
        reactor.callLater(0.5, self.getHealth)
        reactor.callLater(0.6, self.setCoin, 300)
        reactor.callLater(0.6, self.setHealth, 300)
        reactor.callLater(0.6, self.setFame, 300)
        reactor.callLater(0.6, self.setLevel, 300)
        reactor.callLater(1, self.join, "Gotham")
        reactor.callLater(1.5, self.list)
        reactor.callLater(2, self.join, "Back alley")
        reactor.callLater(2.5, self.list)
        reactor.callLater(3, self.join, "1")
        #reactor.callLater(3.5, self.join, "0")
        reactor.callLater(4, self.chatPlayer, "tester1", "test")
        reactor.callLater(4.5, self.chatRoom, "test room")
        reactor.callLater(4.7, self.getAddress)
        reactor.callLater(5, self.dc)
        """
    
    def lineReceived(self, data):
        print "received %s" % (data)
        try:
            mes = json.loads(data)
            if mes.has_key("pos_upd"):
                pos_upd = mes["pos_upd"]
                if pos_upd.has_key("receiver"):
                    dat = {"pos_upd":{"from":self.id,
                                      "receiver":pos_upd['receiver'],
                                      "pos":[30,50]}}
                    print dat
                    self.sendLine(json.dumps(dat))
            elif mes.has_key("heartbeat"):
                hb = {"heartbeat":{"from":self.id}}
                self.sendLine(json.dumps(hb))
                
        except: pass
    
    def setscore(self, quest, score):
        dat = {"setscore":{"from":self.id,"quest":quest, "score":score}}
        self.sendLine(json.dumps(dat))
        
    def gethiscore(self, quest, mode):
        dat = {"gethiscore":{"from":self.id,"quest":quest, "mode":mode}}
        self.sendLine(json.dumps(dat))
    
    def questHelp(self, quest, to):
        dat = {"questhelp":{"from":self.id,"quest":quest, "to":to}}
        self.sendLine(json.dumps(dat))
    
    def questHelpAccept(self, quest, to):
        dat = {"questhelpaccept":{"from":self.id,"quest":quest, "to":to}}
        self.sendLine(json.dumps(dat))
    
    def levelNotify(self, level):
        dat = {"levelnotify":{"from":self.id,"val":level}}
        self.sendLine(json.dumps(dat))
    
    def fbinvite(self, _from, to):
        dat = {"fbinvite":{"from":self.id,"fb":_from, "fbto":to}}
        self.sendLine(json.dumps(dat))
    
    def fbinviteList(self, _from):
        dat = {"fbinvitelist":{"from":self.id,"fb":_from}}
        self.sendLine(json.dumps(dat))
    
    def fbinviteAccept(self, fb, _from):
        dat = {"fbinviteaccept":{"from":self.id, "fb": fb, "accept":_from}}
        self.sendLine(json.dumps(dat))
    
    def worldList(self):
        dat = {"worldlist":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def getAddress(self):
        dat = {"getaddress":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def list(self):
        dat = {"list":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def join(self, realm):
        dat = {"join":{"from":self.id,"realm":realm}}
        self.sendLine(json.dumps(dat))
    
    def joinWorld(self, world):
        dat = {"join":{"from":self.id,"world":world}}
        self.sendLine(json.dumps(dat))
    
    def leave(self):
        dat = {"leave":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def streetList(self):
        dat = {"streetlist":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def joinStreet(self, street):
        dat = {"join":{"from":self.id,"street":street}}
        self.sendLine(json.dumps(dat))
    
    def leaveStreet(self):
        dat = {"leavestreet":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def joinRoom(self, room):
        dat = {"join":{"from":self.id,"room":room}}
        self.sendLine(json.dumps(dat))
    
    def chatRoom(self, message):
        dat = {"chat":{"from":self.id,"message":message}}
        self.sendLine(json.dumps(dat))
    
    def chatPlayer(self, recipient, message):
        dat = {"chat":{"from":self.id,
                             "to":recipient,
                             "message":message}}
        self.sendLine(json.dumps(dat))
    
    def getQflag(self, quest, target=None):
        if target == None:
            dat = {"getquestflag":{"from":self.id,"quest":quest}}
        else:
            dat = {"getquestflag":{"from":self.id,"quest":quest,"target":target}}
        self.sendLine(json.dumps(dat))
    
    def getCoin(self):
        dat = {"getcoin":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def getHealth(self):
        dat = {"gethealth":{"from":self.id}}
        self.sendLine(json.dumps(dat))
        
    def getFriends(self):
        dat = {"getfriends":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def addFriend(self, val):
        dat = {"addfriend":{"from":self.id,"friendname":val}}
        self.sendLine(json.dumps(dat))
        
    def addItem(self, id, type, quantity):
        dat = {"additem":{"from":self.id,"id":id,"type":type,"quantity":quantity}}
        self.sendLine(json.dumps(dat))
    
    def delItem(self, id, type, quantity):
        dat = {"delitem":{"from":self.id,"id":id,"type":type,"quantity":quantity}}
        self.sendLine(json.dumps(dat))
    
    def setItem(self, id, type, quantity):
        dat = {"setitem":{"from":self.id,"id":id,"type":type,"quantity":quantity}}
        self.sendLine(json.dumps(dat))
    
    def getItem(self):
        dat = {"getitem":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def setPower(self, id, level):
        dat = {"setpower":{"from":self.id,"power":id,"level":level}}
        self.sendLine(json.dumps(dat))
        
    def getPower(self):
        dat = {"getpower":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def delFriend(self, val):
        dat = {"delfriend":{"from":self.id,"friendname":val}}
        self.sendLine(json.dumps(dat))
    
    def blockFriend(self, val):
        dat = {"blockfriend":{"from":self.id,"friendname":val}}
        self.sendLine(json.dumps(dat))
    
    def unblockFriend(self, val):
        dat = {"unblockfriend":{"from":self.id,"friendname":val}}
        self.sendLine(json.dumps(dat))
    
    def getFame(self, target=None):
        if target == None:
            dat = {"getfame":{"from":self.id}}
        else:
            dat = {"getfame":{"from":self.id, "username":target}}
        self.sendLine(json.dumps(dat))
    
    
    def getHome(self, target=None):
        if target == None:
            dat = {"gethome":{"from":self.id}}
        else:
            dat = {"gethome":{"from":self.id, "username":target}}
        self.sendLine(json.dumps(dat))
    
    def getLevel(self):
        dat = {"getlevel":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    
    def setToken(self, val):
        dat = {"settoken":{"from":self.id,
                          "val":val}}
        self.sendLine(json.dumps(dat))
    
    def setCoin(self, val):
        dat = {"setcoin":{"from":self.id,
                          "val":val}}
        self.sendLine(json.dumps(dat))
    
    def setQflag(self, quest):
        dat = {"setquestflag":{"from":self.id,
                          "quest":quest}}
        self.sendLine(json.dumps(dat))
    
    def setHome(self, val):
        dat = {"sethome":{"from":self.id,
                          "val":val}}
        self.sendLine(json.dumps(dat))
    
    def setHealth(self, val):
        dat = {"sethealth":{"from":self.id,
                          "val":val}}
        self.sendLine(json.dumps(dat))
    
    def setFame(self, val):
        dat = {"setfame":{"from":self.id,
                          "val":val}}
        self.sendLine(json.dumps(dat))
    
    def addFame(self, val, target, type):
        dat = {"addfame":{"from":self.id,
                          "val":val,
                          "username":target,
                          "type":type}}
        self.sendLine(json.dumps(dat))
    
    def setLevel(self, val):
        dat = {"setlevel":{"from":self.id,
                          "val":val}}
        self.sendLine(json.dumps(dat))
        
    def dc(self):
        dat = {"disconnect":{"from":self.id}}
        self.sendLine(json.dumps(dat))
    # Possibly invoked if there is no server listening on the
    # address to which we are sending.
    def connectionRefused(self):
        print "No one listening"
        
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
    reactor.connectTCP('localhost', 8005, factory)
    reactor.run()

if __name__ == '__main__':
    main()
