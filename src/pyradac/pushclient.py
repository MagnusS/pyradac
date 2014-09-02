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
from twisted.internet.protocol import ClientFactory

class PushClientProtocol(basic.LineReceiver):

    def __init__(self, ident, conf):
        self.identifier = str(ident)
        self.state = "DISCONNECTED"
        self.peer = None
        # states: DISCONNECTED -> CONNECTED -> ID_SENT -> READY -> CONFIG_SENT -> READY
        # ID is always ok when READY

    def sendIdentifier(self):
        if (self.state == "CONNECTED"):
            self.sendLine("IAM " + self.identifier)
            self.state = "ID_SENT"
        else:
            print "Attempt to send identifier when not in CONNECTED state. State is",self.state

    def isReady(self):
        return (self.state == "READY")

    def sendConfig(self):
        if (self.factory.config == None):
            print "sendConfig failed. Config not set in factory"
            return
            
        if (self.state == "READY"):
            self.state = "CONFIG_SENT"
            self.sendLine("PUSH " + self.factory.config)
        else:
            print "Attempt to send config when not in READY state. State is",self.state

    def connectionMade(self):
        print "Connected to candidate node",self.transport.getPeer()
        self.state = "CONNECTED"
        self.peer = self.transport.getPeer()
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        print "Connection lost to candidate node",self.transport.getPeer(),":",reason
        self.state = "DISCONNECTED"
        try:
            self.factory.clients.remove(self)
        except:
            pass
        if self.factory.callbackCandidateNodesUpdated != None:
            reactor.callLater(0, self.factory.callbackCandidateNodesUpdated)

    def lineReceived(self, line):
        #print "client received",line
        if (line != None and line.strip() != ""):
            args = line.strip().split(" ")
            retcode = args[0] 
            if (retcode == "200"): # perform state transition 
                if (self.state == "CONNECTED"):
                    self.sendIdentifier()
                    return

                if (self.state == "CONFIG_SENT"):
                    self.state = "READY"                
                    if self.factory.callbackCandidateNodesUpdated != None:
                        reactor.callLater(0, self.factory.callbackCandidateNodesUpdated)
                    return

                if (self.state == "ID_SENT"):
                    print "Ready to PUSH config to %s:%s" % (self.peer.host, self.peer.port)
                    self.state = "READY"
                    if (self.factory.config != None):
                        self.sendConfig()
                    else:
                        if self.factory.callbackCandidateNodesUpdated != None:
                            reactor.callLater(0, self.factory.callbackCandidateNodesUpdated)
                    return
                # if we get here, there was an error (unknown state)
                print "Server said",line
                print "Unknown state transition. Current state is",self.state
                return
            else:
                print "Error. Server said",line

class PushClientFactory(ClientFactory):
    def __init__(self, ident=None):
        self.identifier = ident
        self.clients = [] # connected clients
        self.config = None
        self.candidateNodes = [] # all clients, also disconnected
        self.callbackCandidateNodesUpdated = None

    def startedConnecting(self, connector):
        print "Attempting to connect to %s:%s" % (connector.host, connector.port)

    def buildProtocol(self, addr):
        if self.identifier != None:
            print "Connected to candidate node %s:%s" % (addr.host, addr.port)
            proto = PushClientProtocol(self.identifier, self.config)
            proto.factory = self
            return proto
        else:
            print "Not connecting to %s:%s because identifier is None" % (addr.host, addr.port)
            return None
    
    def hasCandidateNode(self, host, port, identifier=None):
        for f in self.candidateNodes:
            if (f[1].host == host and f[1].port == port):
                if (identifier != None):
                    return f[0] == identifier
                else:
                    return True
        return False

    def isConnectedTo(self, host, port, identifier=None):
        for f in self.clients:
            if (f.peer.host == host and f.peer.port == port):
                if (identifier != None):
                    return f.peer.identifier == identifier
                else:
                    return True
        return False

    def clientConnectionLost(self, connector, reason):
        print "Connection lost for %s:%s because %s" % (connector.host, connector.port, reason)
        self.removeCandidateNode(connector.host, connector.port)

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed for %s:%s because %s" % (connector.host, connector.port, reason)
        self.removeCandidateNode(connector.host, connector.port)

    def pushConfig(self, config):
        print "Pushing new configuration to all connected candidate nodes."
        self.config = config
        for c in self.clients:
            if (c.isReady()):
                print "PUSH config to %s:%s" % (c.peer.host, c.peer.port)
                c.sendConfig()
            else:
                print "PUSH not sent to %s:%s, state was %s" % (c.peer.host, c.peer.port, c.state)

    def replaceCandidateNodes(self, nodes):
        """ This function expects a dict containing p2pdprd.Node classes as input. """

        # remove old nodes first
        for n in self.candidateNodes:
            found = False
            for i in range(0,len(nodes)):
                (radac_ip, radac_port) = nodes[i].radac_address
                if radac_ip == n[1].host and radac_port == n[1].port:
                    found = True
                    break
            if not found:
                self.removeCandidateNode(n[1].host, n[1].port)
                print "Removed old node %s:%s with id %s" % (n[1].host, n[1].port, n[0])
        # add new nodes
        for i in range(0,len(nodes)):
            (radac_ip, radac_port) = nodes[i].radac_address
            if self.addCandidateNode(radac_ip, radac_port, nodes[i].node_id):
                print "Added new node %s:%s with id %s" % (radac_ip, radac_port, nodes[i].node_id)

    def addCandidateNode(self, host, port, identifier=None):
        # add candidate node to factory and store connectTCP result, but not if host already exsts
        if (not self.hasCandidateNode(host, port)):
            self.candidateNodes.append((identifier, reactor.connectTCP(host,port,self)))
            return True
        else:
            return False

    def removeCandidateNode(self, host, port):
        for f in self.clients: # disconnect if connected
            if (f.peer.host == host and f.peer.port == port):
                f.transport.loseConnection()
                try:
                    self.clients.remove(f)
                except:
                    pass
        for cn in self.candidateNodes: # remove from candidate nodes
            if (cn[1].host == host and cn[1].port == port):
                cn[1].disconnect()
                try:
                    self.candidateNodes.remove(cn)
                except:
                    print "WARNING: Unable to remove node from candidate nodes:",cn
                    pass


