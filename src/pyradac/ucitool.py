#!/usr/bin/env python 

'''
Copyright (c) 2013-2014, Magnus Skjegstad (magnus@skjegstad.com) / FFI
Copyright (c) 2013-2014, Halvdan Hoem Grelland (halvdanhg@gmail.com) / FFI
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

class UCI(object):
    """ Wrapper class for UCI (OpenWRT) commands """
    executor = None
    devicename = None

    def __init__(self, devicename, executor=None):
        if executor == None:
            self.executor = Executor()
        else:
            self.executor = executor
        self.devicename = devicename

    def commit_config(self):
        """Commit uci changes"""
        self.executor.execute_cmd(['uci','commit'])

    def reload_wifi_config(self):
        """Reloads the WiFi config (applying changes) and restarts the wifi subsystem"""
        return self.executor.execute_cmd(['wifi'])

    def get_wifi_interface(self):
        "Return the wifi interface name (e.g. 'radio0')"
        ret = self.executor.execute_cmd(['uci', 'get', 'wireless.@wifi-iface[0].device'])
        
        if ret is None:
            print 'No WiFi device name found.'

        return ret

    def get_tx_power(self):
        "Get the currently set TX-power."
        ret = self.executor.execute_cmd(['uci', 'get', 'wireless.' + self.devicename + '.txpower'])
        
        if ret.isdigit():
            return int(ret)
        else:
            print 'Failed to get TX-power for interface '+self.devicename+ '.'
            return None

    def get_channel(self):
        "Get the currently set WiFi-channel (as channel number)."
        
        ret = self.executor.execute_cmd(['uci', 'get', 'wireless.' + self.devicename + '.channel'])

        # Check if digit and within range
        if ret.isdigit() and int(ret) in range(1,14):
            return int(ret)
        else:
            print 'Failed to get channel'
            return None
            
    def get_operation_mode(self):
        ret = self.executor.execute_cmd(['uci', 'get', 'wireless.@wifi-iface[0].mode'])
        
        if ret is None:
            print 'Failed to get operational mode of the wireless interface.'
        
        return ret

    def get_wifi_mode(self):
        ret = self.executor.execute_cmd(['uci', 'get', 'wireless.' + self.devicename + '.hwmode'])
        
        if ret is None:
            print 'Failed to get HW-mode of interface '+self.devicename+' .'
        
        return ret

    def set_tx_power(self, power):
        "Sets the tx power in dBm. Requires commit and restart for changes to take effect"
        self.executor.execute_cmd(['uci', 'set', 'wireless.' + self.devicename + '.txpower' + '=' + str(power)])
        
    def set_channel(self, channel):
        "Sets the wifi channel. Requires commit and restart of WiFi for changes to take effect"
        self.executor.execute_cmd(['uci', 'set', 'wireless.' + self.devicename + '.channel' + '=' + str(channel)])

    def set_wifi_mode(self, hwmode):
        "Sets the wifi HW-mode. E.g. 11g, 11n, 11b."
        self.executor.execute_cmd(['uci', 'set', 'wireless.' + self.devicename + '=' + hwmode])

    def get_wifi_ssid(self):
        "Return the wifi ssid (e.g. for 'radio0')"
        ret = self.executor.execute_cmd(['uci', 'get', 'wireless.@wifi-iface[0].ssid'])
        
        if ret is None:
            print 'No WiFi device name found.'

        return ret

