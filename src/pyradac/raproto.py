#!/usr/bin/python

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

from twisted.internet import protocol, reactor
from pushclient import PushClientFactory
from pushserver import PushServerProtocol
import sys
import os
import time

# p2p-dprd stuff
import p2pdprd

# Convenience functions
def showConnected():
    print
    print len(serverFactory.clients),"connected clients:"
    print "------------------"
    print "host\t\tstate\tid"
    for c in serverFactory.clients:
        print "%s:%s\t%s\t%s" % (c.peer.host, c.peer.port, c.state, c.identifier)
    print 

def showConfigs():
    print
    print len(serverFactory.configs),"known configurations:"
    print "---------------------"
    print "host\t\tid\ttimestamp\tconfig"
    for k,v in serverFactory.configs.iteritems():
        print "%s:%s\t%s\t%s\t%s" % (v["src"].host, v["src"].port, k, v["timestamp"], v["config"])
    print 

def showCandidateNodes():
    print
    print len(pushClientFactory.clients),"connected candidate nodes:"
    print "---------------------"
    print "host\t\tconnected"
    for c in pushClientFactory.clients:
        print "%s:%s\t%s" % (c.peer.host, c.peer.port, c.state)
    print

# Get and parse opts
from twisted.python import usage
#from twisted.internet.address import IPv4Address
class RAOptions(usage.Options):
    optParameters = [
                ['listen','l',1025,'listen port', int],
                ['interface','if','','only bind to this interface'],
                ['config','c',None,'set configuration to push'],                
                ['control_port','cp', 1111, 'control port to listen to on localhost', int],
                ['lat',None,100.0,'latitude',float],
                ['lon',None,100.0,'longitude',float],
                ['cr',None,50,'coordination range',int],
                ['p2p','p',None,'path to p2p socket', str],
                ['remote_radio_host',None,None,'ip to remote radio device/router. "iw" and "uci" commands will be executed on this device via ssh. Requires paramiko library.', str],
                ['remote_radio_user',None,None,'username on remote radio device (ssh)', str],
                ['remote_radio_password',None,None,'password to remote radio device (ssh)',str],
                ['radio_device_num',0,None,'default radio device by number (e.g. wlan0/radio0 = 0)',int],
                ['has_radio',None,0,'set to 1 to enable radio',int],
                ['radio_type',None,"debian", "Radio type - openwrt or debian",str]
            ]

options = RAOptions()
if len(sys.argv) > 1:
    options.parseOptions(sys.argv[1:])
else:
    options.parseOptions(["--help"])

###############
# Push server
###############
serverFactory = protocol.ServerFactory()
serverFactory.protocol = PushServerProtocol
serverFactory.identifier = None
serverFactory.clients = []
serverFactory.configs = {} # {identifier : { config: ?, timestamp: ?}}
serverFactory.callbackConnectedChanged = showConnected
serverFactory.callbackConfigsChanged = showConfigs

reactor.listenTCP(options['listen'], serverFactory, interface=options['interface'])
print "Listening on TCP port",options['listen'],'on interface',options['interface']

###############
# Push client
###############
pushClientFactory = PushClientFactory()
pushClientFactory.identifier = None
pushClientFactory.config = options['config']
pushClientFactory.callbackCandidateNodesUpdated = showCandidateNodes

##########
# P2P-DPRD
##########
p2pdprd_listening_sock = options['p2p'].strip()
my_listening_sock = "/tmp/radac-" + str(os.getpid()) + ".sock"
our_node_description = None

# Delete the p2p-dprd unix socket path if it already exists
if os.path.exists(my_listening_sock): 
    os.remove(my_listening_sock)

# Listen to responses from p2pdprd
def candidateNodesCallback(nodecollection):
    sys.stdout.write( "Received data from P2PDPRD via IPC\n" )
    if len(nodecollection.nodes) > 0:
        our_node_description = nodecollection.nodes[0]
        sys.stdout.write("Own node description received from p2pdprd: %s\n" % our_node_description)

        serverFactory.identifier = our_node_description.node_id
        pushClientFactory.identifier = our_node_description.node_id
        ipcServerFactory.identifier = our_node_description.node_id

        if len(nodecollection.nodes) > 1 and pushClientFactory != None:
            pushClientFactory.replaceCandidateNodes(nodecollection.nodes[1:]) # skip ourselves (first entry)

p2pdprd_ipc = p2pdprd.IPCProtocol(p2pdprd_listening_sock, my_listening_sock, candidateNodesCallback)
reactor.listenUNIXDatagram(my_listening_sock, p2pdprd_ipc) 
p2pdprd_ipc.setCoordinationRange(options['cr'])
p2pdprd_ipc.setLocation(options['lat'], options['lon'])


###########
# Local IPC
###########
from ipcserver import IPCServerProtocol
from openwrttoolbox import Radio
ipcServerFactory = protocol.ServerFactory()
ipcServerFactory.protocol = IPCServerProtocol
ipcServerFactory.starttime = time.time()
ipcServerFactory.server = serverFactory
ipcServerFactory.client = pushClientFactory
ipcServerFactory.p2pdprd = p2pdprd_ipc # Send p2pdprd_ipc in here
ipcServerFactory.cr = options['cr']
ipcServerFactory.loc = (options['lat'], options['lon'])
ipcServerFactory.identifier = None
ipcServerFactory.clients = []

if options['has_radio'] > 0:
    if options['remote_radio_host'] != None: # execute radio commands remotely
        print "Attempting to connect to remote radio number %s at %s@%s" % (options['radio_device_num'], options['remote_radio_user'], options['remote_radio_host'])
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(options['remote_radio_host'], username=options['remote_radio_user'], password=options['remote_radio_password'])
        ipcServerFactory.radio = Radio(devid=options['radio_device_num'], sshclient = ssh)
    else:
        print "Using local radio on device number",options['radio_device_num']
        ipcServerFactory.radio = Radio(devid=options['radio_device_num'], sshclient=None)
    print "Radio summary:", ipcServerFactory.radio.get_summary()
else:
    print "Radio DISABLED"
    ipcServerFactory.radio = None


print "Listening on control port",options['control_port'],"on localhost"
reactor.listenTCP(options['control_port'], ipcServerFactory, interface='localhost')

# Run:

reactor.run()
