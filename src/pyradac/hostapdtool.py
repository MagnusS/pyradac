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

from executor import Executor

class Hostapd(object):
    """ Wrapper class for UCI (OpenWRT) commands """
    executor = None
    devicename = None

    def __init__(self, config = "/etc/hostapd/hostapd.conf", wifi_restart_command, executor=None):
        if executor == None:
            self.executor = Executor()
        else:
            self.executor = executor

        self.config = config
        self.restart_command = wifi_restart_command

    def get_wifi_interface(self):
        "Return the wifi interface name (e.g. 'wlan0')"
        ret = self.executor.execute_cmd(['grep', '^interface', self.config, '|', 'cut','-f2','-d"="'])
        
        if ret is None:
            print 'No WiFi device name found.'

        return ret

    def get_bridge_interface(self):
        "Return the bridge interface name (e.g. 'br0')"
        ret = self.executor.execute_cmd(['grep', '^bridge', self.config, '|', 'cut','-f2','-d"="'])
        
        if ret is None:
            print 'No bridge device name found.'

        return ret

    def get_wifi_mode(self):
        "Get operation mode (e.g. n)"
        ret = self.executor.execute_cmd(['grep', '^hw_mode', self.config, '|', 'cut','-f2','-d"="'])
        
        if ret is None:
            print 'No mode found in config.'
        
        return ret

    def set_channel(self, channel):
        "Sets the wifi channel. Requires commit and restart of WiFi for changes to take effect"
        self.executor.execute_cmd(['sudo','cat',self.config,'|','sed','-e',"s/channel=[0-9][0-9]*/channel=%d/g" % channel, '>', '/tmp/tmp_hostapd.conf'])
        self.executor.execute_cmd(['sudo','mv','/tmp/tmp_hostapd.conf',self.config])

    def restart():
        "Restart hostapd"
        self.executor.execute_cmd(wifi_restart_command)

    def get_wifi_ssid(self):
        "Return the wifi ssid (e.g. for 'node1-wifi')"
        ret = self.executor.execute_cmd(['grep', '^ssid', self.config, '|', 'cut','-f2','-d"="'])
        
        if ret is None:
            print 'No SSID found in config.'
        
        return ret

