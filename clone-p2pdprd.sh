#!/bin/sh

REPO=https://github.com/MagnusS/p2p-dprd.git
TARGET=src/p2p-dprd

if [ -e "$TARGET" ]; then
    cd $TARGET && \
    git pull || \
    echo "Failed to update p2p-dprd"
else
    git clone $REPO $TARGET || \
    echo "Failed to download p2p-dprd"
fi
