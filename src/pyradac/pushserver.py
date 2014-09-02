'''
Copyright (c) 2013-2014, Magnus Skjegstad (magnus@skjegstad.com) / FFI
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, 
this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
POSSIBILITY OF SUCH DAMAGE.
'''

from twisted.protocols import basic
from twisted.internet import reactor
import time

class PushServerProtocol(basic.LineReceiver):
    def __init__(self):
        self.state = "NOID"
        self.identifier = "Unknown"
        self.config = None
        self.peer = None

    def connectionMade(self):
        print "New connection from",self.transport.getPeer()

        if self.factory.identifier == None: # if our own identifier is unknown, abort and hope it is set later...
            self.transport.loseConnection()
            return 

        self.factory.clients.append(self)
        self.peer = self.transport.getPeer()
        self.sendLine("200 Welcome to " + str(self.factory.identifier) + ". Go ahead.")

    def connectionLost(self, reason):
        #print "Connection lost"
        try:
            self.factory.clients.remove(self)
        except:
            pass

    def lineReceived(self, line):
        #print "Received line",repr(line),"from",self.transport.getPeer()
        if (line != None and line.strip() != ""):
            args = line.strip().split(" ", 1)
            if (args == None or len(args) < 1):
                self.sendLine("400 Missing command. See HELP.")
                return
            command = args[0].upper()
            if (len(args) > 1):
                params = args[1]
            else:
                params = None

            if (command == "HELP"):
                self.sendLine("Available commands:"+'\n'+
                                     "--------------------------" + '\n' +
                                     "IAM [id]" + '\n' +
                                     "PUSH [config]" + '\n' + 
                                     "LIST" + '\n' + 
                                     "HELP" + '\n' +
                                     "QUIT" + '\n')
                return

            if (command == "QUIT"):
                print "Client",self.transport.getPeer(),"with id",self.identifier,"disconnected."
                self.transport.loseConnection()
                if (self.factory.callbackConnectedChanged != None):
                    reactor.callLater(1,self.factory.callbackConnectedChanged)
                return

            if (command == "IAM" and params != None):
                if (self.state == "IDOK"):
                    self.sendLine("500 Already identified.")
                    return

                self.state = "IDOK"
                self.identifier = params
                self.sendLine("200 Hello " + params)
                #print "Client",self.transport.getPeer(),"identified as ",params
                if (self.factory.callbackConnectedChanged != None):
                    reactor.callLater(1,self.factory.callbackConnectedChanged)
                return

            # if we get here without ID, show error
            if (self.state == "NOID"):
                self.sendLine("400 Identify with IAM. See HELP.")
                return

            if (command == "LIST"): # this is a debug command
                print "Client",self.transport.getPeer(),"request LIST"
                for c in self.factory.clients:
                    self.sendLine(str(c.peer) + '\t' + c.state + '\t' + c.identifier)
                return
        
            if (command == "PUSH" and params != None):
                #print "Client",self.transport.getPeer(),"id",self.identifier,"pushed",params
                self.sendLine("200 Configuration received.")
                self.config = params
                epochutc = int(time.time())
                self.factory.configs[str(self.identifier)] = {"config" : params, "timestamp": epochutc, "src" : self.peer}
                if (self.factory.callbackConfigsChanged != None):
                    reactor.callLater(0, self.factory.callbackConfigsChanged)
                return

            # if we get here it is an error
            self.sendLine("400 Invalid command. See HELP.")

