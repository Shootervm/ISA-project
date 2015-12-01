all:
	@echo "Please run ./antipirat script"

run:
	./antipirat.py --help

.PHONY: clean pack

clean:
	@rm -rf *.xml *.torrent *.txt *.peerlist 2>/dev/null
	@rm -rf xmasek15.tar 2>/dev/null

pack:
	tar cf xmasek15.tar *