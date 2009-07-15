all:
	cd doc; $(MAKE)

clean:
	rm pyzui/*.pyc
	cd doc; $(MAKE) clean
