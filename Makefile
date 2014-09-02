all: p2p-dprd

depends:
	./clone-p2pdprd.sh
	sudo apt-get install libconfig-dev python-paramiko python-twisted

p2p-dprd: 
	cd src/p2p-dprd/src && $(MAKE) && cp p2p-dprd ../../../bin/p2pdprd 

clean:
	rm -f bin/radac bin/radac_client radac.log bin/p2p-dprd
	rm -f src/pyradac/*.pyc
	cd src/p2p-dprd/src && make clean
