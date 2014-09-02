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

from subprocess import Popen, PIPE
from iwtool import IW
from ucitool import UCI
from wifihelpers import WifiHelpers
from minstrel import Minstrel
from executor import Executor

class Radio(object):
    """ Wrapper class for all radio object. Contains UCI and IW helper objects. """ 

    def __init__(self, devid=0, sshclient=None):
        """ Initiate class and sub-classes. Dev id is the device id counting from zero, e.g. wlan0 becomes 0. Sshclient is an optional paramiko.SSHClient() object used to execute commands. If sshclient==None, commands are execute """
        self.executor = Executor(sshclient)

        phy_dev = "radio" + str(devid)
        wlan_dev = "wlan" + str(devid)

        self.uci = UCI(devicename=phy_dev, executor=self.executor)
        self.minstrel_path= "/sys/kernel/debug/ieee80211/phy%s/netdev:wlan%s/stations/" % (devid, devid)
        self.deviceid = int(devid)
        self.iw = IW(devicename=wlan_dev, executor=self.executor)
        self.minstrel = Minstrel(minstrel_path=self.minstrel_path, executor=self.executor)

    def reconfigure(self, new_channel=None, new_tx_power=None):
        """ Reconfigure the radio (channel, tx power) and restart the wifi driver. This takes the AP down for a few seconds. Parameters set to None are left unchanged. """
        if new_tx_power != None:
            self.uci.set_tx_power(new_tx_power)
        if new_channel != None:
            self.uci.set_channel(new_channel)
        self.uci.commit_config()
        self.uci.reload_wifi_config()
        
    def get_summary(self):
        """ Summarize radio settings (channel, tx_power, ssid etc) """
        res = {}

        res['channel'] = self.uci.get_channel() # channel
        res['tx_power'] = self.minstrel.get_tx_power() # transmission power
        res['type'] = self.uci.get_operation_mode() # operation mode, e.g.
        res['mode'] = self.uci.get_wifi_mode() # wifi mode, e.g. 11ag

        info = self.iw.get_info()

        res['addr'] = info['addr'] # mac addr
        res['info'] = info['info'] # information string
        res['interface'] = info['interface'] # wifi interface, e.g. wlan0
        res['phy'] = info['wiphy'] 
        res['ssid'] = self.uci.get_wifi_ssid()

        return res

    def get_stations(self):
        """ Get info about users (stations) connected to the AP """
        stations = self.iw.get_stations()
        result = []
        minstrel = self.minstrel.get_frame_error_rates()
        for station in stations:
            result.append({
                'addr': station['addr'], 
                'tx_rate': WifiHelpers.get_numbers_from_str(station['tx bitrate'])[0],
                'rx_rate': WifiHelpers.get_numbers_from_str(station['rx bitrate'])[0],
                'signal': WifiHelpers.get_numbers_from_str(station['signal'])[0],
                'signal_avg': WifiHelpers.get_numbers_from_str(station['signal avg'])[0],
                'fer': minstrel[station['addr']]['current'],
                'fer_avg' : minstrel[station['addr']]['avg']})
        return result

    def get_fer(self):
        """ Get frame error rate for all stations """
        return self.minstrel.get_frame_error_rates()

