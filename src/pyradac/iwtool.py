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

class IW(object):
    """ Wrapper class for calls to the "iw" command """

    def __init__(self, devicename, executor=None):
        """ Initialize the object with a device name (e.g. wlan0) and an executor. If no executor is specified, one is created for local executing local commands """
        self.executor = executor
        self.devicename = devicename
        if self.executor == None:
            self.executor = Executor()

    def get_info(self):
        """ Calls iw info """
        info = {}
        res = self.executor.execute_cmd(['iw',self.devicename,'info'])
        for f in res.split("\n"):
            vals = f.strip().split(" ")
            if vals[0].lower() == "channel":
                info['info'] = f.strip()
            else:
                info[vals[0].lower()] = " ".join(vals[1:])
        return info

    def scan(self):
        """ Scans for other access points. The AP stops responding for about 200 ms """
        return self.executor.execute_cmd(["iw",self.devicename,"scan"])

    def get_stations(self):
        """ Get list of stations connected to the AP """
        res = self.executor.execute_cmd(['iw', self.devicename, 'station', 'dump'])
        stations = []
        curstation = None
        for f in res.split("\n"):
            vals=f.strip().split(" ")
            print vals
            if vals[0].strip().lower() == "station": # new station
                if curstation != None:
                    stations.append(curstation)
                curstation = {}
                curstation['addr'] = vals[1].strip()
            else: # info for this station, split by : instead
                vals = f.strip().split(":")
                if vals != None and curstation != None:
                    curstation[vals[0].strip().lower()] = (" ".join(vals[1:])).strip()
        if curstation != None:
            stations.append(curstation)

        return stations

