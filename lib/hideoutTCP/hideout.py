EXPIRETIME = 86400
from twisted.internet import reactor, protocol
from twisted.internet.task import LoopingCall
from twisted.protocols import basic
from socket import SOL_SOCKET, SO_BROADCAST, gethostname
from realm import Realm, World
from hideoutTCP import HideoutTCP
from twisted.internet import defer
from twisted.python.log import msg
import json, random

from twisted.enterprise import adbapi

class HeroMain(Realm):
    def __init__(self, worldConf,\
                 dbpool,\
                 dev_id_cache,\
                 offline_message_cache,\
                 pushPB, apnPB, fbinv):
        self.dbpool = dbpool
        Realm.__init__(self, "server", "Mainserver")
        self.worldConf = worldConf
        self.worlds = self.initializeWorlds()
        self.worldList = self.generateWorldList()
        self.deviceIDCache = dev_id_cache
        self.chatStore = offline_message_cache
        self.chatStore
        self.dbKA = LoopingCall(self.dbKeepAlive)
        self.dbKA.start(3600)
        self.pushPB = pushPB
        self.apnPB = apnPB
        self.fbinv = fbinv
        self.fbinv.service = self   
          
    def fbinvite(self, _from, fbfrom, _to):
        self.fbinv.remoteDialback.callRemote\
            ("invite", _from, fbfrom, _to)
    
    def fbinviteResponse(self, _from):
        dat = {"fbinvite":{"message":"invite stored"}}
        print "Debug", self.players
        self.players[_from].reply(json.dumps(dat))
        
    def fbinviteList(self, _from, fb):
        self.fbinv.remoteDialback.callRemote\
            ("list", _from, fb)
    
    def fbinviteListResponse(self, _to, list):
        dat = {"fbinvitelist":list}
        self.players[_to].reply(json.dumps(dat))
    
    def fbinviteAccept(self, _from, fbfrom, _to):
        self.fbinv.remoteDialback.callRemote\
            ("accept", _from, fbfrom, _to)
    
    def fbinviteAcceptResponse(self, _from, _to):
        dat = {"fbinviteaccept":{"message":"accepted"}}
        self.players[_to].reply(json.dumps(dat))
        self.players[_to].sendNews(_from, "accepted", _type="fbinviteaccept",\
                                   _apn = "%s has accepted your invitation"%_to)
    
    def apnSend(self, username, message):
        def cbResult(res):
            print res
            if len(res)>0:
                print res[0][0]
                d = defer.Deferred()
                def cbApn(result):
                    if result == None:
                        d.callback(None)
                    else:
                        d.callback(result)
                    return d
                def cbError(result):
                    print result
                    return d
                if self.apnPB.remoteDialback != None:
                    return self.apnPB.remoteDialback\
                    .callRemote("sendMessage", res[0][0], message)\
                    .addCallbacks(cbApn, cbError)
                else:
                    msg ("APN Service is Down")
                    return d                
            else: 
                msg("No Token on DB, not sent.")
        def cbErr(res):
            print res
            msg ("Error on MySQL")
        self.getToken(username).addCallback(cbResult).addErrback(cbErr)
    """
    def addPushException(self, pushCodes, username):
        d = defer.Deferred()
        def cbResult(result):
            d.callback(result)
            return d
        def cbError(result):
            d.callback(-1)
            return d
        self.pushPB.remoteDialback\
            .callRemote("addException", pushCodes, username)
    """
    
    def getPush(self, username):
        print "DEBUG on PUSH", self.pushPB
        d = defer.Deferred()
        def cbPush(result):
            if result == None:
                d.callback(None)
            else:
                d.callback(result)
            return d
        def cbError(result):
            d.errback("Error on Push Service")
            return d
        if self.pushPB.remoteDialback != None:
            return self.pushPB.remoteDialback\
            .callRemote("getMessages", username).addCallbacks(cbPush, cbError)
        else:
            msg ("Push Service is Down")
            return d
            
    def dbKeepAlive(self):
        msg("Sending DB keepalive")
        self.dbpool.runOperation("select 1");
    
    def authenticate(self, d_id):
        print "auth"
        d = defer.Deferred()
        def cbResult(result):
            print result, "test"
            if len(result)==0 or result =="None":
                d.callback(-1)
                return d
            else:
                d.callback(result[0][0])
                print self.deviceIDCache.set(d_id.__str__(),result[0][0])                       
                msg("%s found in DB"%result)
                return d
        def cbError(res):
            d.callback(-2)
            return d
        
        try:
            cacheRes = self.deviceIDCache.get(d_id.__str__())
        except:
            cacheRes = None       
 
        if cacheRes != None :
            user = cacheRes
            msg ("%s found in cache, no need to query from DB"%user)
            d.callback(user)
            return d
        
        return self.dbpool.runQuery("select username from ho_users where\
               device_id = '%s'"%(d_id)).addCallback(cbResult)\
                                        .addErrback(cbError)
                                        
    
    def getFriends(self, username):
        d = defer.Deferred()
        def cbResult(result):
            
            if len(result) == 0 or result == "None":
                d.errback()
                return d
            else:
                new_res = []
                for row in result:
                    new_res.append(tuple(row))
                print new_res
                d.callback(dict(new_res))
                return d

        return self.dbpool.runQuery("select friend, flag from friend_list where\
                user = '%s'"%(username)).addCallback(cbResult)
        
    def addFriend(self, username, friend):
        return self.dbpool.runQuery("insert into friend_list values\
                 ('%s','%s','%s');insert into friend_list values\
                 ('%s','%s','%s')"%(username, friend, 0, friend, username, 0))
        
    def delFriend(self, user, friend):
        print "delete from friend_list where\
                 user='%s' and friend = '%s';delete from friend_list where\
                 user='%s' and friend = '%s'"%(user, friend,friend,user)
        return self.dbpool.runQuery("delete from friend_list where\
                 user='%s' and friend = '%s';delete from friend_list where\
                 user='%s' and friend = '%s'"%(user, friend,friend,user))
    
    def checkIfBlockedFriend(self, username, friend):
        d = defer.Deferred()
        def cbResult(result):
            if len(result) > 0:         
                d.callback(result[0][0])
                return d
            else: 
                d.callback(None)
                return d
        
        
        return self.dbpool.runQuery("select flag from friend_list where\
                user = '%s' and friend = '%s'"%(username, friend))\
                .addCallback(cbResult)
    
    def checkIfBlocked(self, username, blockie):
        d = defer.Deferred()
        def cbResult(result):
            if len(result) > 0:         
                d.callback(result[0][0])
                return d
            else: 
                d.callback(None)
                return d
        
        
        return self.dbpool.runQuery("select blocked_user from block_list where\
                user = '%s' and blocked_user = '%s'"%(username, blockie))\
                .addCallback(cbResult)

    def blockUser(self, username, blockie):
        return self.dbpool.runQuery("insert ignore into block_list values\
                 ('%s', '%s')"%( username, blockie))
    
    def unblockUser(self, username, blockie):
        return self.dbpool.runQuery("delete from block_list where\
                 user= '%s' and blocked_user ='%s'"%(username, blockie))
    
    def blockFriend(self, username, friend):
        return self.dbpool.runQuery("update friend_list set flag = '%s' where\
                 user='%s' and friend = '%s'"%(1, username, friend))
    
    def unblockFriend(self, username, friend):
        return self.dbpool.runQuery("update friend_list set flag = '%s' where\
                 user='%s' and friend = '%s'"%(0, username, friend))
    
    def addItem(self, username, icode, type, quantity):
        return self.dbpool.runQuery("insert into inventory values\
                 ('%s', '%s', '%s', '%s') on duplicate key update\
                 quantity=if((quantity+%s)<0,0,quantity+%s)"%\
                 (username,icode,type,quantity,quantity,quantity))
    
    def delItem(self, username, icode, type, quantity):
        return self.dbpool.runQuery("insert into inventory values\
                 ('%s', '%s', '%s', '%s') on duplicate key update\
                 quantity=if((quantity-%s)<0,0,quantity-%s)"%\
                 (username,icode,type,quantity,quantity,quantity))
    
    def setItem(self, username, icode, type, quantity):
        return self.dbpool.runQuery("replace into inventory values\
                 ('%s', '%s', '%s', '%s')"%( username, icode, type, quantity))
    
    def getItem(self, username):
        d = defer.Deferred()
        def cbResult(result):
            
            if len(result) == 0 or result == "None":
                d.errback()
                return d
            else:
                new_res = []
                for row in result:
                    new_res.append(tuple(row))
                print new_res
                d.callback(new_res)
                return d

        return self.dbpool.runQuery("select item, type, quantity from\
               inventory where user = '%s' and quantity > 0"
               %(username)).addCallback(cbResult)
    
    def setPower(self, username, pcode, level):
        return self.dbpool.runQuery("replace into powers values\
                 ('%s', '%s', '%s')"%( username, pcode, level))
    
    def getPower(self, username):
        d = defer.Deferred()
        def cbResult(result):
            
            if len(result) == 0 or result == "None":
                d.errback()
                return d
            else:
                new_res = []
                for row in result:
                    new_res.append(tuple(row))
                print new_res
                d.callback(dict(new_res))
                return d

        return self.dbpool.runQuery("select power, level from powers where\
                user = '%s'"%(username)).addCallback(cbResult)
    
    def setToken(self, username, token):
        return self.dbpool.runQuery("update ho_users set token = '%s' where\
                username = '%s'"%(token, username))
    
    def getToken(self, username):
        return self.dbpool.runQuery("select token from ho_users where\
                username = '%s'"%(username))
    
    def getCoin(self, username):
        return self.dbpool.runQuery("select coin from ho_users where\
                username = '%s'"%(username))
    
    def setCoin(self, username, coin):
        return self.dbpool.runQuery("update ho_users set coin = '%s' where\
                username = '%s'"%(coin, username))
    
    def getHealth(self, username):
        return self.dbpool.runQuery("select health, max_health from ho_users\
                where username = '%s'"%(username))
    
    def setHealth(self, username, health):
        return self.dbpool.runQuery("update ho_users set health = '%s' where\
                username = '%s'"%(health, username))
    
    def getFame(self, username):
        return self.dbpool.runQuery("select fame from ho_users where\
                username = '%s'"%(username))
    
    def setFame(self, username, fame):
        return self.dbpool.runQuery("update ho_users set fame = '%s' where\
                username = '%s'"%(fame, username))
    
    def addFame(self, username, quantity):
        return self.dbpool.runQuery("update ho_users set fame=fame + %s  where\
                username = %s",(quantity, username))
        
    def setQflag(self, username, quest):
        return self.dbpool.runQuery("insert into quest_played values\
                 ('%s', '%s', now()) on duplicate key update\
                 tstamp=if\
                 ((unix_timestamp(now())-unix_timestamp(tstamp))>=86400,\
                 now(),tstamp)"%\
                 (username,quest))
    
    def getQflag(self, username, quest):
        return self.dbpool.runQuery("select tstamp from quest_played where\
                user = %s and quest = %s and\
                (unix_timestamp(now())-unix_timestamp(tstamp))<%s",\
                (username, quest, EXPIRETIME))
    
    def getQplayed(self, username):
        return self.dbpool.runQuery("select quest from quest_played where\
                user = %s and\
                (unix_timestamp(now())-unix_timestamp(tstamp))<%s",\
                (username, EXPIRETIME))
    
    def getLevel(self, username):
        return self.dbpool.runQuery("select level from ho_users where\
                username = '%s'"%(username))
   
    def setLevel(self, username, level):
        return self.dbpool.runQuery("update ho_users set level = '%s' where\
                username = '%s'"%(level, username))
        
    def getAttributes(self, username):
        return self.dbpool.runQuery("select attributes from ho_users where\
                username = '%s'"%(username))

    def setAttributes(self, username, attr):
        return self.dbpool.runQuery("update ho_users set attributes = %s\
                where username = %s",(attr, username))
        
    def getHome(self, username):
        return self.dbpool.runQuery("select home from ho_users where\
                username = '%s'"%(username))

    def setHome(self, username, home):
        return self.dbpool.runQuery("update ho_users set home = %s where\
                username = %s", (home, username))
    
    def deleteUser(self, did):
        print ("delete from ho_users where device_id = '%s'"%(did))
        name = self.deviceIDCache.get(did.__str__())
        self.deviceIDCache.delete(did.__str__())
        return self.dbpool.runQuery("delete from ho_users where\
                device_id = %s; delete from quest_played wher user=%s;\
                delete from powers where user=%s\
                delete from inventory where user=%s",(did, name, name, name))

    def checkUser(self, username):
        d = defer.Deferred()
        def cbResult(result):
            if len(result) == 0 or result == "None":
                d.callback(-1)
                return d
            else:
                d.callback(result[0][0])
                msg("%s found in DB"%result[0][0])
                return d
        
        def cbError(res):
            d.callback(-2)
            return d
        
        return self.dbpool.runQuery("select username from ho_users where\
               username = '%s'"%(username)).addCallback(cbResult)\
                                           .addErrback(cbError)
    
    def checkEmail(self, email):
        return self.dbpool.runQuery("select email from ho_users where\
                email = '%s'"%(email))
    
    def getUsernameAndPasswordViaEmail(self, email):
        return self.dbpool.runQuery("select username, password from ho_users\
                where email = '%s'"%(email))
    
    def insertUser(self, username, device_id, attributes):
        self.dbpool.runOperation("insert into ho_users set username = %s, \
                device_id = %s, attributes = %s",(username,
                                                       device_id,
                                                       attributes))
        
    def insertScore(self, quest, username, fbid, score):
        self.dbpool.runOperation("insert into hiscore set quest = %s, \
                user = %s, fbid = %s, score = %s",\
                (quest, username, fbid, score))
    
    """
    mod
    1 = day
    2 = week
    3 = alltime
    """
    def getHiscore(self, quest, mod):
        d = defer.Deferred()
        
        def cbResult(result):
            
            if len(result) == 0 or result == "None":
                d.errback()
                return d
            else:
                d.callback(result)
                return d
        
        if mod == 1:
            print "select user, score, fbid from hiscore\
              where quest = %s and tstamp = curdate()\
              order by score desc limit 20"%(quest)
            return self.dbpool.runQuery("select user, score, fbid from hiscore\
              where quest = %s and date(tstamp) = curdate()\
              order by score desc limit 20",(quest)).addCallback(cbResult)
            
        if mod == 2:
            return self.dbpool.runQuery("select user, score, fbid from hiscore\
              where quest = %s and week(date(tstamp)) = week(curdate() \
              order by score desc limit 20",(quest)).addCallback(cbResult)
        
        if mod == 3:
            return self.dbpool.runQuery("select user, score, fbid from hiscore\
              where quest = %s order by score desc limit 20",\
              (quest)).addCallback(cbResult)
            
    def getRealm(self):
        for world in self.worlds.values():
            print world.name,":", world.desc
            for street in world.streets.values():
                print "\t",street.name,":", street.desc
                for room in street.rooms.values():
                    print "\t\t",room.name,":", room.desc
    
    def initializeWorlds(self):
        worlds = {}
        for world_ in self.worldConf.sections():
            worlds[world_]=World(world_,\
                                 self.worldConf.get(world_, "description"),\
                                 self)
        return worlds
    
    def generateWorldList(self):
        v = {}
        for x in self.worlds.keys():
            v[x]=self.worlds[x].desc
        return v
"""    
    def start(self):
        reactor.listenUDP(8005, self.UDP)
        reactor.run()

    def idGen(self):
        self.id += 1
        return self.id
    
        
# this only runs if the module was *not* imported
if __name__ == '__main__':
    print gethostname()
    v = HeroMain()
    v.start()
"""
