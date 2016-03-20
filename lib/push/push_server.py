from twisted.spread import pb
from twisted.internet import reactor
from twisted.web.server import Site, Request, NOT_DONE_YET
from twisted.web.static import File
from twisted.web.resource import ErrorPage, NoResource, Resource,\
getChildForRequest 
from twisted.internet.task import LoopingCall
import time
import shelve

class LocalReference(pb.Referenceable):
    """
      Reference sent to clients as dial-back
    """
    def __init__(self, name, peer, web_service):
        self.name = name
        self.peer = peer
        self.web_service = web_service

    def __str__(self):
        return self.name
    
    def remote_test(self, name):
        print name
        return name
    
    def remote_getMessages(self, username):
        ret = self.web_service.getMessages(username)
        print username, ret
        return ret
    
class PBBroker(pb.Root):
    """
      Root reference to invoke initialisation on
    """
    local_ref = LocalReference
    
    def __init__(self, web_service, factory):
        self.web_service = web_service
        self.factory = factory
    
    def remote_init(self, name, peer):
        ref = self.local_ref(name, peer, self.web_service)
        self.factory.clientRef[name] = peer
        peer.callRemote("ping")
        return ref

class PBServerFactory(pb.PBServerFactory):
    broker = PBBroker
    def __init__(self, web_service):
        self.web_service = web_service
        self.clientRef = {}
        pb.PBServerFactory.__init__(self, self.broker(web_service,self))  

    def start(self, pbport, webport):
        reactor.listenTCP(webport, Site(self.web_service))
        reactor.listenTCP(pbport, self)

class AddMessage(Resource):
    def __init__(self, main):
        Resource.__init__(self)
        self.main = main
    
    def render_POST(self, request):
        try:
            desc = request.args["d"][0]
            type = request.args["t"][0]
            qcode = request.args["q"][0]
            message = request.args["m"][0]
            d_start = time.mktime(time.strptime(request.args["ds"][0],\
                                                "%d-%m-%Y %H:%M:%S"))
            d_end = time.mktime(time.strptime(request.args["de"][0],\
                                              "%d-%m-%Y %H:%M:%S"))
            print type, desc, qcode, message, d_start, d_end
            self.main.addMessage(desc,qcode,type,message,d_start,d_end)
            request.render(getChildForRequest(Index(self.main), request))
            return NOT_DONE_YET
        except:
            return "erorr"

class RemoveMessage(Resource):
    def __init__(self, main):
        Resource.__init__(self)
        self.main = main
    
    def render_GET(self, request):
        try:
            index = request.args["code"][0]
            self.main.removeMessage(index)
            request.render(getChildForRequest(Index(self.main), request))
            return NOT_DONE_YET
        except:
            return "Error"
    
class Index(Resource):
    def __init__(self, main):
        Resource.__init__(self)
        self.main = main
    
    def render(self, request):
        ret='<script language="javascript" type="text/javascript"\
            src="res/datetimepicker.js"></script>'
        ret+='<form action="/add" method="post">\
            <p>\
            Message Description: <input type="text" name="d" value=""/>\
            </p>\
            Quest Code: <input type="text" name="q" value=""/>\
            </p>\
            <p>Message Type<br />\
            <input type="radio" name="t" value="quest" checked = "checked" />\
            Quest<br />\
            <input type="radio" name="t" value="news"  /> News<br />\
            </p>\
            <p>\
            Message:<br />\
            <textarea name="m" rows="5" cols="40"></textarea>\
            <p>\
            <p>\
            Date Start:<br />\
            <input id="ds" name="ds" type="text" size="25">\
            <a href="javascript:NewCal(\'ds\',\'ddmmyyyy\',true,24)">\
            <img src="res/cal.gif" width="16" height="16" border="0"\
            alt="Pick a date"></a>\
            </p>\
            <p>\
            Date End:<br />\
            <input id="de" name="de" type="text" size="25">\
            <a href="javascript:NewCal(\'de\',\'ddmmyyyy\',true,24)">\
            <img src="res/cal.gif" width="16" height="16" border="0"\
            alt="Pick a date"></a>\
            </p>\
            <p><input type="submit" value="Submit" /></p>\
            </form>'


        ret+="<table border=1 cellpadding=10>\
                <tr>\
                    <td>Message Code</td>\
                    <td>Message Description</td>\
                    <td>Quest Code</td>\
                    <td>Message Type</td>\
                    <td>Message</td>\
                    <td>Date Start</td>\
                    <td>Date End</td>\
                    <td>Status</td>\
                 </tr>"
        ret+="<tr>"
        for i,d,q,t,m,ds,de in self.main.shelf["messages"]:
            ret+="<td>%s</td>"%i
            ret+="<td>%s</td>"%d
            ret+="<td>%s</td>"%q
            ret+="<td>%s</td>"%t
            ret+="<td>%s</td>"%m
            ret+="<td>%s</td>"%time.localtime(ds)
            ret+="<td>%s</td>"%time.localtime(de)
            if time.time() >= ds and time.time() < de:
                ret+="<td>Running</td>"
            elif time.time() >= de:
                ret+="<td>Done</td>"
            else:
                ret+="<td>Waiting</td>"
            ret+="<td><a href=del?code=%s>Delete</a></td>"%i
            ret+="</tr>"
            
        return ret
    
        
class PushAdmin(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.putChild("res", File("./"))
        self.putChild("add", AddMessage(self))
        self.putChild("del", RemoveMessage(self))
        self.putChild("/", self)
        self.isLeaf = False
        self.shelf = shelve.open("data.bjf", writeback=True)
        if self.shelf == {}:
            self.shelf["index"]=0
            self.shelf["messages"]=list()
            self.shelf["exceptions"]={}
        self.index = self.shelf["index"]
        
    def nextIndex(self):
        ret = self.index 
        self.index += 1
        self.shelf["index"] = self.index
        self.shelf.sync()
        return self.index
        
    def addMessage(self, desc, q, type, message,ds,de):
        index = str(self.nextIndex())
        print self.shelf
        print self.shelf["messages"]
        self.shelf["messages"].append((index, desc, q, type, message, ds, de))
        self.shelf["exceptions"][index]=[]
        self.shelf.sync()

    def getMessages(self, username):
        result = []
        for (i, d, q, t, m, ds, de) in self.shelf["messages"]:
            if time.time() >= ds and time.time() < de:
                if not username in self.shelf["exceptions"][i]:
                    result.append((t, q, m))
                    self.shelf["exceptions"][i].append(username)
        if result == []:
            return None
        else: return result
    
    def removeMessage(self, index):
        for i,d,q,t,m,ds,de in self.shelf["messages"]:
            print index, type(index), i, type(i)
            if index == i:
                self.shelf["messages"].remove((i,d,q,t,m,ds,de))
        self.shelf["exceptions"].pop(index)
        self.shelf.sync()
    
    def getChild(self, path, request):

        print path, "test"
        return Index(self)
    
webport = 8989
g = PBServerFactory(PushAdmin())
g.start(7777, webport)
reactor.run()
