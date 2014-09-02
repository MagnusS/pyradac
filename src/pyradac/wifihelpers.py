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

class WifiHelpers(object):
    """ Static helper methods for calculating wifi-related values """

    @staticmethod
    def chan_to_freq(channel):
        """Convert a channel number (1->14) to WiFi channel in the 2.4 Ghz spectrum."""
        """Return type is an int given in Mhz (4 digits)."""
        freq_lookup = [0, 2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452, 2457, 2462, 2467, 2472, 2484]
        
        # Basic sanity checks
        assert isinstance(int, channel)
        assert channel in range(1,14)
        
        return freq_lookup[channel]

    @staticmethod
    def freq_to_chan(freq):
        """Convert a frequency value (4-digit integer [Mhz]) to wifi channel"""
        """Returns a channel number in the range from 1 to 14 (2.4 Ghz spectrum). None else."""
        freq_lookup = [0, 2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452, 2457, 2462, 2467, 2472, 2484]
        
        try:
            chan = freq_lookup.index(freq)
        except ValueError:
            chan = None
            
        return chan

    # Simple enum-like container
    @staticmethod
    def enum(**enums):
        return type('Enum', (), enums)

    @staticmethod
    def get_numbers_from_str(string):
        import re
        numbers = re.findall(r"[-+]?\d+", string)
        return numbers

