#!/bin/sh

../cfggen/cfggen.py --clients=10 \
    --p2p_bin=../../bin/p2pdprd \
    --p2p_template=../cfggen/p2p-dprd-cfg.template \
    --radac_bin=../../src/pyradac/raproto.py \
    --sh_template=../cfggen/start-client-sh.template \
    --lat_min=100 --lat_max=100 \
    --lon_min=100 --lon_max=100 \
    --cr_min=25 --cr_max=50 \
    | tar -xv

