from twisted.python.log import msg

class Realm():
    def __init__(self, name, desc):
        self.id = 0;
        self.players = dict()
        self.name = name
        self.desc = desc

    def addPlayer(self, player, ref):
        msg("Added Player %s "%player)
        self.players[player]=ref
        msg("Player Map: %s"%self.players)
    
    def removePlayer(self, player):
        msg("Removed Player %s "%player)
        self.players.pop(player)
        msg("Player Map: %s"%self.players)
    
    def send_to_others(self, exclude, mes):
        for player, ref in self.players.items():
            if exclude != player:
                msg("sending to %s"%ref.name)
                ref.reply(mes)

class World(Realm):
    def __init__(self, name, desc, main):
        Realm.__init__(self, name, desc)
        self.main = main
        self.streets = self.initializeStreets()
        self.streetList = self.generateStreetList()
        #print self.streets
        
    
    def initializeStreets(self):
        streets = {}
        for street in self.main.worldConf.options(self.name):
            if street.strip() != "description":
                opts = str(self.main.worldConf.get(self.name, street)).split("|")
                streets[opts[0]]=Street(opts[0],\
                                   int(opts[1]),\
                                   opts[2],\
                                   self)
        return streets
    
    def generateStreetList(self):
        v = {}
        for x in self.streets.keys():
            v[x]=self.streets[x].desc
        return v

class Street(Realm):
    def __init__(self, name, roomNum, desc, world):
        Realm.__init__(self, name, desc)
        self.world = world
        self.roomNum = roomNum
        self.rooms = self.initializeRooms(roomNum)
        self.roomList = self.generateRoomList()    
    
    def initializeRooms(self, roomNum):
        cnt = 0;
        room = {}
        while cnt != roomNum:
            room[str(cnt)]=Room(str(cnt),\
                           "room "+str(cnt),\
                           self)
            cnt+=1
        return room
    
    def generateRoomList(self):
        v = {}
        for x in self.rooms.keys():
            v[x]=self.rooms[x].desc
        return v
    
class Room(Realm):
    def __init__(self, name, desc, street):
        Realm.__init__(self, name, desc)
        self.street = street
    
    def getAllPlayerAttributes(self):
        playerats = {}
        for chars in self.players.values():
            playerats[chars.name]=chars.attributes
        return playerats
