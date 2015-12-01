all:
	@chmod +x ./antipirat
	@echo "Please run ./antipirat python3 script"

run:
	./antipirat --help

.PHONY: clean pack

clean:
	@rm -rf __pycache__ *.xml *.torrent *.txt *.peerlist 2>/dev/null
	@rm -rf xmasek15.tar 2>/dev/null

pack: clean
	@tar cf xmasek15.tar *.py antipirat Makefile README* manual.pdf bencodepyFolder