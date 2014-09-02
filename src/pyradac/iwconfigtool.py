'''
Copyright (c) 2014, Magnus Skjegstad (magnus@skjegstad.com) / FFI
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

class IWCONFIG(object):
    """ Wrapper class for calls to the "iw" command """

    def __init__(self, devicename, executor=None):
        """ Initialize the object with a device name (e.g. wlan0) and an executor. If no executor is specified, one is created for local executing local commands """
        self.executor = executor
        self.devicename = devicename
        if self.executor == None:
            self.executor = Executor()

    ''' Get current wifi channel '''
    def get_channel(host):
        from wifihelpers import WifiHelpers as wh
        freq = get_freq(host)
        if freq:
            return wh.freq_to_chan(get_freq(host))
        else:
            return 0

    ''' Get current wifi frequency '''
    def get_freq(host):
        import StringIO
        from contextlib import closing 

        with closing(StringIO.StringIO()) as result:
            if executor.execute_cmd(host, ["sudo",'iwconfig',self.devicename,'|','grep','Freq', out=result) == 0:
                return float(result.getvalue().split(':')[2].split(' ')[0].strip())
            else:
                return None

