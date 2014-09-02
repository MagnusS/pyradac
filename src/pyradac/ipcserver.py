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
import time

class IPCServerProtocol(basic.LineReceiver):

    # 200 are ok messages
    REPLY_BANNER = 211
    REPLY_HELP = 214
    REPLY_READY = 200
    REPLY_DISCONNECTING = 221
    REPLY_COMMAND_OUTPUT = 201

    # 500 are server errors
    REPLY_BUSY = 500
    # 400 are parsing/command errors
    REPLY_INVALID_COMMAND = 400
    REPLY_INVALID_PARAMETER = 401

    def connectionMade(self):
        """ Triggered when new connections are made to the IPC server """
        print "IPC: New connection from",self.transport.getPeer()

        if (len(self.factory.clients) >= 1):
            self.output(self.REPLY_BUSY, " Too many connections. Aborting.")
            self.transport.loseConnection()
            print "IPC: Too many connections. Disconnecting..."
            return

        self.factory.clients.append(self)
        self.peer = self.transport.getPeer()
        self.output(self.REPLY_BANNER,"RADAC IPC server")
        self.lastcommand = None
        self.lastparams = None
        self.sayReady()

    def connectionLost(self, reason):
        """ Triggered the connection to the client is lost """
        print "IPC: Connection lost"
        try:
            self.factory.clients.remove(self)
        except:
            pass

    def output(self,code,msg):
        """ Generic method for sending text to the client. Code is an int representing the message type being displayed (see predefined REPLY_* constants) """
        self.sendLine("%s %s" % (code, msg))

    def sayReady(self):
        """ Notify the client that the output is complete by sending a reply prefixed by the REPLY_READY code """
        self.output(self.REPLY_READY, "Ready.")

    def lineReceived(self, line):
        """ Triggered when a new line is received from the client. """
        #print "Received line",repr(line),"from",self.transport.getPeer()
        if (line != None and line.strip() != ""):
            args = line.strip().split(" ", 1)
            if (args == None or len(args) < 1):
                self.output(self.REPLY_INVALID_COMMAND +" Missing command. See HELP.")
                return
            command = args[0].upper()
            if (len(args) > 1):
                params = args[1]
            else:
                params = None

            if (command == "."):
                params = self.lastparams
                command = self.lastcommand
            else:
                self.lastparams = params
                self.lastcommand = command

            if (command == "HELP"):
                self.output(self.REPLY_HELP,"Available commands:")
                self.output(self.REPLY_HELP,"--------------------------" )
                self.output(self.REPLY_HELP,"STATUS\t\t\t\tShow pyradac status")
                self.output(self.REPLY_HELP,"LOC [lat] [lon]\t\t\tSet location (float)")
                self.output(self.REPLY_HELP,"CR [coordination range]\t\tSet coordination range (unsigned int)")
                self.output(self.REPLY_HELP,"CONFIG [config]\t\t\tSet current configuration (string, use base64 for binary)")
                self.output(self.REPLY_HELP,"LIST [cn|connections|configs]\tList known candidate nodes (cn), connections or configs")
                self.output(self.REPLY_HELP,"Radio commands:")
                self.output(self.REPLY_HELP," RADIO SCAN\tPerform scan for other networks (AP goes down for 200ms)")
                self.output(self.REPLY_HELP," RADIO SHOW\tShow configuration summary (channel, tx etc)")
                self.output(self.REPLY_HELP," RADIO SHOW STATIONS\tShow list of connected stations")
                self.output(self.REPLY_HELP," RADIO SHOW FER\tShow list list of stations with frame error rate from Minstrel only")
                self.output(self.REPLY_HELP," RADIO SET {channel} {tx power}\tSet new channel and tx power. -1 = keep current value. ")
                self.output(self.REPLY_HELP,".\t\t\t\t\tRepeat last command.")
                self.output(self.REPLY_HELP,"HELP\t\t\t\tThis text")
                self.output(self.REPLY_HELP,"QUIT\t\t\t\tDisconnect")
                self.sayReady()
                return

            if (command == "QUIT"):
                print "IPC: Client",self.transport.getPeer()," disconnected (QUIT)"
                self.output(self.REPLY_DISCONNECTING, "Disconnecting")
                self.transport.loseConnection()
                return

            if (command == "CR" and params != None):
                try:
                    self.factory.cr = int(params)
                except:
                    self.output(self.REPLY_INVALID_COMMAND +"Invalid format.")
                    self.sayReady()
                    return

                self.factory.p2pdprd.setCoordinationRange(int(self.factory.cr))

                self.output(self.REPLY_COMMAND_OUTPUT,"Coordination range set to " + str(self.factory.cr))
                print "IPC: Client",self.transport.getPeer(),"has coordination range ",self.factory.cr
                self.sayReady()
                return

            if (command == "STATUS"):
                self.output(self.REPLY_COMMAND_OUTPUT,"Node identifier: " + str(self.factory.identifier))
                self.output(self.REPLY_COMMAND_OUTPUT,"Current location: %s %s" % (self.factory.loc[0], self.factory.loc[1]))
                self.output(self.REPLY_COMMAND_OUTPUT,"Current coordination range: " + str(self.factory.cr))
                self.output(self.REPLY_COMMAND_OUTPUT,"Uptime: %s seconds" % int(time.time() - self.factory.starttime))
                self.output(self.REPLY_COMMAND_OUTPUT,"Last update from P2PDPRD: %s" % ("%s seconds ago" % int(time.time() - self.factory.p2pdprd.updated) if self.factory.p2pdprd.updated != None else "Never"))
                try:
                    self.output(self.REPLY_COMMAND_OUTPUT,"Known candidate nodes: %s" % len(self.factory.p2pdprd.candidate_nodes.nodes))
                    self.output(self.REPLY_COMMAND_OUTPUT,"Known configurations: %s" % len(self.factory.server.configs))
                    self.output(self.REPLY_COMMAND_OUTPUT,"Incoming connections: %s" % len(self.factory.server.clients))
                    self.output(self.REPLY_COMMAND_OUTPUT,"Outgoing connections: %s" % len(self.factory.client.candidateNodes))
                except:
                    pass
                self.sayReady()
                return

            if (command == "LOC" and params != None):
                try:
                    (lat,lon) = params.split(' ')
                    self.factory.loc = [float(lat), float(lon)]
                except:
                    self.output(self.REPLY_INVALID_COMMAND,'Invalid format. See HELP.')
                    return

                self.factory.p2pdprd.setLocation(self.factory.loc[0], self.factory.loc[1])

                self.output(self.REPLY_COMMAND_OUTPUT,"Location is now " + lat + ", " + lon)

                print "IPC: Client",self.transport.getPeer(),"has location",self.factory.loc
                self.sayReady()
                return

            if (command == "RADIO"): 
                print "IPC: Client",self.transport.getPeer(),"requested RADIO"

                if self.factory.radio == None:
                    self.output(self.REPLY_INVALID_COMMAND, "Radio disabled")
                    self.sayReady()
                    return

                if (params != None):
                    params = params.strip().upper()                    
                    if params == "SHOW":
                        summary = self.factory.radio.get_summary()
                        for f in summary: 
                            self.output(self.REPLY_COMMAND_OUTPUT, "%s: %s" % (f, summary[f]))
                        self.sayReady()
                        return

                    if params == "SCAN":
                        from openwrttoolbox import WifiHelpers
                        import re

                        self.output(self.REPLY_HELP,"BSS\tSIGNAL\tCHANNEL\tFREQ\tLAST_SEEN_MS\tSSID")
                        scan_result = self.factory.radio.iw.scan()


                        # Gather data in array first

                        bss = None
                        cur_row = {}
                        rows = []
                        for line in str(scan_result).splitlines():
                            parts = line.strip().split(" ")
                            if parts[0] == "BSS":
                                bss = "".join(re.findall(r"\w\w:\w\w:\w\w:\w\w:\w\w:\w\w", parts[1]))
                                if cur_row != {}:
                                    rows.append(cur_row)
                                cur_row = {}
                                cur_row['bss'] = bss
                            else:
                                fields = line.strip().split(":")
                                #print fields
                                if fields[0] == "SSID":
                                    cur_row['ssid'] = fields[1]
                                if fields[0] == "signal":
                                    cur_row['signal'] = int(WifiHelpers.get_numbers_from_str(line)[0])
                                if fields[0] == "last seen":
                                    cur_row['last_seen'] = int(WifiHelpers.get_numbers_from_str(line)[0])
                                if fields[0] == 'freq':
                                    cur_row['freq'] = int(WifiHelpers.get_numbers_from_str(line)[0])
                                    cur_row['channel'] = WifiHelpers.freq_to_chan(cur_row['freq'])

                            #self.output(self.REPLY_COMMAND_OUTPUT, "L %s: %s" % (bss, line.strip()))

                        if cur_row != {}:
                            rows.append(cur_row)
            
                        # Output array
                        for row in rows:
                            self.output(self.REPLY_COMMAND_OUTPUT, "%s\t%s\t%s\t%s\t%s\t%s" %
                                    (row['bss'], row['signal'], row['channel'], row['freq'], row['last_seen'], row['ssid']))

                        self.sayReady()
                        return

                    if params[:4] == "SET ":
                        p = params.split(" ")
                        if len(p) != 3:
                            self.output(self.REPLY_INVALID_PARAMETER, "Invalid number of parameters. See HELP")
                            self.sayReady()
                            return

                        try:
                            chan = int(p[1])
                            tx = int(p[2])
                        except:
                            self.output(self.REPLY_INVALID_PARAMETER,"Invalid format. See HELP")
                            self.sayReady()
                            return

                        if chan < 0:
                            chan = None

                        if tx < 1:
                            tx = None
                        
                        self.factory.radio.reconfigure(chan, tx)
                        self.sayReady()
                        return

                    if params == "SHOW STATIONS":
                        self.output(self.REPLY_HELP,"MAC\tTX_RATE\tRX_RATE\tFER_AVG\tFER\tSIGNAL\tSIGNAL_AVG")
                        scan_result = self.factory.radio.get_stations()
                        if len(scan_result) > 0: 
                            for station in scan_result:
                                self.output(self.REPLY_COMMAND_OUTPUT, "%s\t%s\t%s\t%s\t%s\t%s\t%s" % 
                                        (station['addr'], station['tx_rate'], station['rx_rate'], 
                                            station['fer_avg'], station['fer'],
                                            station['signal'], station['signal_avg']))
                        self.sayReady()
                        return

                    if params == "SHOW FER":
                        self.output(self.REPLY_HELP,"MAC\tFER\tFER_AVG")
                        scan_result = self.factory.radio.get_fer()
                        for station in scan_result:
                            self.output(self.REPLY_COMMAND_OUTPUT, "%s\t%s\t%s" % 
                                    (station, scan_result[station]['current'], scan_result[station]['avg']))
                        self.sayReady()
                        return
                
                self.output(self.REPLY_INVALID_PARAMETER,"Invalid parameters. See HELP for options. ")
                self.sayReady()

                return

            if (command == "LIST"): 
                print "IPC: Client",self.transport.getPeer(),"requested LIST"

                if (params != None):
                    params = params.strip().upper()                    
                    if params == "CN":
                        self.output(self.REPLY_HELP,"ID\tAGE\tCR\tLAT\tLON\tP2P_IP\tRADAC_IP\t")
                        n = self.factory.p2pdprd.candidate_nodes.nodes if self.factory.p2pdprd.candidate_nodes != None else None
                        if (n != None):
                            for i in range(0, len(n)):
                                self.output(self.REPLY_COMMAND_OUTPUT,"%s\t%s\t%s\t%s\t%s\t%s:%s\t%s:%s" % (n[i].node_id, int(time.time() - n[i].timestamp), n[i].coord_range, n[i].position[0], n[i].position[1], 
                                    n[i].address[0], n[i].address[1],
                                    n[i].radac_address[0], n[i].radac_address[1]))
                        self.sayReady()
                        return


                    if params == "CONFIGS":
                        i = 0
                        self.output(self.REPLY_HELP,"ID\tAGE\tSRC_IP\tCONFIG")
                        for k,v in self.factory.server.configs.iteritems():
                            self.output(self.REPLY_COMMAND_OUTPUT,"%s\t%s\t%s:%s\t%s" % (k, int(time.time() - v['timestamp']), v['src'].host, v['src'].port, v['config']))

                        self.sayReady()
                        return


                    if params == "CONNECTIONS":
                        self.output(self.REPLY_HELP,"DIR\tPEER_ID\tPEER_IP")

                        for k in self.factory.server.clients:
                            self.output(self.REPLY_COMMAND_OUTPUT,"IN\t%s\t%s:%s" % (k.identifier, k.peer.host, k.peer.port))

                        for k in self.factory.client.candidateNodes:
                            self.output(self.REPLY_COMMAND_OUTPUT,"OUT\t%s\t%s:%s" % (k[0], k[1].host, k[1].port))

                        self.sayReady()
                        return
                
                self.output(self.REPLY_INVALID_PARAMETER,"Invalid parameters. See HELP for options. ")
                self.sayReady()

                return
        
            if (command == "CONFIG" and params != None):
                self.output(self.REPLY_COMMAND_OUTPUT,"Configuration received.")
                self.factory.config = params
                self.factory.client.pushConfig(self.factory.config)
                self.factory.server.config = self.factory.config
                self.sayReady()
                return

            # if we get here it is an error
            self.output(self.REPLY_INVALID_COMMAND,"Invalid command. See HELP for options. ")
            self.sayReady()

            return
