#!/usr/bin/env python

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

import telnetlib
import socket
import base64
from ipcserver import IPCServerProtocol as isp

class IPCClient(object):
host = str()
port = int()
tn = None

def __init__(self, host, port):
""" Connect to pyradac configuration port at given host """
self.host = host
self.port = port
self.connect()

    def connect(self):
        """ Force connect/reconnect """
        self.disconnect()
        self.tn = telnetlib.Telnet(self.host, self.port)
        self.tn.read_until(str(isp.REPLY_READY), 5) # wait 5 seconds for a 200 ready to appear

    def disconnect(self):
        """ Disconnect from server """
        if (self.tn != None):
            try:
                self.tn.close()
            except:
                pass
        self.tn = None

    def getConnections(self):
        """ Get incoming and outgoing pyradac connections as array of dict """
        return self.getCommandOutputAsRows("LIST CONNECTIONS\r\n")

    def isconnected(self):
        """ Check connection status """
        return self.tn != None

    def setLocation(self, lat, lon):
        """ Set current location """
        (msg, res) = self.sendCommand("LOC " + str(float(lat)) + " " + str(float(lon)) + "\r\n")
        return res

    def setCoordinationRadius(self, cr):
        """ Set current coordination radius """
        (msg, res) = self.sendCommand("CR " + str(long(cr)) + "\r\n")
        return res

    def setConfig(self, config):
        """ Set and distribute new configuration parameters. The configuration is automatically base64-encoded before it is transmitted. """
        (msg, res) = self.sendCommand("CONFIG " + base64.b64encode(config) + "\r\n")
        return res

    def getStatus(self):
        """ Get current status from pyradac """
        return self.getCommandOutputAsCols("STATUS\r\n")

    def getCoordinationRange(self):
        """ Get current coordination range """
        status = self.getStatus()
        if status != None:
            return int(status['Current coordination range'])
        return None

    def getLocation(self):
        """ Get current location """
        status = self.getStatus()
        if status != None:
            loc = status['Current location'].split(' ')
            return (float(loc[0]), float(loc[1]))
        return None

    def getIdentifier(self):
        """ Get pyradac/p2pdprd node identifier """
        status = self.getStatus()
        if status != None:
            return int(status['Node identifier'])
        return None

    def getCandidateNodes(self):
        """ Get known candidate nodes as array of dict """
        return self.getCommandOutputAsRows("LIST CN\r\n")

    def getRadioStations(self):
        """ Get list of stations connected to the access point, with current and average frame error rates. Note that FER=1.0 in practice means that there is no traffic from the station. """
        return self.getCommandOutputAsRows("RADIO SHOW STATIONS\r\n")

    def getRadioFER(self):
        """ Return a list of MAC addrsses connected to the access point with frame error rates. This command is faster than getRadioStations(), but returns less information """
        return self.getCommandOutputAsRows("RADIO SHOW FER\r\n")

    def getRadioSummary(self):
        """ Return a summary of the current configuration """
        return self.getCommandOutputAsCols("RADIO SHOW\r\n")

    def getRadioScan(self):
        """ Scan for SSIDs and return result. WARNING: Takes the AP down for the duration of the scan (200ms?) """
        return self.getCommandOutputAsRows("RADIO SCAN\r\n")

    def setRadioChannelAndTx(self, channel, tx_power):
        """ Set channel and tx power of radio. Use -1 or None for no change. Verify new configuration with getRadioSummary()  """
        if channel == None:
            channel = -1
        if tx_power == None:
            tx_power = -1

        return self.sendCommand("RADIO SET %s %s\r\n" % (channel, tx_power))

    def isRadioEnabled(self):
        return self.getRadioSummary() != {}

    def getConfigs(self):
        """ Get all known configurations """
        result = self.getCommandOutputAsRows("LIST CONFIGS\r\n")
        if result == None:
            return None

        # base64 decode all configurations
        for row in result:
            row['config'] = base64.b64decode(row['config'])

        return result

    def reuse_or_reconnect(self):
        """ Check for existing connection and reconnect if necessary """
        if not self.isconnected():
            self.connect()

    def sendCommand(self, cmd):
        """ Send command to server. Line feeds are not automatically added. """
        self.reuse_or_reconnect()        
        try:
            self.tn.read_very_lazy()
            self.tn.write(cmd) # attempt to write
        except: # disconnect on errors and raise exception
            self.disconnect()
            raise
        #return self.tn.read_very_lazy()
        result = self.tn.read_until(str(isp.REPLY_READY) + " ", 5) # wait for data until server is ready
        self.tn.read_until("\r\n", 5) # Make sure that we get final new line after the REPLY_READY line

        # return tuple (success, message)
        if (str(isp.REPLY_READY) in result):
            return (result, True)
        else:
            return (result, False) 

    def getCommandOutputAsCols(self, command):
        (result, ok) = self.sendCommand(command)
        if ok:
            fields = {}
            # return array of dict where keys are taken from the first row. 
            for line in result.split("\r\n"):
                code = line.split(' ')[0]
                row = (line[3:]).split(":")
                
                if (int(code) == isp.REPLY_COMMAND_OUTPUT):
                    fields[row[0].strip()] = row[1].strip()

            return fields
        else:
            return None

    def getCommandOutputAsRows(self, command):
        """ Generic method for executing commands in pyradac that return multiple rows of named columns. Returns a list of dictionaries, where each dictionary has column names as keys """
        (result, ok) = self.sendCommand(command)
        if ok:
            columnnames = None
            rows = []

            # return array of dict where keys are taken from the first row. 
            for line in result.split("\r\n"):
                code = line.split(' ')[0]
                cols = (line[3:]).split("\t")
                
                if (int(code) == isp.REPLY_HELP):
                    columnnames = cols

                if (int(code) == isp.REPLY_COMMAND_OUTPUT):
                    if (columnnames == None):
                        raise Exception('No column names')
                    if (len(columnnames) < len(cols)):
                        raise Exception('Column name count lower than actual columns')

                    row = {}
                    for n in range(0,len(cols)):
                        row[columnnames[n].lower()] = cols[n].strip()
                    rows.append(row)

            return rows
        else:
            return None


def test():
    #client.tn.set_debuglevel(255)
    config = "test configuration"
    print "Connecting..."
    client = IPCClient("127.0.0.1", 4001)

    print "My id:",client.getIdentifier()
    print "Current location:", client.getLocation()
    print "Current coordination range:", client.getCoordinationRange()

    print "Setting location to 99, 99"
    client.setLocation(99, 99)
    
    print "Setting coordination radius to 100"
    client.setCoordinationRadius(100)

    print "Known configs:"
    print client.getConfigs()

    print "Setting own config to " + config
    client.setConfig(config)

    print "Updated configs:"
    print client.getConfigs()

    print "Known candidate nodes"
    print client.getCandidateNodes()

    if client.isRadioEnabled():
        print "Radio: Enabled"
        print "Radio summary:"
        print client.getRadioSummary()

        print "Radio scan:"
        print client.getRadioScan()

        print "Radio stations:"
        print client.getRadioStations()

        print "Radio FER per station:"
        print client.getRadioFER()
    
        print "Changing channel to channel 3 and tx power 1:"
        print client.setRadioChannelAndTx(3, 1)

        print "Result summary:"
        print client.getRadioSummary()

    else:
        print "Radio: Disabled"

    client.disconnect()
    

if __name__ == "__main__":
        test()
