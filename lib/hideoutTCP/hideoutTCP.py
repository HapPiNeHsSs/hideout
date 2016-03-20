from twisted.protocols import basic
from character import Character
from twisted.python.log import msg
from twisted.internet import reactor, protocol
import json, sys, urllib
from base64 import b64decode

class HeroFactory(protocol.ServerFactory):
    def __init__(self, main):
        self.main = main

class HideoutTCP(basic.LineReceiver):
    main = None
        
    def __init__(self):
        self.setRawMode()
        self.jdec = json.JSONDecoder()
        self.jenc = json.JSONEncoder()
        self.id = 0
        self.handlers = {"connect":self.connect,
                         "create":self.create}
        self.charClass = ""
    
    def connectionMade(self):
        self.main = self.factory.main
        print "connect"
        
    def connectionLost(self, args): 
        print "DC", args
        try:
            self.charClass.stop()
        except:
            pass

    """
    def reply(self, data, address):
        msg ("sending %s"%data)
        self.transport.write(data, address)
    """
    
    def reply(self, dat):
        print "sending", dat
        self.sendLine(dat)
    
    def rawDataReceived(self, data):
        splits = str(data).split("\n")
        for x in splits:
            self.process(urllib.unquote(x))
        
    def process(self, data):
        msg ("received %s"%data)
        str(data)
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
                self.handlers[handler](data)
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
    def connect(self, data):
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
                
                self.charClass = Character(name, self, self.main, data_dec)
                self.main.addPlayer(name, self.charClass)
                dat = {"connect":name}
                self.reply(json.dumps(dat))     
                self.charClass.sendOffline()
            elif result == -1:
                dat = {"connect":{"error":"not a user"}}
                self.reply(json.dumps(dat))
            elif result == -2:
                dat = {"connect":{"error":"MySQL Error"}}
                self.reply(json.dumps(dat))
                
        def ebOnError(result):
            print result, ">>>"
            dat = {"connect":{"error":"Unknown Error"}}
            self.reply(json.dumps(dat))
        
        data_dec = b64decode(data)
        self.main.authenticate(data_dec).\
            addCallback(cbOnResult).addErrback(ebOnError)
        
    def create(self, data):
        def cbOnResult(result):
            print result, type(result).__name__
            if type(result).__name__ in ["str","unicode"]:
                dat = {"create":{"error":"username already registered"}}
                self.reply(json.dumps(dat))
            elif result == -1:
                def cbOnResultDID(result):
                    if type(result).__name__ in ["str","unicode"]:
                         dat = {"create":{"error":"dev_id already registered"}}
                         self.reply(json.dumps(dat))
                         
                    elif result == -1:
                        self.main.insertUser(data["username"],
                                             data["device_id"],
                                             json.dumps(data["attributes"]))
                        dat = {"create":"success"}
                        self.reply(json.dumps(dat))
                        
                    elif result == -2:
                        dat = {"create":{"error":"MySQL Error"}}
                        self.reply(json.dumps(dat))
                    
                def ebOnErrorDID(result):
                    print result
                    dat = {"connect":{"error":"Unknown Error"}}
                    self.reply(json.dumps(dat))
                
                self.main.authenticate(data["device_id"]).\
                    addCallback(cbOnResultDID).addErrback(ebOnErrorDID)

            elif result == -2:
                dat = {"create":{"error":"MySQL Error"}}
                self.reply(json.dumps(dat))
                
        def ebOnError(result):
            print result
            dat = {"connect":{"error":"Unknown Error"}}
            self.reply(json.dumps(dat))
        
        if data.has_key("username") and data.has_key("device_id")\
        and data.has_key("attributes") and len(data.keys())==3:
            self.main.checkUser(data["username"]).\
                addCallback(cbOnResult).addErrback(ebOnError)
        
