# Pyradac #
Pyradac is a framework for building resource/frequency allocators for [p2p-dprd](https://github.com/MagnusS/p2p-dprd)

## Overview ##

P2P-DPRD is an Internet-based peer-to-peer software to find other wireless devices in your area. Pyradac connects to the devices found by P2P-DPRD over the Internet and provides a platform for exchanging additional data, such as current radio configuration, measured interference etc. 

P2P-DPRD provides a unix socket interface that Pyradac connects to. Pyradac then provides a text-based configuration interface that can be accessed via telnet or python API.

P2P-DPRD and Pyradac are modules we have written to implement the architecture described in (this paper)[http://arxiv.org/pdf/1210.3552.pdf] (see Fig 1). P2P-DPRD is the discovery mechanism and Pyradac is the resource allocator framework. More specific resource/frequency allocation algorithms can be developed on top of Pyradac.

## Installation ##

To compile, run "make depends" to download dependencies and clone p2p-dprd, and then "make" to compile it (only tested in Ubuntu).

* src/p2p-dprd contains the cloned p2p-dprd source code after "make depends"
* bin/p2p-dprd contains the p2p-dprd binary after "make"
* [src/pyradac](src/pyradac) contains pyradac
* [tools/cfggen](tools/cfggen) contains a configuration file generator that can be used to generate matching configurations for p2p-dprd and pyradac
* [tools/testrun](tools/testrun) contains scripts for generating configuration files for a local test environment

## Test environment ##

The testrun-utility located in [tools/testrun](tools/testrun) can be used to generate a set of configuration files and startup scripts for p2pdprd and pyradac. 

The command
```
./create_configs.sh
```

creates 10 startup scripts called start-client-x.sh, where x is the client number from 1 to 10. To start the clients, execute each of these scripts in a separate terminal window. All clients are configured to connect to node 1. If you want to start fewer than 10 nodes, always start node 1 first if you want an unpartitioned network.

Each node opens up a port for monitoring and configuring pyradac. This port is 400x, where x is the client number. Pyradac can be configured with telnet:

```
$ telnet localhost 4001
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
211 RADAC IPC server
200 Ready.
help
214 Available commands:
214 --------------------------
214 STATUS                              Show pyradac status
214 LOC [lat] [lon]                     Set location (float)
214 CR [coordination range]             Set coordination range (unsigned int)
214 CONFIG [config]                     Set current configuration (string, use base64 for binary)
214 LIST [cn|connections|configs]       List known candidate nodes (cn), connections or configs
214 .                                   Repeat last command.
214 HELP                                This text
214 QUIT                                Disconnect
200 Ready.
```

The testrun-utility uses cfggen.py to create the startup files. Cfggen is further explained in the next section.

### cfggen ###
The current version of p2pdprd requires a configuration file to start. Pyradac must be started with many of the same parameters and it is important that these parameters match the values set for p2pdprd. To make it easier to create configuration files and startup scripts for multiple nodes, we have written a simple template system.

The configuration generator is located in [tools/cfggen](tools/cfggen) and is called [cfggen.py](tools/cfggen/cfggen.py). This utility creates a set of configurations and startup scripts for a given number of nodes and outputs the result as uncompressed tar to standard output.

For example, the following command would generate the necessary files to start two nodes:

```
$ ./cfggen.py --clients=2
```

Note however, that the output is in tar format. To list the output files, use 

```
./cfggen.py --clients=2 | tar -t
p2pdprd-client1.cfg
start-client-1.sh
p2pdprd-client2.cfg
start-client-2.sh
```

The files can also be extracted by replacing "tar -t" with "tar -xv".

To start the two clients, use start-client-1.sh for client 1 and start-client-2.sh to start client 2. The script will make sure that both p2pdprd and pyradac are started with the correct parameters. The following ports are assigned to the different services by default (where x is the node id, counting from 1):

```
200x p2pdprd to p2pdprd listen port
300x pyradac to pyradac listen port
400x pyradac api/ipc port
```

To configure or monitor the current status of pyradac, use telnet to connect to port 400x on localhost.

The cfggen.py-utility supports various parameters to modify the behavior of the clients. These parameters modifies the variables that are replaced in the templates that are located in the same folder as cfggen.py. The template files are called "p2p-dprd-cfg.template" and "start-client-sh.template". 

Here is the full output from cfggen.py when it is executed without parameters:

```
$ ./cfggen.py 
Usage: cfggen.py [options]
Options:
      --clients=             Number of clients to generate configs for
      --p2p_ip=              p2pdprd listen ip [default: 127.0.0.1]
      --p2p_port=            p2pdprd first listen port [default: 2001]
      --p2p_sock=            p2pdprd socket file. Client ID is appended.
                             [default: /tmp/p2p-sock]
      --p2p_bin=             p2pdprd binary [default: p2p-dprd]
      --radac_ip=            radac listen ip [default: 127.0.0.1]
      --radac_listen_port=   radac first listen port [default: 3001]
      --radac_control_port=  radac first control port [default: 4001]
      --radac_sock=          radac socket file. Client ID is appended. [default:
                             /tmp/radac-sock]
      --radac_bin=           radac binary [default: raproto.py]
      --log_file=            log file. Client ID is appended. [default:
                             p2pdprd-log]
      --p2p_template=        template used to generate p2pdprd config [default:
                             p2p-dprd-cfg.template]
      --sh_template=         template used to generate launch scripts [default:
                             start-client-sh.template]
      --lat_max=             Maximum latitude (latitude is randomly generated)
                             [default: 58.01]
      --lat_min=             Minimum latitude (latitude is randomly generated)
                             [default: 58.0]
      --lon_max=             Maximum longitude (longitude is randomly generated)
                             [default: 10.01]
      --lon_min=             Minimum longitude (longitude is randomly generated)
                             [default: 10.0]
      --cr_max=              Maximum coordination range (cr is randomly
                             generated) [default: 50]
      --cr_min=              Minimum coordination range (cr is randomly
                             generated) [default: 25]
      --first_id=            First identifier. Increased by 1 for each client.
                             Note that 0 is not a valid ID. [default: 1]
      --version              Display Twisted version and exit.
      --help                 Display this help and exit.

This script generates configurations files for p2pdprd based on a template.

The configuration files are generated as a tar file that is output to stdout.

To extract the configuration files, pipe the output to tar. E.g:

./cfggen --clients 10 | tar -xv

Or alternatively ./cfggen --clients 10 > myconfigs.tar

... and open myconfigs.tar in your favourite archive manager.

(c) Magnus Skjegstad <magnus@skjegstad.com> / FFI, 2013
```

## Pyradac API #

Pyradac API example:

```python
import sys
sys.path.append("../pyradac") # point this to the pyradac folder that contains ipcclient.py

import ipcclient as pyradac # import pyradac ipc client

client = pyradac.IPCClient("localhost",4001) # connect to local pyradac ipc port

print "My identifier is",client.getIdentifier()

client.setLocation(99,99) # set geographical location
client.setCoordinationRange(50) # set coordination range 

client.setConfig("TESTCONFIG") # set our own config, which is pushed to all candidate nodes

print client.getConfigs() # print all known configurations
print client.getCandidateNodes() # print all known candidatenodes with locations

client.disconnect() # disconnect
```

More examples are provided in [ipcclient.py](src/pyradac/ipcclient.py).

## Contributors ##

* Magnus Skjegstad - Protocol and system design, pyradac, p2pdprd, various
* Halvdan Hoem Grelland - P2P-DPRD, Pyradac, OpenWRT hacks
* Jostein Aardal - P2P-DPRD, original radac (now replaced by pyradac) 
* Tore Ulversoy - Resource allocation
* Terje Mikal Mjelde - Aggie

