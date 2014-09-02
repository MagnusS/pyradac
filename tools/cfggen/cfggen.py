#!/usr/bin/env python

"""
This script generates configurations files for p2pdprd based on a template.

The configuration files are generated as a tar file that is output to stdout. 

To extract the configuration files, pipe the output to tar. E.g:

    ./cfggen --clients 10 | tar -xv

Or alternatively
    
    ./cfggen --clients 10 > myconfigs.tar

... and open myconfigs.tar in your favourite archive manager.


(c) Magnus Skjegstad <magnus@skjegstad.com> / FFI, 2013
"""

from twisted.python import usage
from string import Template
import random
import sys
import math

# Parameters
class CfgOptions(usage.Options):
    optParameters = [
            ['clients',None,None,'Number of clients to generate configs for',int],
            ['p2p_ip',None,'127.0.0.1','p2pdprd listen ip',int],
            ['p2p_port',None,2001,'p2pdprd first listen port',int],
            ['p2p_sock',None,'/tmp/p2p-sock','p2pdprd socket file. Client ID is appended.',str],
            ['p2p_bin',None,'p2p-dprd','p2pdprd binary',str],
            ['radac_ip',None,'127.0.0.1','radac listen ip',int],
            ['radac_listen_port',None,3001,'radac first listen port',int],
            ['radac_control_port',None,4001,'radac first control port', int],
            ['radac_sock',None,'/tmp/radac-sock','radac socket file. Client ID is appended.',str],
            ['radac_bin',None,'raproto.py','radac binary',str],
            ['log_file',None,'p2pdprd-log','log file. Client ID is appended.',str],
            ['p2p_template',None,'p2p-dprd-cfg.template','template used to generate p2pdprd config',str],
            ['sh_template',None,'start-client-sh.template','template used to generate launch scripts',str],
            ['lat_max',None,58.01,'Maximum latitude (latitude is randomly generated)', float],
            ['lat_min',None,58.00,'Minimum latitude (latitude is randomly generated)', float],
            ['lon_max',None,10.01,'Maximum longitude (longitude is randomly generated)', float],
            ['lon_min',None,10.00,'Minimum longitude (longitude is randomly generated)', float],
            ['cr_max',None,50,'Maximum coordination range (cr is randomly generated)',int],
            ['cr_min',None,25,'Minimum coordination range (cr is randomly generated)',int],
            ['first_id',None,1,'First identifier. Increased by 1 for each client. Note that 0 is not a valid ID.', int],
            ['has_radio',None,0,'Set to 1 to enable radio.',int],
        ]


options = CfgOptions()
options.parseOptions(sys.argv[1:])

if options['clients'] == None:
    print options
    sys.exit(-1)

# Read p2pdprd config template file as string
with open(options['p2p_template'], 'r') as template_file:
    templatestr = template_file.read()
cfg = Template(templatestr)

# Read shell script template file as string
with open(options['sh_template'], 'r') as template_file:
    templatestr = template_file.read()
shellscript = Template(templatestr)

origip = options['p2p_ip']
origport = options['p2p_port']

# Open tar file
import tarfile, datetime
from cStringIO import StringIO
tar = tarfile.open(fileobj=sys.stdout, mode="w|")

# Create parameter sets
for i in range(0, options['clients']):
    clientid = options['first_id'] + i
    # Create dict with standard substitutions
    substitutions = dict(
        origin_ip = origip,
        origin_port = origport,
        identifier = clientid,
        lat = random.uniform(options['lat_min'], options['lat_max']),
        lon = random.uniform(options['lon_min'], options['lon_max']),
        cr = int(math.ceil(random.uniform(options['cr_min'], options['cr_max']))),
        p2p_ip = options['p2p_ip'],
        p2p_port = options['p2p_port'] + i,
        p2p_sock = options['p2p_sock'] + str(i),
        p2p_bin = options['p2p_bin'], 
        radac_ip = options['radac_ip'],
        radac_listen_port = options['radac_listen_port'] + i,
        radac_control_port = options['radac_control_port'] + i,
        radac_sock = options['radac_sock'] + str(i),
        radac_bin = options['radac_bin'], 
        log_file = options['log_file'] + str(i),
        has_radio = options['has_radio'])

    # Create P2PDPRD configuration file
    cfgstr = cfg.safe_substitute(substitutions)
    tarinfo = tarfile.TarInfo("p2pdprd-client" + str(clientid) + ".cfg")
    tarinfo.size = len(cfgstr)
    tarinfo.mode = 0644
    tarinfo.mtime = int(datetime.datetime.now().strftime("%s"))
    tar.addfile(tarinfo, StringIO(cfgstr))

    # Create bash startup script
    shellstr = shellscript.safe_substitute(substitutions)
    tarinfo = tarfile.TarInfo("start-client-" + str(clientid) + ".sh")
    tarinfo.size = len(shellstr)
    tarinfo.mode = 0775 # executable
    tarinfo.mtime = int(datetime.datetime.now().strftime("%s"))
    tar.addfile(tarinfo, StringIO(shellstr))
    
# close tar
tar.close()
