#! /usr/bin/python

"""FUDS WEB application."""

import sys
sys.path.append("../")

import memcache
from lib.hideoutTCP.hideout import HeroMain
from lib.hideoutTCP.hideoutTCP import HideoutTCP, HeroFactory
from lib.push.push_client import pushClient
from lib.apn.apn_client import apnClient
import time
from ConfigParser import ConfigParser
from twisted.internet import protocol
from twisted.enterprise import adbapi
from twisted.application import service
from twisted.application.internet import TCPServer, TCPClient
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile

#Read Config File
config = ConfigParser()
config.read("../etc/hideout.conf")

#Read Worlds Fike
worldConf = ConfigParser()
worldConf.read("../etc/worlds.conf")

#Instantiate DB pool
dbpool = adbapi.ConnectionPool("MySQLdb",\
                                user=config.get("db", "user"),\
                                passwd=config.get("db", "passwd"),\
                                host=config.get("db", "host"),\
                                db=config.get("db", "dbname"))



devid_cache = memcache.Client(["%s:%s"%(config.get("static",\
                                                   "devid_memcache_ip"),\
                                     config.getint("static",\
                                                   "devid_memcache_port"))])

message_cache = memcache.Client(["%s:%s"%(config.get("static",\
                                                     "message_memcache_ip"),\
                                     config.getint("static",\
                                                   "message_memcache_port"))])

push = pushClient("test","test")
#push.connect("127.0.0.1",7777)
apn = pushClient("APN","APN")
apn.connect("127.0.0.1",4545)

ho_factory = HeroFactory(HeroMain(worldConf,\
                             dbpool,\
                             devid_cache,\
                             message_cache,\
                             push, apn))
ho_factory.protocol = HideoutTCP
tcp_service = TCPServer(config.getint("static", "port"), ho_factory)



#Create Application Instance
application = service.Application(config.get("static", "sname"))

#Attach Site Roots to Application
tcp_service.setServiceParent(application)

#Instantiate Log File
logfile = DailyLogFile(config.get("logging", "logfile"),\
                       config.get("logging", "logdir"))

#Set Logger to application
application.setComponent(ILogObserver, 
                         FileLogObserver(logfile).emit)

#run this by twistd -y <name.tac>
