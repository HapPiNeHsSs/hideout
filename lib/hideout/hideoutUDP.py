from twisted.internet.protocol import DatagramProtocol
from character import Character
from twisted.python.log import msg
import json, sys
from base64 import b64decode

class HideoutUDP(DatagramProtocol):
    
    def __init__(self, main):
        
        self.main = main
        self.jdec = json.JSONDecoder()
        self.jenc = json.JSONEncoder()
        #self.factory.main = HeroMain
        self.id = 0
        self.handlers = {"connect":self.connectionMade,
                         "create":self.create}
        

    def reply(self, data, address):
        msg ("sending %s"%data)
        self.transport.write(data, address)

    def datagramReceived(self, data, address):
        msg ("received %s"%data)
        try:
            mes = self.jdec.raw_decode(data)
        except:
            msg ("Fail: Not JSON, Dumping %s"%data)
            return
        mes=mes[0]
        if type(mes).__name__ != "dict":
            msg ("Fail: Not the Right Format, Dumping %s"%data)
            return
        for handler, data in mes.items():
            if handler in self.handlers:
                self.handlers[handler](data, address)
            else: self.relay(mes, data['from'])
        # The uniqueID check is to ensure we only service requests from
        # ourselves
        """
        if datagram == 'UniqueID':
            print "Server Received:" + repr(datagram)
            self.transport.write("data", address)
        """   
    def relay(self, data, _from):
        #print ">>>relay", data
        msg("Pushing Request to %s's handler: %s"%(_from, data))
        self.main.players[_from].onRelay(data)
        """
        try:
            self.main.players[_from].onRelay(data)
        except Exception, e:
            print Exception
            msg("Not Connected, Dumping")
        """
    def connectionMade(self, data, address):
        def cbOnResult(result):
            print "res", result
            if type(result).__name__ in ["str","unicode"]:
                name = result
                msg ("%s has connected"%name)
                #try to remove a duplicate user
                try:
                    self.main.players[name].connectionLost({"from":name})
                    msg("Found Duplicate, Disconnecting Duplicate Player: %s"\
                        %name)
                except: msg("No Duplicates Found")
                
                char = Character(name, address, self, self.main)
                self.main.addPlayer(name, char)
                dat = {"connect":name}
                self.reply(json.dumps(dat), address)     
                char.sendOffline()
            elif result == -1:
                dat = {"connect":{"error":"not a user"}}
                self.reply(json.dumps(dat), address)
            elif result == -2:
                dat = {"connect":{"error":"MySQL Error"}}
                self.reply(json.dumps(dat), address)
                
        def ebOnError(result):
            print result, ">>>"
            dat = {"connect":{"error":"Unknown Error"}}
            self.reply(json.dumps(dat), address)
        
        data = b64decode(data)
        self.main.authenticate(data).\
            addCallback(cbOnResult).addErrback(ebOnError)
        
    def create(self, data, address):
        def cbOnResult(result):
            print result, type(result).__name__
            if type(result).__name__ in ["str","unicode"]:
                dat = {"create":{"error":"username already registered"}}
                self.reply(json.dumps(dat), address)
            elif result == -1:
                def cbOnResultDID(result):
                    if type(result).__name__ in ["str","unicode"]:
                         dat = {"create":{"error":"dev_id already registered"}}
                         self.reply(json.dumps(dat), address)
                         
                    elif result == -1:
                        self.main.insertUser(data["username"],
                                             data["device_id"],
                                             json.dumps(data["attributes"]))
                        dat = {"create":"succress"}
                        self.reply(json.dumps(dat), address)
                        
                    elif result == -2:
                        dat = {"create":{"error":"MySQL Error"}}
                        self.reply(json.dumps(dat), address)
                    
                def ebOnErrorDID(result):
                    print result
                    dat = {"connect":{"error":"Unknown Error"}}
                    self.reply(json.dumps(dat), address)
                
                self.main.authenticate(data["device_id"]).\
                    addCallback(cbOnResultDID).addErrback(ebOnErrorDID)

            elif result == -2:
                dat = {"create":{"error":"MySQL Error"}}
                self.reply(json.dumps(dat), address)
                
        def ebOnError(result):
            print result
            dat = {"connect":{"error":"Unknown Error"}}
            self.reply(json.dumps(dat), address)
        
        if data.has_key("username") and data.has_key("device_id")\
        and data.has_key("attributes") and len(data.keys())==3:
            self.main.checkUser(data["username"]).\
                addCallback(cbOnResult).addErrback(ebOnError)
        
