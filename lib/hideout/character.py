from twisted.internet.task import LoopingCall
from twisted.python.log import msg
from twisted.python.failure import Failure
from twisted.python.failure import NoCurrentExceptionError
from _mysql_exceptions import OperationalError
import json

class Character():
    def __init__(self, name, address, udp, main):
        self.name  = name
        self.address = address
        self.udp = udp
        self.heartBeatCount = 5
        self.main = main
        self.world = None
        self.street = None
        self.room = None
        self.attributes = ""
        self.initAttributes()
        self.friends = {}
        self.handlers = { "disconnect":self.connectionLost,
                          "heartbeat":self.onHeartBeat,
                          "join":self.join,
                          "list":self.list,
                          "leave":self.leave,
                          "getcoin":self.getCoin,
                          "gethealth":self.getHealth,
                          "getfame":self.getFame,
                          "gethome":self.getHome,
                          "getlevel":self.getLevel,
                          "setcoin":self.setCoin,
                          "sethealth":self.setHealth,
                          "setfame":self.setFame,
                          "addfame":self.addFame,
                          "sethome":self.setHome,
                          "setlevel":self.setLevel,
                          "settoken":self.setToken,
                          "getaddress":self.getAddress,
                          "chat":self.chat,
                          "uncreate":self.uncreate,
                          "setattributes":self.setAttributes,
                          "getattributes":self.getAttributes,
                          "special":self.special,
                          "getfriends":self.getFriends,
                          "addfriend":self.addFriend,
                          "delfriend":self.delFriend,
                          "blockfriend":self.blockFriend,
                          "unblockfriend":self.unblockFriend,
                          "friendrequest":self.friendRequest,
                          "getitem":self.getItem,
                          "additem":self.addItem,
                          "delitem":self.delItem,
                          "setitem":self.setItem,
                          "getpower":self.getPower,
                          "setpower":self.setPower,
                          "getquestflag": self.getQflag,
                          "getquestplayed": self.getQplayed,
                          "setquestflag": self.setQflag,
                          "levelnotify":self.levelNotify}
        self.heartbeatloop = LoopingCall(self.sendHeartbeat)
        self.heartbeatloop.start(5, False)
        self.getFriends({"from":self.name})
    
    def sendOffline(self):
        offlineMessages = self.main.chatStore.get(self.name)
        self.main.chatStore.delete(self.name)
        if not offlineMessages == None:
            for mes in str(offlineMessages).split("|-|"):
                if mes!='':
                    self.reply(mes)
    
    def initAttributes(self):
        def cbOnResult(result):
            if len(result)>0:
                try: results = json.loads(result[0][0])
                except: results = ""
                self.attributes=results
            else:
                self.attributes=""
        def ebOnMysqlError(result):
            print result, "error"
            dat = {"getattributes":{"error":"MySQL Error"}}

        self.main.getAttributes(self.name).\
        addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def stop(self):
        msg ("%s has disconnected"%self.name)
        dc = json.dumps({'dc':{"from":self.name}})
        if self.room != None:
            self.room.send_to_others(self.name, dc)
            self.room.removePlayer(self.name)
        if self.street != None:
            self.street.removePlayer(self.name)
        if self.world != None:
            self.world.removePlayer(self.name)
        self.main.removePlayer(self.name)
        #todo friend list
        self.heartbeatloop.stop()
        self = None
    
    def sendHeartbeat(self):
        """
        Checks if this character instance is still connected.
        Does three heart beat retry
        """
        if self.heartBeatCount == 0:
            self.connectionLost({"from":self.name})
            return
        if self.heartBeatCount <= 3:
            hb = json.dumps({'heartbeat':1})
            self.reply(hb)
        
        def cbPush(result):                
            if result != None:
                print result
                for message in result:
                    if message[0] == "quest":
                        mes = {message[0]:{"code":message[1],
                                           "message":message[2]}}
                    else:
                        mes = {message[0]:message[2]}
                    self.reply(json.dumps(mes))
                
        def cbError(result):
            msg("Error on Push Service")
        
        self.main.getPush(self.name).addCallbacks(cbPush, cbError)
        self.heartBeatCount-=1
    
    def onHeartBeat(self, val):
        msg("Hearbeat OK")
        self.heartBeatCount = 5
    
    def onRelay(self, data):
        self.heartBeatCount = 5
        for handler, data in data.items():
            if handler in self.handlers:
                self.handlers[handler](data)
    
    def reply(self, data):
        self.udp.reply(data, self.address)
        
    def friendFunc(self, data, type):
        if type =="add":
            self.friends[data] = 0
            mes={"addfriend":data}
            self.reply(json.dumps(mes))
        if type =="del":
            self.friends.pop(data)
            mes={"delfriend":data}
            self.reply(json.dumps(mes))
        
    def chatReply(self, data, _from):
        self.udp.reply(data, self.address)
        
    def connectionLost(self, data):
        self.stop()
    
    def getWorlds(self, val):
        if val.has_key("from") and len(val.keys())==1:
            mes = {"worldlist":self.main.worldList}
            self.reply(json.dumps(mes))
    
    def getAddress(self, val):
        address = {}
        if self.world != None:
            address[self.world.name] = {}
            if self.street != None:
                address[self.world.name][self.street.name] = {}
                if self.room != None:
                    address[self.world.name][self.street.name]\
                    [self.room.name]={}
        self.reply(json.dumps(address))
                   
    def list(self, val):
        if self.world == None:
            if val.has_key("from") and len(val.keys())==1:
                mes = {"list":self.main.worldList}
                self.reply(json.dumps(mes))
        elif self.world != None and self.street == None:
            if val.has_key("from") and len(val.keys())==1:
                mes = {"list":self.world.streetList}
                self.reply(json.dumps(mes))
        elif self.world != None and self.street != None and self.room == None:
            if val.has_key("from") and len(val.keys())==1:
                mes = {"list":self.street.roomList}
                self.reply(json.dumps(mes))   
        else:
            mes = {"list":"error"}
            self.reply(json.dumps(mes)) 

    def join(self, val):
        if val.has_key("from") and val.has_key("realm") and self.world == None\
        and len(val.keys())==2:
            try:
                self.world = self.main.worlds[val["realm"]]
                self.world.addPlayer(val["from"], self)
                mes = {"join":{"realm":self.world.name,
                                    "description":self.world.desc}}
                self.reply(json.dumps(mes))
            except Exception:
                mes = {"join":{"error":"no such Realm"}}
                self.reply(json.dumps(mes))
            return
                
        if val.has_key("from") and val.has_key("realm") and self.world != None \
        and self.street == None and len(val.keys())==2:
            try:
                self.street = self.world.streets[val["realm"]]
                self.street.addPlayer(val["from"], self)
                """
                #join at middle screen
                roomNum = self.street.roomNum
                startroom = str((roomNum + (roomNum % 2) /2)-1)
                ##
                """
                mes = {"join":{"realm":self.street.name,
                                    "description":self.street.desc}}
                self.reply(json.dumps(mes))
                #self.join({"from":self.name, "realm":startroom})
            except:
                mes = {"join":{"error":"no such Realm"}}
                self.reply(json.dumps(mes))
            return
        
        if val.has_key("from") and val.has_key("realm") and self.world != None \
        and self.street != None and len(val.keys())==2:
            try:
                if self.room != None:
                    self.leave({"from":self.name})
                self.room = self.street.rooms[val["realm"]]
                self.room.addPlayer(val["from"], self)
                mes = {"join":{"realm":self.room.name,
                                    "description":self.room.desc}}
                self.reply(json.dumps(mes))
                
                #Get All player position and attributes
                #send it one at a time
                for player, attributes in\
                self.room.getAllPlayerAttributes().items():
                    room_upd = json.dumps({"room_upd":\
                                          {"player":\
                                          {player:attributes}}}) 
                    self.reply(room_upd)
                
                #send your position to others
                room_upd_others = json.dumps({'room_upd':\
                                              {"player":\
                                               {self.name:self.attributes}}})
                
                self.room.send_to_others(self.name, room_upd_others)

            except Exception:
                mes = {"joinroom":{"error":"no such Realm"}}
                self.reply(json.dumps(mes))
                return

    def leave(self, val):
        if val.has_key("from") and len(val.keys())==1:
            if self.room!=None:
                mes = {"leave":self.name}
                self.room.send_to_others("", json.dumps(mes))
                self.room.removePlayer(val["from"])
                self.room = None
            elif self.street!=None:
                self.street.removePlayer(val["from"])
                self.street = None
                mes = {"leave":self.name}
                self.reply(json.dumps(mes))
            elif self.world != None:
                self.world.removePlayer(val["from"])
                self.world = None
                mes = {"leave":self.name}
                self.reply(json.dumps(mes))
            else:
                mes = {"leave":{"error":"Not in any realm"}}
                self.reply(json.dumps(mes))

    def getCoin(self, val):
        name = '' 
        def cbOnResult(result):
            if len(result)>0:
                dat = {"getcoin":{"coin":result[0][0],
                                  "username":name}}
                self.reply(json.dumps(dat))                
            else:
                dat = {"getcoin":{"error":"not a user"}}
                self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"getcoin":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))
            
        if val.has_key("from") and len(val.keys())==1:
            name = val["from"]
            self.main.getCoin(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("username")\
            and len(val.keys())==2:
            name = val["username"]
            self.main.getCoin(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def getAttributes(self, val):
        name = ''
        def cbOnResult(result):
            if len(result)>0:
                try: result = json.loads(result[0][0])
                except: result = ""
                dat = dat = {"getattributes":{"attributes":result,
                                              "username":name}}
                self.reply(json.dumps(dat))
            else:
                dat = {"getattributes":{"error":"not a user"}}
                self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"getattributes":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and len(val.keys())==1:
            name = val["from"]
            self.main.getAttributes(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("username")\
            and len(val.keys())==2:
            name = val["username"]
            self.main.getAttributes(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
    
    def getHome(self, val):
        name = ''
        def cbOnResult(result):
            if len(result)>0:
                try: result = json.loads(result[0][0])
                except: result = ""
                dat = dat = {"gethome":{"home":result, "username":name}}
                self.reply(json.dumps(dat))
            else:
                dat = {"gethome":{"error":"not a user"}}
                self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            print result
            dat = {"gethome":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and len(val.keys())==1:
            name = val["from"]
            self.main.getHome(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("username")\
            and len(val.keys())==2:
            name = val["username"]
            self.main.getHome(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
 
    def getHealth(self, val):
        name = ''
        def cbOnResult(result):
            if len(result)>0:
                dat = {"gethealth":{"health":result[0][0],
                                    "max_health":result[0][1],
                                    "username":name}}
                self.reply(json.dumps(dat))                
            else:
                dat = {"gethealth":{"error":"not a user"}}
                self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"gethealth":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and len(val.keys())==1:
            name = val["from"]
            self.main.getHealth(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("username")\
            and len(val.keys())==2:
            name = val["username"]
            self.main.getHealth(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def getFame(self, val):
        name = ''
        def cbOnResult(result):
            if len(result)>0:
                dat = {"getfame":{"fame":result[0][0],
                                  "username":name}}
                self.reply(json.dumps(dat))                
            else:
                dat = {"getfame":{"error":"not a user"}}
                self.reply(json.dumps(dat))
                
        def ebOnMysqlError(result):
            dat = {"getfame":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and len(val.keys())==1:
            name = val["from"]
            self.main.getFame(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("username")\
            and len(val.keys())==2:
            name = val["username"]
            self.main.getFame(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def getLevel(self, val):
        name = ''
        def cbOnResult(result):
            if len(result)>0:
                dat = {"getlevel":{"level":result[0][0],
                                  "username":name}}
                self.reply(json.dumps(dat))                
            else:
                dat = {"getlevel":{"error":"not a user"}}
                self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"getlevel":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and len(val.keys())==1:
            name = val["from"]
            self.main.getLevel(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("username")\
            and len(val.keys())==2:
            name = val["username"]
            self.main.getLevel(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def setToken(self, val):
        def cbOnResult(result):
            dat = {"settoken":val}
            self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"settoken":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("val") and len(val.keys())==2:
            name = val["from"]
            val = val["val"]
            self.main.setToken(name, val).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def setCoin(self, val):
        def cbOnResult(result):
            dat = {"setcoin":val}
            self.reply(json.dumps(dat))                
        def ebOnMysqlError(result):
            dat = {"setcoin":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("val") and len(val.keys())==2:
            name = val["from"]
            val = val["val"]
            self.main.setCoin(name, val).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def setAttributes(self, val):
        def cbOnResult(result):
            dat = {"setattributes":val}
            self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"setattributes":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("val") and len(val.keys())==2:
            name = val["from"]
            val = val["val"]
            self.main.setAttributes(name, json.dumps(val)).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
    
    def setHome(self, val):
        def cbOnResult(result):
            dat = {"sethome":val}
            self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"sethome":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("val") and len(val.keys())==2:
            name = val["from"]
            val = val["val"]
            self.main.setHome(name, json.dumps(val)).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def setHealth(self, val):
        def cbOnResult(result):
            dat = {"sethealth":val}
            self.reply(json.dumps(dat))                
        def ebOnMysqlError(result):
            dat = {"sethealth":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("val") and len(val.keys())==2:
            name = val["from"]
            val = val["val"]
            self.main.setHealth(name, val).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def setFame(self, val):
        def cbOnResult(result):
            dat = {"setfame":val}
            self.reply(json.dumps(dat))                
        def ebOnMysqlError(result):
            dat = {"setfame":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("val") and len(val.keys())==2:
            name = val["from"]
            val = val["val"]
            self.main.setFame(name, val).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("val")\
            and val.has_key("username") and len(val.keys())==3:
            name = val["username"]
            val = val["val"]
            self.main.setFame(name, val).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def addFame(self, val):
        """
        types
        1 = home
        2 = character
        """
        set_other = 0
        def cbOnResult(result):
            dat = {"addfame":{"fame":valx, "username":name}}
            dat = json.dumps(dat)
            if set_other == 1:
                if type.__str__() == "1":
                    m = "Your Home has been rated!"
                if type.__str__() == "2":
                    m = "Your Character has been rated!"
                self.main.apnSend(name, m)
                self.send(name, dat)
                self.sendNews(name, m)
            self.reply(dat)
            
        def ebOnMysqlError(result):
            print result
            dat = {"addfame":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))
        
        if not val.has_key("type"):
            val["type"]=0

        if val.has_key("from") and val.has_key("val") and val.has_key("type")\
            and len(val.keys())==3:
            name = val["from"]
            type = val["type"]
            valx = val["val"]
            self.main.addFame(name, valx).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("val")\
            and val.has_key("username") and val.has_key("type")\
            and len(val.keys())==4:
            set_other = 1
            name = val["username"]
            type = val["type"]
            valx = val["val"]
            self.main.addFame(name, valx).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)

    def setLevel(self, val):
        def cbOnResult(result):
            dat = {"setlevel":val}
            self.reply(json.dumps(dat))                
        def ebOnMysqlError(result):
            dat = {"setlevel":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("val") and len(val.keys())==2:
            name = val["from"]
            val = val["val"]
            self.main.setLevel(name, val).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
    
    def setItem(self, val):
        def cbOnResult(result):
            dat = {"setitem":{"item":id,"type":type,"quantity":quantity}}
            self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"setitem":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("id") and val.has_key("type")\
            and val.has_key("quantity") and len(val.keys())==4:
            name = val["from"]
            id = val["id"]
            type = val["type"]
            quantity = val["quantity"]
            self.main.setItem(name, id, type, quantity).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("id") and val.has_key("type")\
            and val.has_key("quantity") and val.has_key("username")\
            and len(val.keys())==5:
            name = val["username"]
            id = val["id"]
            type = val["type"]
            quantity = val["quantity"]
            self.main.setItem(name, id, type, quantity).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
    
    def addItem(self, val):
        def cbOnResult(result):
            dat = {"additem":{"item":id,"type":type,"quantity_added":quantity}}
            self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"additem":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("id") and val.has_key("type")\
            and val.has_key("quantity") and len(val.keys())==4:
            name = val["from"]
            id = val["id"]
            type = val["type"]
            quantity = val["quantity"]
            self.main.addItem(name, id, type, quantity).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("id") and val.has_key("type")\
            and val.has_key("quantity") and val.has_key("username")\
            and len(val.keys())==5:
            name = val["username"]
            id = val["id"]
            type = val["type"]
            quantity = val["quantity"]
            self.main.addItem(name, id, type, quantity).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
    
    def delItem(self, val):
        def cbOnResult(result):
            dat = {"delitem":{"item":id,
                              "type":type,
                              "quantity_deleted":quantity}}
            self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"delitem":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("id") and val.has_key("type")\
            and val.has_key("quantity") and len(val.keys())==4:
            name = val["from"]
            id = val["id"]
            type = val["type"]
            quantity = val["quantity"]
            self.main.delItem(name, id, type, quantity).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("id") and val.has_key("type")\
            and val.has_key("quantity") and val.has_key("username")\
            and len(val.keys())==5:
            name = val["username"]
            id = val["id"]
            type = val["type"]
            quantity = val["quantity"]
            self.main.delItem(name, id, type, quantity).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
    
    def getItem(self, val):
        def cbRes(res):
            mes = {"getitem":res}
            self.reply(json.dumps(mes))
        def cbError(err_):
            trap = err_.trap(NoCurrentExceptionError, OperationalError)
            if trap == NoCurrentExceptionError:
                msg("No Result, traceback: %s"%err_)
                mes = {"getitem":0}
                self.reply(json.dumps(mes))
            elif trap == OperationalError:
                msg("MySQL No connection, traceback: %s"%err_)
                mes = {"getitem":{"error":"Database Error"}}
                self.reply(json.dumps(mes))
            else:
                msg("General Error, traceback: %s"%err_)
                mes = {"getitem":{"error":"Internal Error"}}
                self.reply(json.dumps(mes))
        
        if val.has_key("from") and len(val.keys())==1:
            self.main.getItem(val["from"]).addCallback(cbRes)\
                .addErrback(cbError)

    def setPower(self, val):
        def cbOnResult(result):
            dat = {"setpower":{"power":id,"level":level}}
            self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"setpower":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("power")\
            and val.has_key("level") and len(val.keys())==3:
            name = val["from"]
            power = val["power"]
            level = val["level"]
            self.main.setPower(name, power, level).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("power")\
            and val.has_key("level") and val.has_key("username")\
            and len(val.keys())==4:
            name = val["username"]
            power = val["power"]
            level = val["level"]
            self.main.setPower(name, power, level).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
            
    def getPower(self, val):
        def cbRes(res):
            mes = {"getpower":res}
            self.reply(json.dumps(mes))
        def cbError(err_):
            trap = err_.trap(NoCurrentExceptionError, OperationalError)
            if trap == NoCurrentExceptionError:
                msg("No Result, traceback: %s"%err_)
                mes = {"getpower":0}
                self.reply(json.dumps(mes))
            elif trap == OperationalError:
                msg("MySQL No connection, traceback: %s"%err_)
                mes = {"getpower":{"error":"Database Error"}}
                self.reply(json.dumps(mes))
            else:
                msg("General Error, traceback: %s"%err_)
                mes = {"getpower":{"error":"Internal Error"}}
                self.reply(json.dumps(mes))
        
        if val.has_key("from") and len(val.keys())==1:
            self.main.getPower(val["from"]).addCallback(cbRes)\
                .addErrback(cbError)
    
    def getQflag(self, val):
        name = ''
        def cbOnResult(result):
            if len(result)>0:
                dat = {"getquestflag":{"quest":quest,
                                       "flag":1,
                                       "username":name}}
                self.reply(json.dumps(dat))                
            else:
                dat = {"getquestflag":{"quest":quest,
                                       "flag":0,
                                       "username":name}}
                self.reply(json.dumps(dat))
                
        def ebOnMysqlError(result):
            print result
            dat = {"getquestflag":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and len(val.keys())==2:
            name = val["from"]
            quest = val["quest"]
            self.main.getQflag(name, quest).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("username")\
            and len(val.keys())==3:
            name = val["username"]
            quest = val["quest"]
            self.main.getQflag(name, quest).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
    def getQplayed(self, val):
        name = ''
        def cbOnResult(result):
            if len(result)>0:
                questplayed = []
                for res in result:
                    questplayed.append(res[0])
                dat = {"getquestplayed":questplayed}
                self.reply(json.dumps(dat))                
            else:
                dat = {"getquestplayed":[]}
                self.reply(json.dumps(dat))
                
        def ebOnMysqlError(result):
            print result
            dat = {"getquestplayed":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and len(val.keys())==1:
            name = val["from"]
            self.main.getQplayed(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("username")\
            and len(val.keys())==2:
            name = val["username"]
            self.main.getQplayed(name).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
    
    def setQflag(self, val):
        def cbOnResult(result):
            dat = {"setquestflag":{"quest":quest,"flag":1}}
            self.reply(json.dumps(dat))
        def ebOnMysqlError(result):
            dat = {"setquestflag":{"error":"MySQL Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("quest") and len(val.keys())==2:
            name = val["from"]
            quest = val["quest"]
            self.main.setQflag(name, quest).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
        
        if val.has_key("from") and val.has_key("quest")\
            and val.has_key("username") and len(val.keys())==3:
            name = val["username"]
            quest = val["quest"]
            self.main.setQflag(name, quest).\
            addCallback(cbOnResult).addErrback(ebOnMysqlError)
    
    def chat(self, val):
        if val.has_key("from") and val.has_key("to") and\
        val.has_key("message") and len(val.keys())==3:
            
            def cbRes(res):
                print "DEB", res
                if res == 1 or res == self.name:
                    msg("%s is blocked by %s"%(val["from"], val["to"]))
                    return
                else:
                    mes = json.dumps({"chat":val})
                    if self.send(val["to"], mes) == False:
                        
                        def cbStoreOfflineMessage(result):
                            if type(result).__name__ == "str":
                                cacheResult = self.main.chatStore\
                                              .get(val["to"].__str__())
                                if cacheResult == None:
                                    self.main.chatStore.set(val["to"].__str__()\
                                                            ,"|-|%s"%mes)
                                else:
                                    self.main.chatStore.append\
                                            (val["to"].__str__(),"|-|%s"%mes)
                                self.main.apnSend(val["to"],\
                                                  "You have a message")
                            elif result == -1:
                                msg ("%s is not registered, dumping"%val["to"])
                            elif result == -2:
                                msg("MySQL Error")
            
                        def ebOnError(result):
                            print result
                            dat = {"chat":{"error":"Unknown Error"}}
                            self.reply(json.dumps(dat))
            
                        msg("Failed: player not here,\
                        Trying to store Offline Message")
                        self.main.checkUser(val["to"])\
                                  .addCallback(cbStoreOfflineMessage)\
                                  .addErrback(ebOnError)
                                  
            def cbError(err_):
                trap = err_.trap(NoCurrentExceptionError,\
                                 OperationalError)
                if trap == NoCurrentExceptionError:
                    msg("No Result, traceback: %s"%err_)
                elif trap == OperationalError:
                    msg("MySQL No connection, traceback: %s"%err_)
                else: msg("General Error, traceback: %s"%err_)

            if self.friends.has_key(val["to"]):
                self.main.checkIfBlockedFriend(val["to"], val["from"])\
                .addCallback(cbRes).addErrback(cbError)
            else:
                self.main.checkIfBlocked(val["to"], val["from"])\
                .addCallback(cbRes).addErrback(cbError)
            

        elif val.has_key("from") and val.has_key("message")\
            and len(val.keys())==2:
            mes = {"chat":val}
            self.room.send_to_others(val["from"], json.dumps(mes))

    def sendNews(self,to, message):
        _from = self.name            
        payload={"news":{"from":_from,"message":message}}
        mes = json.dumps(payload)
        if self.send(to, mes) == False:
            def cbStoreOfflineMessage(result):
                if type(result).__name__ == "str":
                    cacheResult = self.main.chatStore\
                                  .get(to.__str__())
                    if cacheResult == None:
                        self.main.chatStore.set(to.__str__()\
                                                ,"|-|%s"%mes)
                    else:
                        self.main.chatStore.append\
                                (to.__str__(),"|-|%s"%mes)
                    self.main.apnSend(to,\
                                      "A News has been delivered")
                elif result == -1:
                    msg ("%s is not registered, dumping"%to)
                elif result == -2:
                    msg("MySQL Error")

            def ebOnError(result):
                print result
                dat = {"news":{"error":"Unknown Error"}}
                self.reply(json.dumps(dat))

            msg("Failed: player not here,\
            Trying to store Offline Message")
            self.main.checkUser(to)\
                      .addCallback(cbStoreOfflineMessage)\
                      .addErrback(ebOnError)
                              

    def special(self, val):
        if val.has_key("from") and val.has_key("power")\
            and len(val.keys())==2:
            mes = {"special":val}
            self.room.send_to_others(val["from"], json.dumps(mes))
    
    def getFriends(self, val):
        def cbRes(res):
            self.friends = res
            mes = {"getfriends":self.friends}
            self.reply(json.dumps(mes))
        def cbError(err_):
            trap = err_.trap(NoCurrentExceptionError, OperationalError)
            if trap == NoCurrentExceptionError:
                msg("No Result, traceback: %s"%err_)
                mes = {"getfriends":0}
                self.reply(json.dumps(mes))
            elif trap == OperationalError:
                msg("MySQL No connection, traceback: %s"%err_)
                mes = {"getfriends":{"error":"Database Error"}}
                self.reply(json.dumps(mes))
            else:
                msg("General Error, traceback: %s"%err_)
                mes = {"getfriends":{"error":"Internal Error"}}
                self.reply(json.dumps(mes))
        
        if val.has_key("from") and len(val.keys())==1:
            if len(self.friends)==0:
                self.main.getFriends(val["from"]).addCallback(cbRes)\
                    .addErrback(cbError)
            else:
                mes = {"getfriends":self.friends}
                self.reply(json.dumps(mes))

    def addFriend(self, val):
        if val.has_key("from") and val.has_key("friendname")\
            and len(val.keys())==2:
            if  self.friends.has_key(val["friendname"]):
                dat = {"addFriend":
                       {"error":"Already a friend"}
                      }
                self.reply(json.dumps(dat))
                return
            else:
                def cbResult(result):
                    if type(result).__name__ == "str":
                        def cbResult(result):
                            print result, "dev"
                            dat = {"addfriend":
                              {"success":val["friendname"]}}
                            self.reply(json.dumps(dat))
                            self.friendNotify\
                                (val["friendname"], self.name, "add")
                            self.friends[val["friendname"]]=0
                            
                        def ebError(result):
                            msg(result)
                            dat = {"addfriend":{"error":"Internal Error"}}
                            self.reply(json.dumps(dat))
                        
                        self.main.addFriend(val["from"],val["friendname"])\
                            .addCallback(cbResult).addErrback(ebError)
                        
                    elif result == -1:
                        msg ("%s is not registered, dumping"%val["to"])
                        dat = {"addfriend":{"error":
                                            "Friend is not an existing user"}}
                        self.reply(json.dumps(dat))
                    elif result == -2:
                        msg("MySQL Error")
                        dat = {"addfriend":{"error":
                                            "Database Error"}}
                        self.reply(json.dumps(dat))

                def ebOnError(result):
                    print result
                    dat = {"addfriend":{"error":"Internal Error"}}
                    self.reply(json.dumps(dat))

                self.main.checkUser(val["friendname"])\
                          .addCallback(cbResult)\
                          .addErrback(ebOnError)

    def delFriend(self, val):
        if val.has_key("from") and val.has_key("friendname")\
            and len(val.keys())==2:
            if  not self.friends.has_key(val["friendname"]):
                dat = {"delFriend":
                       {"error":"Not a friend"}
                      }
                self.reply(json.dumps(dat))
                return
            else:
                def cbResult(result):
                    print result, "dev"
                    dat = {"delfriend":{"success":val["friendname"]}}
                    self.reply(json.dumps(dat))
                    self.friends.pop(val["friendname"])
                    self.friendNotify(val["friendname"], self.name, "del")
                    
                def ebError(result):
                    print result
                    dat = {"delfriend":{"error":"Internal Error"}}
                    self.reply(json.dumps(dat))
                
                self.main.delFriend(val["from"],val["friendname"])\
                    .addCallback(cbResult).addErrback(ebError)
    
    def blockFriend(self, val):
        def cbOnResult(result):
            dat = {"blockfriend":{"success":val}}
            self.friends[val] = 1
            self.reply(json.dumps(dat))                
        def ebError(result):
            print result
            dat = {"blockfriend":{"error":"Internal Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("friendname")\
            and len(val.keys())==2:
            name = val["from"]
            val = val["friendname"]
            if  not self.friends.has_key(val):
                self.main.blockUser(name, val).\
                addCallback(cbOnResult).addErrback(eblError)
            else:
                self.main.blockFriend(name, val).\
                addCallback(cbOnResult).addErrback(eblError)
    
    def unblockFriend(self, val):
        def cbOnResult(result):
            dat = {"unblockfriend":{"success":val}}
            self.friends[val] = 0
            self.reply(json.dumps(dat))                
        def ebError(result):
            dat = {"unblockfriend":{"error":"Internal Error"}}
            self.reply(json.dumps(dat))

        if val.has_key("from") and val.has_key("friendname")\
            and len(val.keys())==2:
            name = val["from"]
            val = val["friendname"]
            if  not self.friends.has_key(val):
                self.main.unblockUser(name, val).\
                addCallback(cbOnResult).addErrback(ebError)
            else:
                self.main.unblockFriend(name, val).\
                addCallback(cbOnResult).addErrback(ebError)

    def friendRequest(self, val):
        if val.has_key("from") and val.has_key("to") and len(val.keys())==2:
            if  self.friends.has_key(val["to"]):
                dat = {"friendrequest":
                       {"error":"Already a friend"}
                      }
                self.reply(json.dumps(dat))
                return
            else:
                mes = json.dumps({"friendrequest":val})
                if self.send(val["to"], mes) == False:
                    def cbStoreOfflineMessage(result):
                        if type(result).__name__ == "str":
                            cacheResult = self.main.chatStore\
                                          .get(val["to"].__str__())
                            if cacheResult == None:
                                self.main.chatStore.set(val["to"].__str__()\
                                                        ,"|-|%s"%mes)
                            else:
                                self.main.chatStore.append(val["to"].__str__()\
                                                        ,"|-|%s"%mes)
                            self.main.apnSend(val["to"],\
                                                  "You have a Friend Request")
                        elif result == -1:
                            msg ("%s is not registered, dumping"%val["to"])
                            dat = {"friendrequest":{"error":
                                            "Friend is not an existing user"}}
                            self.reply(json.dumps(dat))
                        elif result == -2:
                            msg("MySQL Error")
                            dat = {"friendrequest":{"error":
                                                "Database Error"}}
                            self.reply(json.dumps(dat))
    
                    def ebOnError(result):
                        dat = {"friendrequest":{"error":"Internal Error"}}
                        self.reply(json.dumps(dat))
    
                    msg("ERR: player offline, Trying to store Offline Request")
                    self.main.checkUser(val["to"])\
                              .addCallback(cbStoreOfflineMessage)\
                              .addErrback(ebOnError)

    def uncreate(self, val):
        if val.has_key("from") and val.has_key("device_id") and \
          len(val.keys())==2:
            self.main.deleteUser(val["device_id"])
            dat = {"uncreate":"success, will disconnect"}
            self.reply(json.dumps(dat))
            self.stop()

    def send(self, player, mes):
        try:
            self.main.players[player].reply(mes)
            return True
        except Exception:
            return False
    
    def friendNotify(self, player, friend, type):
        try:
            self.main.players[player].friendFunc(friend, type)
            return True
        except Exception:
            return False

    def send_friend_news(self, mes):
            for friend in self.friends.keys():
                self.sendNews(friend, mes)
    
    def levelNotify(self, val):
        if val.has_key("from") and val.has_key("val") and \
          len(val.keys())==2:
            mes = self.name+" is now Level "+str(val["val"])
            self.send_friend_news(mes)
            dat = {"levelnotify":"success"}
            self.reply(json.dumps(dat))
        