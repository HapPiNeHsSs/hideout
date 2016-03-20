
from twisted.internet.protocol import DatagramProtocol

from twisted.internet import reactor, protocol
from twisted.protocols import basic
from socket import SOL_SOCKET, SO_BROADCAST
from twisted.internet.task import LoopingCall

import json, random, time

class Character():
    def __init__(self, name, address, udp, main):
        self.name  = name
        self.address = address
        self.udp = udp
        self.heartBeatCount = 3
        self.main = main
        self.world = None
        self.street = None
        self.room = None
        self.handlers = { "disconnect":self.connectionLost,
                          "pos_upd":self.pos_upd_handler,
                          "mov":self.mov_handler,
                          "heartbeat":self.onHeartBeat}
        self.heartbeatloop = LoopingCall(self.sendHeartbeat)
        self.heartbeatloop.start(5)
    
    def stop(self):
        self.heartbeatloop.stop()
        self = None
    
    def sendHeartbeat(self):
        """
        Checks if this character instance is still connected.
        Does three heartv beat retry
        """
        if self.heartBeatCount == 0:
            self.connectionLost({"id":self.name})
            return
        hb = json.dumps({'heartbeat':1})
        self.udp.reply(hb, self.address)
        self.heartBeatCount-=1
    
    def onHeartBeat(self, val):
        print "Hearbeat OK"
        self.heartBeatCount = 3
    
    def onRelay(self, data):
        for handler, data in data.items():
            if handler in self.handlers:
                self.handlers[handler](data)
    
    def reply(self, data):
        self.udp.reply(data, self.address)
        
    def connectionLost(self, data):
        name = data['id']
        print name, "has disconnected"
        dc = json.dumps({'dc':{"id":name}})
        self.main.send_to_others(name, dc)
        self.main.removePlayer(name)
    
    def pos_upd_handler(self, val):
        #update receiver with the my current position
        if val.has_key("pos") and val.has_key("id") and val.has_key("receiver")\
        and len(val.keys())==2:
            mes = {"pos_upd":{"id":val['receiver'],"pos":[val["pos"][0],\
                                                          val["pos"][1]]}}
            self.send(val['receiver'], json.dumps(mes))
    
    def mov_handler(self, val):
        if val.has_key("dest") and val.has_key("id") and len(val.keys())==2:
            mes = {"mov":{"id":val['id'],"dest":[val['dest'][0],\
                                                 val['dest'][1]]}}
            self.main.send_to_others(self.name, json.dumps(mes))
    
    def send(self, player, mes):
        try:
            self.main.players[player].reply(mes)
        except Exception:
            print self.main.players, player
            print "Failed: Not in here anymore"
    
class HeroFactory(protocol.ServerFactory):
    def __init__(self, main):
        self.main = main

class HeroProtocol(DatagramProtocol):
    
    def __init__(self, main):
        
        self.main = main
        self.jdec = json.JSONDecoder()
        self.jenc = json.JSONEncoder()
        #self.factory.main = HeroMain
        self.id = 0
        self.handlers = {"connect":self.connectionMade}

    
    def reply(self, dat, address):
        print "sending", dat
        self.transport.write(dat, address)
    
    def datagramReceived(self, data, address):
        print "received", str(data)
        mes = data
        try:
            mes = json.loads(data)
        except:
            print mes, "Fail: Not Json"
            return
        for handler, data in mes.items():
            if handler in self.handlers:
                self.handlers[handler](data, address)
            else: self.relay(mes, data['id'])
        # The uniqueID check is to ensure we only service requests from
        # ourselves
        """
        if datagram == 'UniqueID':
            print "Server Received:" + repr(datagram)
            self.transport.write("data", address)
        """   
    def relay(self, data, id):
        print ">>>relay", data
        self.main.players[id].onRelay(data)
        
    def connectionMade(self, data, address):
        #self.id = self.main.idGen()
        name = data['id']
        self.id = name
        print self.id
        print name, "has connected"
        char = Character(name, address, self, self.main)
        self.main.addPlayer(name, char)
        x,y = self.main.randomXY()
        #Broadcast to other your attributes first
        my_pos_to_others = json.dumps({"pos_upd":{"id":name,"pos":(x,y)}}) 
        self.main.send_to_others(name, my_pos_to_others)
        #Update Your attributes (this comes second so that your position to
        #other players are synchronized
        pos_upd = json.dumps({'pos_upd':{"pos":(x,y)}})
        self.reply(pos_upd, address)
        #Request other players attributes
        request_pos = json.dumps({'pos_upd':{"receiver":name}})
        self.main.send_to_others(name, request_pos)
        
class HeroMain():
    def __init__(self):
        self.id = 0;
        self.players = dict()
        self.UDP = HeroProtocol(self)
        self.reso = (480,320)
    
    def start(self):
        reactor.listenUDP(8005, self.UDP)
        reactor.run()

    def idGen(self):
        self.id += 1
        return self.id
    
    def addPlayer(self, player, ref):
        print "Added Player", player
        self.players[player]=ref
        print "Player Map:",self.players
    
    def removePlayer(self, player):
        print "Remove Player", player
        self.players[player].stop()
        self.players.pop(player)
        print "Player Map:",self.players
    
    def randomXY(self):
        x = random.randrange(0, self.reso[0])
        y = random.randrange(0, self.reso[1])
        return (x,y)
    
    def send_to_others(self, exclude, mes):
        print "sending to others", mes
        for player, ref in self.players.items():
            if exclude != player:
                print "sending to", ref.name
                ref.reply(mes)
        
# this only runs if the module was *not* imported
if __name__ == '__main__':
    v = HeroMain()
    v.start()
