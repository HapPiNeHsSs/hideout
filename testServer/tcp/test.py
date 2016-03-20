
from twisted.internet import reactor, protocol
from twisted.protocols import basic
import json, random, time
class HeroFactory(protocol.ServerFactory):
    def __init__(self, main):
        self.main = main

class HeroProtocol(basic.LineReceiver):
    def __init__(self):
        
        self.jdec = json.JSONDecoder()
        self.jenc = json.JSONEncoder()
        #self.factory.main = HeroMain
        self.id = 0
        self.handlers = {"pos_upd":self.pos_upd_handler,
                         "mov":self.mov_handler}
    
    def reply(self, dat):
        print "sending", dat
        self.sendLine(dat)
    
    def connectionMade(self):
        self.id = self.factory.main.idGen()
        print self.id, "has connected"
        self.factory.main.addPlayer(self.id, self)
        x,y = self.factory.main.randomXY()
        #Broadcast to other your attributes first
        my_pos_to_others = json.dumps({"pos_upd":{"id":self.id,"pos":(x,y)}}) 
        self.factory.main.send_to_others(self.id, my_pos_to_others)
        #Update Your attributes (this comes second so that your position to
        #other players are synchronized
        pos_upd = json.dumps({'pos_upd':{"pos":(x,y)}})
        self.reply(pos_upd)
        #Request other players attributes
        request_pos = json.dumps({'pos_upd':{"receiver":self.id}})
        self.factory.main.send_to_others(self.id, request_pos)
        
    def connectionLost(self, reason):
        dc = json.dumps({'dc':{"id":self.id}})
        self.factory.main.send_to_others(self.id, dc)
        self.factory.main.removePlayer(self.id)
    
    def lineReceived(self, data):
        print "received", str(data)
        mes = data
        try:
            mes = json.loads(data)
        except:
            print mes, "Fail: Not Json"
            return
        for handler, value in mes.items():
            if handler in self.handlers:
                self.handlers[handler](value)
    
    def pos_upd_handler(self, val):
        #update receiver with the my current position
        if val.has_key("pos") and val.has_key("receiver")\
        and len(val.keys())==2:
            mes = {"pos_upd":{"id":self.id,"pos":[val["pos"][0],val["pos"][1]]}}
            self.send(val['receiver'], json.dumps(mes))
    
    def mov_handler(self, val):
        if val.has_key("dest") and len(val.keys())==1:
            mes = {"mov":{"id":self.id,"dest":[val['dest'][0],val['dest'][1]]}}
            self.factory.main.send_to_others(self.id, json.dumps(mes))
    
    def send(self, player, mes):
        try:
            self.factory.main.players[player].reply(mes)
        except Exception:
            print self.factory.main.players, player
            print "Failed: Not in here anymore"
         
class HeroMain():
    def __init__(self):
        self.id = 0;
        self.players = dict()
        self.factory = HeroFactory(self)
        self.factory.protocol = HeroProtocol
        self.reso = (480,320)
    
    def start(self):
        reactor.listenTCP(8000,self.factory)
        reactor.run()

    def idGen(self):
        self.id += 1
        return self.id
    
    def addPlayer(self, player, ref):
        print "Added Player", player
        self.players[player]=ref
    
    def removePlayer(self, player):
        print "Remove Player", player
        self.players.pop(player)
    
    def randomXY(self):
        x = random.randrange(0, self.reso[0])
        y = random.randrange(0, self.reso[1])
        return (x,y)
    
    def send_to_others(self, exclude, mes):
        print "sending to others", mes
        for player, ref in self.players.items():
            if exclude != player:
                print "sending to", ref.id
                ref.reply(mes)
        
# this only runs if the module was *not* imported
if __name__ == '__main__':
    v = HeroMain()
    v.start()
